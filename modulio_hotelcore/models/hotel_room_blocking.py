# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime
import logging

_logger = logging.getLogger(__name__)


class HotelRoomBlocking(models.Model):
    _name = 'hotel.room.blocking'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Hotel Room Blocking'
    _order = 'start_date, end_date'

    name = fields.Char(
        string='Blocking Name',
        required=True,
        tracking=True,
        help='Name or reason for blocking the room'
    )
    room_id = fields.Many2one(
        'hotel.room',
        string='Room',
        required=True,
        index=True,
        ondelete='cascade',
        tracking=True,
        help='Room to be blocked'
    )
    room_number = fields.Char(
        related='room_id.room_number',
        string='Room Number',
        store=True,
        help='Room number for easy reference'
    )
    room_type_id = fields.Many2one(
        related='room_id.room_type_id',
        string='Room Type',
        store=True,
        help='Type of the blocked room'
    )
    start_date = fields.Date(
        string='Start Date',
        required=True,
        tracking=True,
        help='Date when blocking starts'
    )
    end_date = fields.Date(
        string='End Date',
        required=True,
        tracking=True,
        help='Date when blocking ends'
    )
    start_datetime = fields.Datetime(
        string='Start DateTime',
        compute='_compute_datetime_fields',
        store=True,
        help='Start date and time for calendar display'
    )
    end_datetime = fields.Datetime(
        string='End DateTime',
        compute='_compute_datetime_fields',
        store=True,
        help='End date and time for calendar display'
    )
    blocking_type = fields.Selection([
        ('maintenance', 'Maintenance'),
        ('event', 'Event'),
        ('out_of_order', 'Out of Order'),
        ('renovation', 'Renovation'),
        ('other', 'Other'),
    ], string='Blocking Type', default=False, required=True,
       tracking=True, help='Type of room blocking')
    
    reason = fields.Text(
        string='Reason',
        help='Detailed reason for blocking the room'
    )
    responsible_user_id = fields.Many2one(
        'res.users',
        string='Blocking Responsible',
        default=lambda self: self.env.user,
        tracking=True,
        help='User responsible for this blocking'
    )
    status = fields.Selection([
        ('planned', 'Planned'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='planned', required=True,
       tracking=True, help='Current status of the blocking')
    
    duration_days = fields.Integer(
        string='Duration (Days)',
        compute='_compute_duration',
        store=True,
        help='Duration of blocking in days'
    )
    
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True,
        index=True,
        ondelete='restrict'
    )

    @api.depends('start_date', 'end_date')
    def _compute_datetime_fields(self):
        """Convert date fields to datetime for calendar display"""
        for record in self:
            if record.start_date:
                record.start_datetime = datetime.combine(record.start_date, datetime.min.time())
            else:
                record.start_datetime = False
            
            if record.end_date:
                # End datetime should be end of day
                record.end_datetime = datetime.combine(record.end_date, datetime.max.time())
            else:
                record.end_datetime = False

    @api.depends('start_date', 'end_date')
    def _compute_duration(self):
        """Calculate duration in days"""
        for record in self:
            if record.start_date and record.end_date:
                delta = record.end_date - record.start_date
                record.duration_days = delta.days + 1  # Include both start and end days
            else:
                record.duration_days = 0

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to validate dates and check conflicts"""
        for vals in vals_list:
            if 'start_date' in vals and 'end_date' in vals:
                self._validate_dates(vals['start_date'], vals['end_date'])
                self._check_room_availability(vals.get('room_id'), vals['start_date'], vals['end_date'])
        return super().create(vals_list)

    def write(self, vals):
        """Override write to validate dates and check conflicts"""
        status_before_map = {rec.id: rec.status for rec in self}
        blocking_type_before_map = {rec.id: rec.blocking_type for rec in self}
        
        if 'start_date' in vals or 'end_date' in vals or 'room_id' in vals:
            for record in self:
                start_date = vals.get('start_date', record.start_date)
                end_date = vals.get('end_date', record.end_date)
                room_id = vals.get('room_id', record.room_id.id)
                
                if start_date and end_date:
                    self._validate_dates(start_date, end_date)
                    self._check_room_availability(room_id, start_date, end_date, exclude_id=record.id)
        res = super().write(vals)

        # Only affect room occupancy when status becomes active or leaves active
        if 'status' in vals or 'blocking_type' in vals:
            event_closes_inventory = self._event_closes_inventory()
            for record in self:
                prev_status = status_before_map.get(record.id)
                new_status = record.status
                prev_type = blocking_type_before_map.get(record.id)
                new_type = record.blocking_type

                # Transition into active → apply impact
                if prev_status != 'active' and new_status == 'active':
                    if record.room_id:
                        room_vals = {
                            'blocking_type': new_type,
                            'blocking_reason': record.reason or record.name,
                        }
                        if new_type == 'event':
                            if event_closes_inventory:
                                room_vals['housekeeping_state'] = 'out_of_service'
                        else:
                            room_vals['housekeeping_state'] = 'out_of_service'
                        record.room_id.write(room_vals)

                # Transition out of active (to planned/completed/cancelled) → reset housekeeping
                if prev_status == 'active' and new_status != 'active':
                    if record.room_id:
                        record.room_id.write({
                            'housekeeping_state': 'inspected',
                            'blocking_type': False,
                            'blocking_reason': False,
                        })

                # Change type while active → re-apply impact based on new type
                if new_status == 'active' and prev_status == 'active' and prev_type != new_type:
                    if record.room_id:
                        room_vals = {
                            'blocking_type': new_type,
                            'blocking_reason': record.reason or record.name,
                        }
                        if new_type == 'event':
                            # If moving to event and config does not close inventory, clear housekeeping_state only if previously set by non-event
                            if event_closes_inventory:
                                room_vals['housekeeping_state'] = 'out_of_service'
                            else:
                                # do not change housekeeping_state
                                pass
                        else:
                            room_vals['housekeeping_state'] = 'out_of_service'
                        record.room_id.write(room_vals)

        return res

    def _validate_dates(self, start_date, end_date):
        """Validate that start_date is before end_date"""
        if start_date and end_date:
            # Convert string dates to date objects for comparison
            if isinstance(start_date, str):
                start_date = fields.Date.from_string(start_date)
            if isinstance(end_date, str):
                end_date = fields.Date.from_string(end_date)
            
            if start_date > end_date:
                raise ValidationError(_("Start date must be before or equal to end date."))

    def _check_room_availability(self, room_id, start_date, end_date, exclude_id=None):
        """Check if room is available for the given date range"""
        if not room_id or not start_date or not end_date:
            return
        
        domain = [
            ('room_id', '=', room_id),
            ('status', 'in', ['planned', 'active']),
            ('start_date', '<=', end_date),
            ('end_date', '>=', start_date),
        ]
        
        if exclude_id:
            domain.append(('id', '!=', exclude_id))
        
        conflicting_blockings = self.search(domain)
        if conflicting_blockings:
            room = self.env['hotel.room'].browse(room_id)
            raise ValidationError(_(
                "Room %s is already blocked during this period.\n"
                "Conflicting blockings:\n%s"
            ) % (
                room.room_number,
                '\n'.join([f"- {b.name} ({b.start_date} to {b.end_date})" for b in conflicting_blockings])
            ))

    def action_activate(self):
        """Activate the blocking"""
        self.write({'status': 'active'})
        # Set room status based on blocking type
        if self.room_id:
            # Debug logging
            _logger.info(f"DEBUG: Blocking {self.name} - blocking_type: '{self.blocking_type}' (type: {type(self.blocking_type)})")
            
            # Update room status and blocking info
            room_vals = {
                'blocking_type': self.blocking_type,
                'blocking_reason': self.reason or self.name,
            }
            
            event_closes_inventory = self._event_closes_inventory()
            if self.blocking_type == 'event':
                # New housekeeping_state only changes if event closes inventory
                if event_closes_inventory:
                    room_vals['housekeeping_state'] = 'out_of_service'
                    _logger.info(f"Room {self.room_id.room_number} housekeeping_state set to OUT OF SERVICE (event closes inventory) for blocking {self.name}")
                else:
                    _logger.info(f"Room {self.room_id.room_number} housekeeping_state unchanged (event does not close inventory) for blocking {self.name}")
            else:  # maintenance, out_of_order, renovation, other
                room_vals['housekeeping_state'] = 'out_of_service'
                _logger.info(f"Room {self.room_id.room_number} housekeeping set to OUT OF SERVICE for {self.blocking_type.upper()} blocking {self.name}")
            
            self.room_id.write(room_vals)

    def action_complete(self):
        """Mark blocking as completed"""
        self.write({'status': 'completed'})
        # Return room to Inspected when blocking is completed
        if self.room_id:
            self.room_id.write({
                'housekeeping_state': 'inspected',
                'blocking_type': False,
                'blocking_reason': False,
            })

    def action_cancel(self):
        """Cancel the blocking"""
        self.write({'status': 'cancelled'})
        # Return room to Inspected when blocking is cancelled
        if self.room_id:
            self.room_id.write({
                'housekeeping_state': 'inspected',
                'blocking_type': False,
                'blocking_reason': False,
            })

    @api.model
    def get_room_availability(self, room_id, start_date, end_date):
        """Get room availability for a specific date range"""
        # Graceful handling when dates are not provided
        if not start_date or not end_date:
            return {
                'available': True,
                'blockings': []
            }
        domain = [
            ('room_id', '=', room_id),
            ('status', 'in', ['planned', 'active']),
            ('start_date', '<=', end_date),
            ('end_date', '>=', start_date),
        ]
        blockings = self.search(domain)
        # Only count blockings that close inventory
        event_closes_inventory = self._event_closes_inventory()
        closing_blockings = blockings.filtered(lambda b: b.blocking_type != 'event' or (b.blocking_type == 'event' and event_closes_inventory))
        return {
            'available': len(closing_blockings) == 0,
            'blockings': blockings.read(['name', 'start_date', 'end_date', 'blocking_type', 'reason'])
        }

    @api.model
    def get_rooms_availability(self, start_date, end_date, room_type_id=None):
        """Get availability for all rooms in a date range"""
        domain = [
            ('status', 'in', ['planned', 'active']),
            ('start_date', '<=', end_date),
            ('end_date', '>=', start_date),
        ]
        if room_type_id:
            domain.append(('room_type_id', '=', room_type_id))
        blockings = self.search(domain)
        # If needed by callers, keep all blockings grouped; callers can decide which ones close inventory
        room_blockings = {}
        for blocking in blockings:
            room_id = blocking.room_id.id
            room_blockings.setdefault(room_id, []).append(blocking)
        return room_blockings

    @api.model
    def _event_closes_inventory(self) -> bool:
        """Read configuration whether event blocking closes inventory."""
        params = self.env['ir.config_parameter'].sudo()
        return params.get_param('modulio_hotelcore.event_closes_inventory', 'False') == 'True'

    @api.model
    def create_blocking_from_booking(self, room_id, start_date, end_date, booking_reference='', guest_name=''):
        """Create room blocking from booking system integration"""
        blocking_vals = {
            'name': f'Booking {booking_reference} - {guest_name}' if booking_reference else f'Booking - {guest_name}',
            'room_id': room_id,
            'start_date': start_date,
            'end_date': end_date,
            'blocking_type': 'event',
            'reason': f'Room blocked for booking {booking_reference}',
            'responsible_user_id': self.env.user.id,
            'status': 'active',
        }
        return self.create(blocking_vals)

    @api.model
    def get_room_blockings(self, room_id, start_date, end_date):
        """Get room blockings for a specific date range (integration point)"""
        domain = [
            ('room_id', '=', room_id),
            ('start_date', '<=', end_date),
            ('end_date', '>=', start_date),
        ]
        
        blockings = self.search(domain)
        return blockings.read(['name', 'start_date', 'end_date', 'blocking_type', 'status', 'reason'])

    @api.model
    def cancel_blocking(self, blocking_id, reason=''):
        """Cancel a room blocking (integration point)"""
        blocking = self.browse(blocking_id)
        if not blocking.exists():
            raise ValidationError("Blocking not found")
        
        blocking.write({
            'status': 'cancelled',
            'reason': f"{blocking.reason}\n\nCancelled: {reason}" if reason else f"{blocking.reason}\n\nCancelled"
        })
        
        return True

    _sql_constraints = [
        ('dates_check', 'CHECK (start_date <= end_date)', 
         'Start date must be before or equal to end date!'),
    ]
