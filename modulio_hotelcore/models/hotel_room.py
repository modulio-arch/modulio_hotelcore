# -*- coding: utf-8 -*-

from odoo import models, fields, api
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
        string='Floor Number',
        required=True,
        index=True,
        tracking=True,
        help='Floor number where the room is located'
    )
    floor_id = fields.Many2one(
        'hotel.floor',
        string='Floor',
        required=False,  # Temporary: will be set to True after data migration
        index=True,
        ondelete='restrict',
        tracking=True,
        compute='_compute_floor_id',
        store=True,
        help='Floor where the room is located'
    )
    
    @api.depends('floor')
    def _compute_floor_id(self):
        """Auto-populate floor_id based on floor number"""
        for record in self:
            if record.floor is not None and not record.floor_id:
                floor = self.env['hotel.floor'].search([
                    ('floor_number', '=', record.floor),
                    ('company_id', '=', record.company_id.id)
                ], limit=1)
                if floor:
                    record.floor_id = floor.id
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
    
    # Single state system for room status management
    state = fields.Selection([
        ('clean', 'Clean'),                    # Ready for guest
        ('check_in', 'Check In'),              # Guest checked in
        ('check_out', 'Check Out'),            # Guest checked out
        ('dirty', 'Dirty'),                    # Needs cleaning
        ('make_up_room', 'Make Up Room'),      # Currently being cleaned
        ('inspected', 'Inspected'),            # Cleaned and inspected
        ('out_of_service', 'Out of Service'),  # Temporary maintenance
        ('out_of_order', 'Out of Order'),      # Long-term maintenance/repair
        ('house_use', 'House Use'),            # Staff accommodation
    ],
        string='Room Status',
        default='clean',
        required=True,
        index=True,
        tracking=True,
        help='Current room status - single state system for Front Office, Housekeeping, and Maintenance workflows'
    )

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
    
    # Status history fields
    status_history_count = fields.Integer(
        string='Status History Count',
        compute='_compute_status_history_count',
        store=True,
        help='Number of status change records for this room'
    )
    status_history_ids = fields.One2many(
        'hotel.room.status.history',
        'room_id',
        string='Status History',
        help='Status change history for this room'
    )
    
    # Room amenities fields
    room_amenity_count = fields.Integer(
        string='Amenities Count',
        compute='_compute_room_amenity_count',
        store=True,
        help='Number of amenities assigned to this room'
    )
    room_amenity_ids = fields.One2many(
        'hotel.room.amenity',
        'room_id',
        string='Room Amenities',
        help='Amenities assigned to this room'
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

    @api.depends('status_history_ids')
    def _compute_status_history_count(self):
        """Compute the number of status history records for this room"""
        for record in self:
            record.status_history_count = len(record.status_history_ids)

    @api.depends('room_amenity_ids')
    def _compute_room_amenity_count(self):
        """Compute the number of amenities assigned to this room"""
        for record in self:
            record.room_amenity_count = len(record.room_amenity_ids)

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to set last_status_change"""
        for vals in vals_list:
            if 'state' in vals:
                vals['last_status_change'] = fields.Datetime.now()
        
        return super().create(vals_list)

    def write(self, vals):
        """Override write to track status changes"""
        if 'state' in vals:
            vals['last_status_change'] = fields.Datetime.now()
        
        return super().write(vals)


    # -----------------------------
    # New helpers for simplified states
    # -----------------------------

    def set_state(self, new_state: str) -> None:
        """Set room state to one of: clean, dirty, make_up_room, inspected, out_of_service, out_of_order, house_use."""
        self.ensure_one()
        allowed = {'clean', 'dirty', 'make_up_room', 'inspected', 'out_of_service', 'out_of_order', 'house_use'}
        if new_state not in allowed:
            raise ValidationError(f"Invalid state: {new_state}")
        self.write({'state': new_state})

    # Legacy methods for backward compatibility (deprecated)
    def mark_dirty(self) -> None:
        """Deprecated: Use action_start_cleaning instead"""
        self.set_state('dirty')

    def mark_clean(self) -> None:
        """Deprecated: Use action_final_inspection instead"""
        self.set_state('clean')

    def mark_inspected(self) -> None:
        """Deprecated: Use action_finish_cleaning instead"""
        self.set_state('inspected')

    def mark_out_of_service(self) -> None:
        """Deprecated: Use action_maintenance_light instead"""
        self.set_state('out_of_service')

    # -----------------------------
    # Security Helper Methods
    # -----------------------------
    
    def _check_front_office_access(self):
        """Check if user has Front Office access"""
        if not self.env.user.has_group('modulio_hotelcore.group_hotel_front_office'):
            raise ValidationError("Access denied: Front Office permission required")
    
    def _check_housekeeping_access(self):
        """Check if user has Housekeeping access"""
        if not self.env.user.has_group('modulio_hotelcore.group_hotel_housekeeping'):
            raise ValidationError("Access denied: Housekeeping permission required")
    
    def _check_maintenance_access(self):
        """Check if user has Maintenance access"""
        if not self.env.user.has_group('modulio_hotelcore.group_hotel_maintenance'):
            raise ValidationError("Access denied: Maintenance permission required")

    # -----------------------------
    # New simplified transition methods for Front Office and Housekeeping
    # -----------------------------

    def action_assign_house_use(self, staff_name='', notes=''):
        """Front Office: Assign room to house use (clean/inspected -> house_use)"""
        self.ensure_one()
        self._check_front_office_access()
        if self.state not in ['clean', 'inspected']:
            raise ValidationError(f"Room must be clean or inspected to assign to house use. Current state: {self.state}")
        
        # Store old values for history
        old_values = {
            'state': self.state,
            'maintenance_required': self.maintenance_required,
        }
        
        self.write({
            'state': 'house_use',
            'status_change_reason': f"House Use: {staff_name}. {notes}",
            'last_status_change': fields.Datetime.now()
        })
        
        # Create status history record
        new_values = {
            'state': 'house_use',
            'maintenance_required': self.maintenance_required,
        }
        
        self.env['hotel.room.status.history'].create_status_change(
            room_id=self.id,
            change_type='fo',
            old_values=old_values,
            new_values=new_values,
            change_reason=f"House Use: {staff_name}. {notes}",
            change_method='action_assign_house_use',
            change_notes=notes
        )

    def action_staff_checkout(self, staff_name='', notes=''):
        """Front Office: Staff check-out from house use (house_use -> dirty)"""
        self.ensure_one()
        self._check_front_office_access()
        if self.state != 'house_use':
            raise ValidationError(f"Room must be in house use to check-out staff. Current state: {self.state}")
        
        # Store old values for history
        old_values = {
            'state': self.state,
            'maintenance_required': self.maintenance_required,
        }
        
        self.write({
            'state': 'dirty',
            'status_change_reason': f"Staff Check-out: {staff_name}. {notes}",
            'last_status_change': fields.Datetime.now()
        })
        
        # Create status history record
        new_values = {
            'state': 'dirty',
            'maintenance_required': self.maintenance_required,
        }
        
        self.env['hotel.room.status.history'].create_status_change(
            room_id=self.id,
            change_type='fo',
            old_values=old_values,
            new_values=new_values,
            change_reason=f"Staff Check-out: {staff_name}. {notes}",
            change_method='action_staff_checkout',
            change_notes=notes
        )

    def action_check_in(self, guest_name='', notes=''):
        """Front Office: Check in guest (clean/inspected -> check_in)"""
        self.ensure_one()
        self._check_front_office_access()
        if self.state not in ['clean', 'inspected']:
            raise ValidationError(f"Room must be clean or inspected to check in guest. Current state: {self.state}")
        
        # Store old values for history
        old_values = {
            'state': self.state,
            'maintenance_required': self.maintenance_required,
        }
        
        self.write({
            'state': 'check_in',
            'status_change_reason': f"Guest Check-in: {guest_name}. {notes}",
            'last_status_change': fields.Datetime.now()
        })
        
        # Create status history record
        new_values = {
            'state': 'check_in',
            'maintenance_required': self.maintenance_required,
        }
        
        self.env['hotel.room.status.history'].create_status_change(
            room_id=self.id,
            change_type='fo',
            old_values=old_values,
            new_values=new_values,
            change_reason=f"Guest Check-in: {guest_name}. {notes}",
            change_method='action_check_in',
            change_notes=notes
        )

    def action_check_out(self, guest_name='', notes=''):
        """Front Office: Check out guest (check_in -> check_out)"""
        self.ensure_one()
        self._check_front_office_access()
        if self.state != 'check_in':
            raise ValidationError(f"Room must be checked in to checkout guest. Current state: {self.state}")
        
        # Store old values for history
        old_values = {
            'state': self.state,
            'maintenance_required': self.maintenance_required,
        }
        
        self.write({
            'state': 'check_out',
            'status_change_reason': f"Guest Check-out: {guest_name}. {notes}",
            'last_status_change': fields.Datetime.now()
        })
        
        # Create status history record
        new_values = {
            'state': 'check_out',
            'maintenance_required': self.maintenance_required,
        }
        
        self.env['hotel.room.status.history'].create_status_change(
            room_id=self.id,
            change_type='fo',
            old_values=old_values,
            new_values=new_values,
            change_reason=f"Guest Check-out: {guest_name}. {notes}",
            change_method='action_check_out',
            change_notes=notes
        )

    def action_room_ready_for_cleaning(self, notes=''):
        """Front Office: Mark room ready for cleaning after checkout (check_out -> dirty)"""
        self.ensure_one()
        self._check_front_office_access()
        if self.state != 'check_out':
            raise ValidationError(f"Room must be checked out to mark ready for cleaning. Current state: {self.state}")
        
        # Store old values for history
        old_values = {
            'state': self.state,
            'maintenance_required': self.maintenance_required,
        }
        
        self.write({
            'state': 'dirty',
            'status_change_reason': f"Room ready for cleaning. {notes}",
            'last_status_change': fields.Datetime.now()
        })
        
        # Create status history record
        new_values = {
            'state': 'dirty',
            'maintenance_required': self.maintenance_required,
        }
        
        self.env['hotel.room.status.history'].create_status_change(
            room_id=self.id,
            change_type='fo',
            old_values=old_values,
            new_values=new_values,
            change_reason=f"Room ready for cleaning. {notes}",
            change_method='action_room_ready_for_cleaning',
            change_notes=notes
        )

    def action_start_cleaning(self, notes=''):
        """Housekeeping: Start cleaning dirty room (dirty -> make_up_room)"""
        self.ensure_one()
        self._check_housekeeping_access()
        if self.state != 'dirty':
            raise ValidationError(f"Room must be dirty to start cleaning. Current state: {self.state}")
        
        # Store old values for history
        old_values = {
            'state': self.state,
            'maintenance_required': self.maintenance_required,
        }
        
        self.write({
            'state': 'make_up_room',
            'status_change_reason': f"Started cleaning. {notes}",
            'last_status_change': fields.Datetime.now()
        })
        
        # Create status history record
        new_values = {
            'state': 'make_up_room',
            'maintenance_required': self.maintenance_required,
        }
        
        self.env['hotel.room.status.history'].create_status_change(
            room_id=self.id,
            change_type='hk',
            old_values=old_values,
            new_values=new_values,
            change_reason=f"Started cleaning. {notes}",
            change_method='action_start_cleaning',
            change_notes=notes
        )

    def action_finish_cleaning(self, notes=''):
        """Housekeeping: Finish cleaning (make_up_room -> inspected)"""
        self.ensure_one()
        self._check_housekeeping_access()
        if self.state != 'make_up_room':
            raise ValidationError(f"Room must be in make up room to finish cleaning. Current state: {self.state}")
        
        # Store old values for history
        old_values = {
            'state': self.state,
            'maintenance_required': self.maintenance_required,
        }
        
        self.write({
            'state': 'inspected',
            'status_change_reason': f"Finished cleaning. {notes}",
            'last_status_change': fields.Datetime.now()
        })
        
        # Create status history record
        new_values = {
            'state': 'inspected',
            'maintenance_required': self.maintenance_required,
        }
        
        self.env['hotel.room.status.history'].create_status_change(
            room_id=self.id,
            change_type='hk',
            old_values=old_values,
            new_values=new_values,
            change_reason=f"Finished cleaning. {notes}",
            change_method='action_finish_cleaning',
            change_notes=notes
        )

    def action_final_inspection(self, notes=''):
        """Housekeeping: Final inspection (inspected -> clean)"""
        self.ensure_one()
        self._check_housekeeping_access()
        if self.state != 'inspected':
            raise ValidationError(f"Room must be inspected to pass final inspection. Current state: {self.state}")
        
        # Store old values for history
        old_values = {
            'state': self.state,
            'maintenance_required': self.maintenance_required,
        }
        
        self.write({
            'state': 'clean',
            'status_change_reason': f"Final inspection passed. {notes}",
            'last_status_change': fields.Datetime.now()
        })
        
        # Create status history record
        new_values = {
            'state': 'clean',
            'maintenance_required': self.maintenance_required,
        }
        
        self.env['hotel.room.status.history'].create_status_change(
            room_id=self.id,
            change_type='hk',
            old_values=old_values,
            new_values=new_values,
            change_reason=f"Final inspection passed. {notes}",
            change_method='action_final_inspection',
            change_notes=notes
        )

    def action_maintenance_light(self, notes=''):
        """Housekeeping: Put room under light maintenance (clean -> out_of_service)"""
        self.ensure_one()
        self._check_housekeeping_access()
        if self.state != 'clean':
            raise ValidationError(f"Room must be clean to put under light maintenance. Current state: {self.state}")
        
        # Store old values for history
        old_values = {
            'state': self.state,
            'maintenance_required': self.maintenance_required,
        }
        
        self.write({
            'state': 'out_of_service',
            'maintenance_required': True,
            'status_change_reason': f"Light maintenance started. {notes}",
            'last_status_change': fields.Datetime.now()
        })
        
        # Create status history record
        new_values = {
            'state': 'out_of_service',
            'maintenance_required': True,
        }
        
        self.env['hotel.room.status.history'].create_status_change(
            room_id=self.id,
            change_type='hk',
            old_values=old_values,
            new_values=new_values,
            change_reason=f"Light maintenance started. {notes}",
            change_method='action_maintenance_light',
            change_notes=notes
        )

    def action_maintenance_heavy(self, notes=''):
        """Housekeeping: Put room under heavy maintenance (clean -> out_of_order)"""
        self.ensure_one()
        self._check_housekeeping_access()
        if self.state != 'clean':
            raise ValidationError(f"Room must be clean to put under heavy maintenance. Current state: {self.state}")
        
        # Store old values for history
        old_values = {
            'state': self.state,
            'maintenance_required': self.maintenance_required,
        }
        
        self.write({
            'state': 'out_of_order',
            'maintenance_required': True,
            'status_change_reason': f"Heavy maintenance started. {notes}",
            'last_status_change': fields.Datetime.now()
        })
        
        # Create status history record
        new_values = {
            'state': 'out_of_order',
            'maintenance_required': True,
        }
        
        self.env['hotel.room.status.history'].create_status_change(
            room_id=self.id,
            change_type='hk',
            old_values=old_values,
            new_values=new_values,
            change_reason=f"Heavy maintenance started. {notes}",
            change_method='action_maintenance_heavy',
            change_notes=notes
        )

    def action_complete_maintenance(self, notes=''):
        """Housekeeping: Complete maintenance (out_of_service/out_of_order -> clean)"""
        self.ensure_one()
        self._check_housekeeping_access()
        if self.state not in ['out_of_service', 'out_of_order']:
            raise ValidationError(f"Room must be under maintenance to complete. Current state: {self.state}")
        
        # Store old values for history
        old_values = {
            'state': self.state,
            'maintenance_required': self.maintenance_required,
        }
        
        self.write({
            'state': 'clean',
            'maintenance_required': False,
            'status_change_reason': f"Maintenance completed. {notes}",
            'last_status_change': fields.Datetime.now()
        })
        
        # Create status history record
        new_values = {
            'state': 'clean',
            'maintenance_required': False,
        }
        
        self.env['hotel.room.status.history'].create_status_change(
            room_id=self.id,
            change_type='hk',
            old_values=old_values,
            new_values=new_values,
            change_reason=f"Maintenance completed. {notes}",
            change_method='action_complete_maintenance',
            change_notes=notes
        )

    def is_sellable(self) -> bool:
        """Check if room is sellable based on single state and blocking."""
        self.ensure_one()
        
        # Room must be clean or inspected to be sellable
        if self.state not in ['clean', 'inspected']:
            return False
        
        # Honor housekeeping policy - require inspected status
        require_inspected = self.env['ir.config_parameter'].sudo().get_param(
            'modulio_hotelcore.require_inspected_to_sell', 'False'
        ) == 'True'
        if require_inspected and self.state != 'inspected':
            return False
        
        # Check for active blockings
        active_blockings = self.blocking_ids.filtered(lambda b: b.status == 'active')
        if active_blockings:
            return False
        
        return True


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
        
        # Check room availability using single state
        state_available = self.state in ['clean', 'inspected']
        not_maintenance = self.state not in ['out_of_service', 'out_of_order']
        
        # Housekeeping policy via config: require inspected to sell
        require_inspected = self.env['ir.config_parameter'].sudo().get_param(
            'modulio_hotelcore.require_inspected_to_sell', 'False'
        ) == 'True'
        state_ok = self.state == 'inspected' if require_inspected else state_available

        # Room is available if state is clean/inspected, not under maintenance, not blocked
        available = state_available and not_maintenance and blocking['available'] and state_ok
        
        return {
            'room_id': self.id,
            'room_number': self.room_number,
            'room_type_id': self.room_type_id.id,
            'room_type_name': self.room_type_id.name,
            'state': self.state,
            'state_available': state_available,
            'not_maintenance': not_maintenance,
            'not_blocked': blocking['available'],
            'blockings': blocking['blockings'],
            'available': available,
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
            'state': self.state,
            'available': availability['available'],
            'blockings': availability['blockings'],
            'room_number': self.room_number,
            'floor': self.floor,
            'room_type': self.room_type_id.name,
        }

    def _get_calendar_color(self):
        """Get color for calendar display based on single state"""
        color_map = {
            'clean': '#28a745',          # Green - Ready for guest
            'dirty': '#ffc107',          # Yellow - Needs cleaning
            'make_up_room': '#17a2b8',   # Blue - Being cleaned
            'inspected': '#20c997',      # Teal - Cleaned and inspected
            'out_of_service': '#fd7e14', # Orange - Light maintenance
            'out_of_order': '#dc3545',   # Red - Heavy maintenance
            'house_use': '#6f42c1',      # Purple - Staff accommodation
        }
        return color_map.get(self.state, '#6c757d')  # Gray - Unknown

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

    def action_view_status_history(self):
        """Action to view status history for this room"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Status History - {self.room_number}',
            'res_model': 'hotel.room.status.history',
            'view_mode': 'list,kanban,form',
            'domain': [('room_id', '=', self.id)],
            'context': {'default_room_id': self.id},
        }

    def action_view_room_amenities(self):
        """Action to view amenities for this room"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Room Amenities - {self.room_number}',
            'res_model': 'hotel.room.amenity',
            'view_mode': 'list,kanban,form',
            'domain': [('room_id', '=', self.id)],
            'context': {'default_room_id': self.id},
        }

    def action_calendar_drop(self, new_state, start_date, end_date, reason=''):
        """Handle drag & drop in calendar view to change room state or create blocking"""
        self.ensure_one()
        
        if new_state in ['clean', 'dirty', 'make_up_room', 'inspected', 'out_of_service', 'out_of_order', 'house_use']:
            # Change room state
            self.set_state(new_state)
            if reason:
                self.write({
                    'status_change_reason': reason,
                    'last_status_change': fields.Datetime.now()
                })
        elif new_state == 'blocked':
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
                    'state': room.state,
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
        
        # Use new simplified reservation method - assign to house use for now
        # In real implementation, this would be handled by Front Office module
        room.action_assign_house_use(guest_name, notes)
        
        return {
            'success': True,
            'room_number': room.room_number,
            'room_type': room.room_type_id.name,
            'state': room.state,
            'message': f"Room {room.room_number} has been assigned successfully"
        }

    _sql_constraints = [
        ('room_number_floor_unique', 'UNIQUE(room_number, floor)', 
         'Room number must be unique per floor!'),
    ]
