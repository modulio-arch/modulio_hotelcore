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
    
    # New simplified core states (Front Office focus): occupancy_state
    occupancy_state = fields.Selection([
        ('available', 'Available'),
        ('reserved', 'Reserved'),
        ('occupied', 'Occupied'),
    ],
        string='Occupancy State',
        default='available',
        required=True,
        index=True,
        tracking=True,
        help='Core room occupancy state used by Front Office and integrations'
    )

    # New simplified housekeeping state (Housekeeping focus)
    housekeeping_state = fields.Selection([
        ('dirty', 'Dirty'),
        ('clean', 'Clean'),
        ('inspected', 'Inspected'),
        ('out_of_service', 'Out of Service'),
    ],
        string='Housekeeping State',
        default='inspected',
        required=True,
        index=True,
        tracking=True,
        help='Housekeeping cleanliness and service state used by housekeeping workflows'
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
            if 'occupancy_state' in vals or 'housekeeping_state' in vals:
                vals['last_status_change'] = fields.Datetime.now()
        
        return super().create(vals_list)

    def write(self, vals):
        """Override write to track status changes"""
        if 'occupancy_state' in vals or 'housekeeping_state' in vals:
            vals['last_status_change'] = fields.Datetime.now()
        
        return super().write(vals)


    # -----------------------------
    # New helpers for simplified states
    # -----------------------------

    def set_occupancy_state(self, new_state: str) -> None:
        """Set occupancy_state to one of: available, reserved, occupied.
        Does not manage transitions yet; validation is intentionally light here.
        """
        self.ensure_one()
        allowed = {'available', 'reserved', 'occupied'}
        if new_state not in allowed:
            raise ValidationError(f"Invalid occupancy_state: {new_state}")
        self.write({'occupancy_state': new_state})

    def set_housekeeping_state(self, new_state: str) -> None:
        """Set housekeeping_state to one of: dirty, clean, inspected, out_of_service."""
        self.ensure_one()
        allowed = {'dirty', 'clean', 'inspected', 'out_of_service'}
        if new_state not in allowed:
            raise ValidationError(f"Invalid housekeeping_state: {new_state}")
        self.write({'housekeeping_state': new_state})

    def mark_dirty(self) -> None:
        self.set_housekeeping_state('dirty')

    def mark_clean(self) -> None:
        self.set_housekeeping_state('clean')

    def mark_inspected(self) -> None:
        self.set_housekeeping_state('inspected')

    def mark_out_of_service(self) -> None:
        self.set_housekeeping_state('out_of_service')

    # -----------------------------
    # New simplified transition methods for Front Office and Housekeeping
    # -----------------------------

    def action_check_in(self, guest_name='', notes=''):
        """Check-in: reserved -> occupied, housekeeping -> dirty"""
        self.ensure_one()
        if self.occupancy_state != 'reserved':
            raise ValidationError(f"Room must be reserved to check-in. Current state: {self.occupancy_state}")
        
        # Store old values for history
        old_values = {
            'occupancy_state': self.occupancy_state,
            'housekeeping_state': self.housekeeping_state,
            'maintenance_required': self.maintenance_required,
        }
        
        self.write({
            'occupancy_state': 'occupied',
            'housekeeping_state': 'dirty',
            'status_change_reason': f"Check-in: {guest_name}. {notes}",
            'last_status_change': fields.Datetime.now()
        })
        
        # Create status history record
        new_values = {
            'occupancy_state': 'occupied',
            'housekeeping_state': 'dirty',
            'maintenance_required': self.maintenance_required,
        }
        
        self.env['hotel.room.status.history'].create_status_change(
            room_id=self.id,
            change_type='occupancy',
            old_values=old_values,
            new_values=new_values,
            change_reason=f"Check-in: {guest_name}. {notes}",
            change_method='action_check_in',
            change_notes=notes
        )

    def action_check_out(self, guest_name='', notes=''):
        """Check-out: occupied -> available, housekeeping -> dirty"""
        self.ensure_one()
        if self.occupancy_state != 'occupied':
            raise ValidationError(f"Room must be occupied to check-out. Current state: {self.occupancy_state}")
        
        # Store old values for history
        old_values = {
            'occupancy_state': self.occupancy_state,
            'housekeeping_state': self.housekeeping_state,
            'maintenance_required': self.maintenance_required,
        }
        
        self.write({
            'occupancy_state': 'available',
            'housekeeping_state': 'dirty',
            'status_change_reason': f"Check-out: {guest_name}. {notes}",
            'last_status_change': fields.Datetime.now()
        })
        
        # Create status history record
        new_values = {
            'occupancy_state': 'available',
            'housekeeping_state': 'dirty',
            'maintenance_required': self.maintenance_required,
        }
        
        self.env['hotel.room.status.history'].create_status_change(
            room_id=self.id,
            change_type='occupancy',
            old_values=old_values,
            new_values=new_values,
            change_reason=f"Check-out: {guest_name}. {notes}",
            change_method='action_check_out',
            change_notes=notes
        )

    def action_reserve(self, guest_name='', notes=''):
        """Reserve: available -> reserved"""
        self.ensure_one()
        if self.occupancy_state != 'available':
            raise ValidationError(f"Room must be available to reserve. Current state: {self.occupancy_state}")
        
        # Store old values for history
        old_values = {
            'occupancy_state': self.occupancy_state,
            'housekeeping_state': self.housekeeping_state,
            'maintenance_required': self.maintenance_required,
        }
        
        self.write({
            'occupancy_state': 'reserved',
            'status_change_reason': f"Reserved: {guest_name}. {notes}",
            'last_status_change': fields.Datetime.now()
        })
        
        # Create status history record
        new_values = {
            'occupancy_state': 'reserved',
            'housekeeping_state': self.housekeeping_state,
            'maintenance_required': self.maintenance_required,
        }
        
        self.env['hotel.room.status.history'].create_status_change(
            room_id=self.id,
            change_type='occupancy',
            old_values=old_values,
            new_values=new_values,
            change_reason=f"Reserved: {guest_name}. {notes}",
            change_method='action_reserve',
            change_notes=notes
        )

    def action_cancel_reservation(self, reason=''):
        """Cancel reservation: reserved -> available"""
        self.ensure_one()
        if self.occupancy_state != 'reserved':
            raise ValidationError(f"Room must be reserved to cancel. Current state: {self.occupancy_state}")
        
        # Store old values for history
        old_values = {
            'occupancy_state': self.occupancy_state,
            'housekeeping_state': self.housekeeping_state,
            'maintenance_required': self.maintenance_required,
        }
        
        self.write({
            'occupancy_state': 'available',
            'status_change_reason': f"Reservation cancelled: {reason}",
            'last_status_change': fields.Datetime.now()
        })
        
        # Create status history record
        new_values = {
            'occupancy_state': 'available',
            'housekeeping_state': self.housekeeping_state,
            'maintenance_required': self.maintenance_required,
        }
        
        self.env['hotel.room.status.history'].create_status_change(
            room_id=self.id,
            change_type='occupancy',
            old_values=old_values,
            new_values=new_values,
            change_reason=f"Reservation cancelled: {reason}",
            change_method='action_cancel_reservation',
            change_notes=reason
        )

    def action_housekeeping_clean(self, notes=''):
        """Housekeeping: dirty -> clean"""
        self.ensure_one()
        if self.housekeeping_state != 'dirty':
            raise ValidationError(f"Room must be dirty to clean. Current state: {self.housekeeping_state}")
        
        # Store old values for history
        old_values = {
            'occupancy_state': self.occupancy_state,
            'housekeeping_state': self.housekeeping_state,
            'maintenance_required': self.maintenance_required,
        }
        
        self.write({
            'housekeeping_state': 'clean',
            'status_change_reason': f"Cleaned: {notes}",
            'last_status_change': fields.Datetime.now()
        })
        
        # Create status history record
        new_values = {
            'occupancy_state': self.occupancy_state,
            'housekeeping_state': 'clean',
            'maintenance_required': self.maintenance_required,
        }
        
        self.env['hotel.room.status.history'].create_status_change(
            room_id=self.id,
            change_type='housekeeping',
            old_values=old_values,
            new_values=new_values,
            change_reason=f"Cleaned: {notes}",
            change_method='action_housekeeping_clean',
            change_notes=notes
        )

    def action_housekeeping_inspect(self, notes=''):
        """Housekeeping: clean -> inspected"""
        self.ensure_one()
        if self.housekeeping_state != 'clean':
            raise ValidationError(f"Room must be clean to inspect. Current state: {self.housekeeping_state}")
        
        # Store old values for history
        old_values = {
            'occupancy_state': self.occupancy_state,
            'housekeeping_state': self.housekeeping_state,
            'maintenance_required': self.maintenance_required,
        }
        
        self.write({
            'housekeeping_state': 'inspected',
            'status_change_reason': f"Inspected: {notes}",
            'last_status_change': fields.Datetime.now()
        })
        
        # Create status history record
        new_values = {
            'occupancy_state': self.occupancy_state,
            'housekeeping_state': 'inspected',
            'maintenance_required': self.maintenance_required,
        }
        
        self.env['hotel.room.status.history'].create_status_change(
            room_id=self.id,
            change_type='housekeeping',
            old_values=old_values,
            new_values=new_values,
            change_reason=f"Inspected: {notes}",
            change_method='action_housekeeping_inspect',
            change_notes=notes
        )

    def is_sellable(self) -> bool:
        """Check if room is sellable based on occupancy_state, housekeeping_state and blocking."""
        self.ensure_one()
        
        # Room must be available for occupancy
        if self.occupancy_state != 'available':
            return False
        
        # Room must not be out of service in housekeeping
        if self.housekeeping_state == 'out_of_service':
            return False
        
        # Honor housekeeping policy
        require_inspected = self.env['ir.config_parameter'].sudo().get_param(
            'modulio_hotelcore.require_inspected_to_sell', 'False'
        ) == 'True'
        if require_inspected and self.housekeeping_state != 'inspected':
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
        
        # Check room availability using new states
        occupancy_available = self.occupancy_state == 'available'
        housekeeping_ready = self.housekeeping_state == 'inspected'
        not_out_of_service = self.housekeeping_state != 'out_of_service'
        
        # Housekeeping policy via config: require inspected to sell
        require_inspected = self.env['ir.config_parameter'].sudo().get_param(
            'modulio_hotelcore.require_inspected_to_sell', 'False'
        ) == 'True'
        hk_ok = housekeeping_ready if require_inspected else True

        # Room is available if occupancy is available, not out of service, not blocked, and housekeeping policy passes
        available = occupancy_available and not_out_of_service and blocking['available'] and hk_ok
        
        return {
            'room_id': self.id,
            'room_number': self.room_number,
            'room_type_id': self.room_type_id.id,
            'room_type_name': self.room_type_id.name,
            'occupancy_state': self.occupancy_state,
            'housekeeping_state': self.housekeeping_state,
            'occupancy_available': occupancy_available,
            'housekeeping_ready': housekeeping_ready,
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
            'occupancy_state': self.occupancy_state,
            'housekeeping_state': self.housekeeping_state,
            'available': availability['available'],
            'blockings': availability['blockings'],
            'room_number': self.room_number,
            'floor': self.floor,
            'room_type': self.room_type_id.name,
        }

    def _get_calendar_color(self):
        """Get color for calendar display based on occupancy_state and housekeeping_state"""
        # If housekeeping is out of service, show red regardless of occupancy
        if self.housekeeping_state == 'out_of_service':
            return '#dc3545'  # Red
        
        # Otherwise use occupancy state color
        color_map = {
            'available': '#28a745',      # Green
            'reserved': '#17a2b8',       # Blue
            'occupied': '#ffc107',       # Yellow
        }
        return color_map.get(self.occupancy_state, '#6c757d')

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

    def action_calendar_drop(self, new_occupancy_state, start_date, end_date, reason=''):
        """Handle drag & drop in calendar view to change room occupancy state or create blocking"""
        self.ensure_one()
        
        if new_occupancy_state in ['available', 'reserved', 'occupied']:
            # Change room occupancy state
            self.set_occupancy_state(new_occupancy_state)
            if reason:
                self.write({
                    'status_change_reason': reason,
                    'last_status_change': fields.Datetime.now()
                })
        elif new_occupancy_state == 'out_of_service':
            # Set housekeeping state to out of service
            self.mark_out_of_service()
            if reason:
                self.write({
                    'status_change_reason': reason,
                    'last_status_change': fields.Datetime.now()
                })
        elif new_occupancy_state == 'blocked':
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
                    'occupancy_state': room.occupancy_state,
                    'housekeeping_state': room.housekeeping_state,
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
        
        # Use new simplified reservation method
        room.action_reserve(guest_name, notes)
        
        return {
            'success': True,
            'room_number': room.room_number,
            'room_type': room.room_type_id.name,
            'occupancy_state': room.occupancy_state,
            'housekeeping_state': room.housekeeping_state,
            'message': f"Room {room.room_number} has been reserved successfully"
        }

    _sql_constraints = [
        ('room_number_floor_unique', 'UNIQUE(room_number, floor)', 
         'Room number must be unique per floor!'),
    ]
