# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class HotelRoom(models.Model):
    _name = 'hotel.room'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Hotel Room'
    _order = 'floor, room_number'

    name = fields.Char(
        string='Room Name',
        compute='_compute_name',
        store=True,
        help='Display name for the room'
    )
    room_number = fields.Char(
        string='Room Number',
        required=True,
        index=True,
        tracking=True,
        help='Room number (e.g., 101, 201A)'
    )
    floor = fields.Integer(
        string='Floor',
        required=True,
        index=True,
        tracking=True,
        help='Floor number where the room is located'
    )
    room_type_id = fields.Many2one(
        'hotel.room.type',
        string='Room Type',
        required=True,
        index=True,
        ondelete='restrict',
        tracking=True,
        help='Type of the room'
    )
    description = fields.Text(
        string='Description',
        help='Additional description for the room'
    )
    status = fields.Selection([
        ('vacant_ready', 'Vacant Ready'),
        ('reserved', 'Reserved'),
        ('occupied', 'Occupied'),
        ('dirty', 'Dirty'),
        ('inspected', 'Inspected'),
        ('event', 'Event'),
        ('out_of_service', 'Out of Service'),
    ], string='Status', default='vacant_ready', required=True,
       tracking=True, help='Current status of the room')
    
    # Status transition fields
    last_status_change = fields.Datetime(
        string='Last Status Change',
        default=fields.Datetime.now,
        help='When the status was last changed'
    )
    status_change_reason = fields.Text(
        string='Status Change Reason',
        help='Reason for the last status change'
    )
    
    # Blocking information
    blocking_type = fields.Selection([
        ('maintenance', 'Maintenance'),
        ('event', 'Event'),
        ('out_of_order', 'Out of Order'),
        ('renovation', 'Renovation'),
        ('other', 'Other'),
    ], string='Blocking Type', tracking=True,
       help='Current blocking type if room is blocked')
    blocking_reason = fields.Text(
        string='Blocking Reason',
        help='Reason for current blocking'
    )
    
    # Room properties
    max_occupancy = fields.Integer(
        string='Max Occupancy',
        related='room_type_id.max_occupancy',
        store=True,
        help='Maximum number of guests for this room'
    )
    size_sqm = fields.Float(
        string='Size (sqm)',
        related='room_type_id.size_sqm',
        store=True,
        help='Room size in square meters'
    )
    base_price = fields.Monetary(
        string='Base Price',
        related='room_type_id.base_price',
        store=True,
        help='Base price for this room'
    )
    currency_id = fields.Many2one(
        'res.currency',
        related='room_type_id.currency_id',
        store=True,
        help='Currency for pricing'
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True,
        index=True,
        ondelete='restrict'
    )
    
    # Maintenance and service
    maintenance_required = fields.Boolean(
        string='Maintenance Required',
        default=False,
        tracking=True,
        help='Whether the room requires maintenance'
    )
    maintenance_notes = fields.Text(
        string='Maintenance Notes',
        help='Notes about maintenance requirements'
    )
    
    # System fields
    create_date = fields.Datetime(
        string='Created On',
        readonly=True,
        help='When the room was created'
    )
    
    # Room blocking fields
    blocking_count = fields.Integer(
        string='Blocking Count',
        compute='_compute_blocking_count',
        store=True,
        help='Number of active blockings for this room'
    )
    blocking_ids = fields.One2many(
        'hotel.room.blocking',
        'room_id',
        string='Room Blockings',
        help='Blockings for this room'
    )

    @api.depends('room_number', 'floor')
    def _compute_name(self):
        for record in self:
            record.name = f"Floor {record.floor} - Room {record.room_number}"

    @api.depends('blocking_ids', 'blocking_ids.status')
    def _compute_blocking_count(self):
        """Compute the number of active blockings for this room"""
        for record in self:
            record.blocking_count = len(record.blocking_ids.filtered(
                lambda b: b.status in ['planned', 'active']
            ))

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to set last_status_change"""
        for vals in vals_list:
            if 'status' in vals:
                vals['last_status_change'] = fields.Datetime.now()
        return super().create(vals_list)

    def write(self, vals):
        """Override write to track status changes"""
        if 'status' in vals:
            vals['last_status_change'] = fields.Datetime.now()
        return super().write(vals)

    def action_change_status(self, new_status, reason=''):
        """Change room status with validation"""
        self.ensure_one()
        
        # Validate status transition
        valid_transitions = {
            'vacant_ready': ['reserved', 'out_of_service'],
            'reserved': ['occupied', 'vacant_ready', 'out_of_service'],
            'occupied': ['dirty', 'out_of_service'],
            'dirty': ['inspected', 'out_of_service'],
            'inspected': ['vacant_ready', 'dirty', 'out_of_service'],
            'out_of_service': ['vacant_ready', 'dirty', 'inspected'],
        }
        
        current_status = self.status
        if new_status not in valid_transitions.get(current_status, []):
            raise ValidationError(
                f"Cannot change status from {current_status} to {new_status}. "
                f"Valid transitions from {current_status} are: {', '.join(valid_transitions.get(current_status, []))}"
            )
        
        self.write({
            'status': new_status,
            'status_change_reason': reason,
            'last_status_change': fields.Datetime.now()
        })

    def action_vacant_ready(self):
        """Set room to Vacant Ready status"""
        self.action_change_status('vacant_ready', 'Room cleaned and ready for guests')

    def action_reserved(self):
        """Set room to Reserved status"""
        self.action_change_status('reserved', 'Room reserved for guest')

    def action_occupied(self):
        """Set room to Occupied status"""
        self.action_change_status('occupied', 'Guest checked in')

    def action_dirty(self):
        """Set room to Dirty status"""
        self.action_change_status('dirty', 'Guest checked out, room needs cleaning')

    def action_inspected(self):
        """Set room to Inspected status"""
        self.action_change_status('inspected', 'Room inspected after cleaning')

    def action_out_of_service(self):
        """Set room to Out of Service status"""
        self.action_change_status('out_of_service', 'Room taken out of service for maintenance')

    @api.constrains('room_number', 'floor')
    def _check_room_number_unique(self):
        """Ensure room number is unique per floor"""
        for record in self:
            if record.room_number and record.floor:
                existing = self.search([
                    ('room_number', '=', record.room_number),
                    ('floor', '=', record.floor),
                    ('id', '!=', record.id)
                ])
                if existing:
                    raise ValidationError(
                        f"Room number {record.room_number} already exists on floor {record.floor}"
                    )

    def get_availability(self, start_date, end_date):
        """Get room availability for a specific date range"""
        self.ensure_one()
        
        # Check if room is blocked
        blocking = self.env['hotel.room.blocking'].get_room_availability(
            self.id, start_date, end_date
        )
        
        # Check room status
        status_available = self.status in ['vacant_ready', 'inspected']
        
        return {
            'room_id': self.id,
            'room_number': self.room_number,
            'room_type_id': self.room_type_id.id,
            'room_type_name': self.room_type_id.name,
            'status': self.status,
            'status_available': status_available,
            'not_blocked': blocking['available'],
            'blockings': blocking['blockings'],
            'available': status_available and blocking['available'],
            'floor': self.floor,
            'max_occupancy': self.max_occupancy,
        }

    def get_availability_calendar_data(self, start_date, end_date):
        """Get calendar data for room availability"""
        self.ensure_one()
        
        availability = self.get_availability(start_date, end_date)
        
        return {
            'id': self.id,
            'title': f"Room {self.room_number} - {self.room_type_id.name}",
            'start': start_date,
            'end': end_date,
            'color': self._get_calendar_color(),
            'status': self.status,
            'available': availability['available'],
            'blockings': availability['blockings'],
            'room_number': self.room_number,
            'floor': self.floor,
            'room_type': self.room_type_id.name,
        }

    def _get_calendar_color(self):
        """Get color for calendar display based on room status"""
        color_map = {
            'vacant_ready': '#28a745',      # Green
            'reserved': '#17a2b8',          # Blue
            'occupied': '#ffc107',          # Yellow
            'dirty': '#fd7e14',             # Orange
            'inspected': '#6c757d',         # Gray
            'out_of_service': '#dc3545',    # Red
        }
        return color_map.get(self.status, '#6c757d')

    @api.model
    def get_rooms_availability_calendar(self, start_date, end_date, room_type_id=None, floor=None):
        """Get calendar data for all rooms in a date range"""
        domain = []
        
        if room_type_id:
            domain.append(('room_type_id', '=', room_type_id))
        
        if floor:
            domain.append(('floor', '=', floor))
        
        rooms = self.search(domain)
        calendar_data = []
        
        for room in rooms:
            room_data = room.get_availability_calendar_data(start_date, end_date)
            calendar_data.append(room_data)
        
        return calendar_data

    def action_view_blockings(self):
        """Action to view blockings for this room"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Room Blockings - {self.room_number}',
            'res_model': 'hotel.room.blocking',
            'view_mode': 'list,calendar,form',
            'domain': [('room_id', '=', self.id)],
            'context': {'default_room_id': self.id},
        }

    def action_calendar_drop(self, new_status, start_date, end_date, reason=''):
        """Handle drag & drop in calendar view to change room status or create blocking"""
        self.ensure_one()
        
        if new_status in ['vacant_ready', 'reserved', 'occupied', 'dirty', 'inspected', 'out_of_service']:
            # Change room status
            self.action_change_status(new_status, reason)
        elif new_status == 'blocked':
            # Create room blocking
            blocking_vals = {
                'name': f'Blocking for {self.room_number}',
                'room_id': self.id,
                'start_date': start_date,
                'end_date': end_date,
                'blocking_type': 'maintenance',
                'reason': reason or 'Room blocked from calendar',
                'responsible_user_id': self.env.user.id,
            }
            self.env['hotel.room.blocking'].create(blocking_vals)
        
        return True

    @api.model
    def get_available_rooms(self, start_date, end_date, room_type_id=None, floor=None):
        """Get available rooms for booking integration"""
        domain = []
        
        if room_type_id:
            domain.append(('room_type_id', '=', room_type_id))
        
        if floor:
            domain.append(('floor', '=', floor))
        
        rooms = self.search(domain)
        available_rooms = []
        
        for room in rooms:
            availability = room.get_availability(start_date, end_date)
            if availability['available']:
                available_rooms.append({
                    'room_id': room.id,
                    'room_number': room.room_number,
                    'room_type_id': room.room_type_id.id,
                    'room_type_name': room.room_type_id.name,
                    'floor': room.floor,
                    'max_occupancy': room.max_occupancy,
                    'base_price': room.base_price,
                    'currency_id': room.currency_id.id,
                })
        
        return available_rooms

    @api.model
    def check_room_availability(self, room_id, start_date, end_date):
        """Check if specific room is available for booking"""
        room = self.browse(room_id)
        if not room.exists():
            return False
        
        availability = room.get_availability(start_date, end_date)
        return availability['available']

    @api.model
    def reserve_room(self, room_id, start_date, end_date, guest_name='', notes=''):
        """Reserve a room (integration point for Front Office)"""
        room = self.browse(room_id)
        if not room.exists():
            raise ValidationError("Room not found")
        
        if not room.check_room_availability(room_id, start_date, end_date):
            raise ValidationError(f"Room {room.room_number} is not available for the selected dates")
        
        # Change room status to reserved
        room.action_change_status('reserved', f"Reserved for {guest_name}. {notes}")
        
        return {
            'success': True,
            'room_number': room.room_number,
            'room_type': room.room_type_id.name,
            'message': f"Room {room.room_number} has been reserved successfully"
        }

    _sql_constraints = [
        ('room_number_floor_unique', 'UNIQUE(room_number, floor)', 
         'Room number must be unique per floor!'),
    ]
