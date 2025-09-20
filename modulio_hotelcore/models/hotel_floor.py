# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class HotelFloor(models.Model):
    _name = 'hotel.floor'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Hotel Floor'
    _order = 'sequence, floor_number'

    name = fields.Char(
        string='Floor Name',
        required=True,
        tracking=True,
        help='Name of the floor (e.g., Ground Floor, First Floor, Second Floor)'
    )
    floor_number = fields.Integer(
        string='Floor Number',
        required=True,
        index=True,
        tracking=True,
        help='Numeric floor number (0 for ground floor, 1 for first floor, etc.)'
    )
    description = fields.Text(
        string='Description',
        help='Additional description for the floor'
    )
    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help='Order of floors in lists'
    )
    
    # Room management
    room_count = fields.Integer(
        string='Room Count',
        compute='_compute_room_count',
        store=True,
        help='Number of rooms on this floor'
    )
    room_ids = fields.One2many(
        'hotel.room',
        'floor_id',
        string='Rooms',
        help='Rooms on this floor'
    )
    
    # Room type distribution
    room_type_count = fields.Integer(
        string='Room Type Count',
        compute='_compute_room_type_count',
        store=True,
        help='Number of different room types on this floor'
    )
    
    # Status and availability
    total_rooms = fields.Integer(
        string='Total Rooms',
        compute='_compute_room_stats',
        store=True,
        help='Total number of rooms on this floor'
    )
    available_rooms = fields.Integer(
        string='Available Rooms',
        compute='_compute_room_stats',
        store=True,
        help='Number of available rooms on this floor'
    )
    occupied_rooms = fields.Integer(
        string='Occupied Rooms',
        compute='_compute_room_stats',
        store=True,
        help='Number of occupied rooms on this floor'
    )
    reserved_rooms = fields.Integer(
        string='Reserved Rooms',
        compute='_compute_room_stats',
        store=True,
        help='Number of reserved rooms on this floor'
    )
    
    # Maintenance and service
    maintenance_required = fields.Boolean(
        string='Maintenance Required',
        compute='_compute_maintenance_status',
        store=True,
        help='Whether any room on this floor requires maintenance'
    )
    maintenance_notes = fields.Text(
        string='Maintenance Notes',
        help='Notes about floor maintenance requirements'
    )
    
    # System fields
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True,
        index=True,
        ondelete='restrict'
    )
    active = fields.Boolean(
        string='Active',
        default=True,
        help='Whether this floor is active'
    )

    @api.depends('room_ids')
    def _compute_room_count(self):
        for record in self:
            record.room_count = len(record.room_ids)

    @api.depends('room_ids', 'room_ids.room_type_id')
    def _compute_room_type_count(self):
        for record in self:
            room_types = record.room_ids.mapped('room_type_id')
            record.room_type_count = len(room_types)

    @api.depends('room_ids', 'room_ids.occupancy_state')
    def _compute_room_stats(self):
        for record in self:
            rooms = record.room_ids
            record.total_rooms = len(rooms)
            record.available_rooms = len(rooms.filtered(lambda r: r.occupancy_state == 'available'))
            record.occupied_rooms = len(rooms.filtered(lambda r: r.occupancy_state == 'occupied'))
            record.reserved_rooms = len(rooms.filtered(lambda r: r.occupancy_state == 'reserved'))

    @api.depends('room_ids', 'room_ids.maintenance_required')
    def _compute_maintenance_status(self):
        for record in self:
            record.maintenance_required = any(room.maintenance_required for room in record.room_ids)

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to ensure floor number uniqueness"""
        for vals in vals_list:
            if 'floor_number' in vals:
                self._validate_floor_number(vals['floor_number'])
        return super().create(vals_list)

    def write(self, vals):
        """Override write to validate floor number changes"""
        if 'floor_number' in vals:
            for record in self:
                self._validate_floor_number(vals['floor_number'], exclude_id=record.id)
        return super().write(vals)

    def _validate_floor_number(self, floor_number, exclude_id=None):
        """Validate that floor number is unique"""
        if floor_number is not None:
            domain = [('floor_number', '=', floor_number)]
            if exclude_id:
                domain.append(('id', '!=', exclude_id))
            
            existing = self.search(domain)
            if existing:
                raise ValidationError(
                    f"Floor number {floor_number} already exists. "
                    f"Please choose a different floor number."
                )

    def action_view_rooms(self):
        """Action to view rooms on this floor"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Rooms - Floor {self.name}',
            'res_model': 'hotel.room',
            'view_mode': 'list,kanban,form',
            'domain': [('floor_id', '=', self.id)],
            'context': {'default_floor_id': self.id},
        }

    def action_view_room_types(self):
        """Action to view room types on this floor"""
        self.ensure_one()
        room_types = self.room_ids.mapped('room_type_id')
        return {
            'type': 'ir.actions.act_window',
            'name': f'Room Types - Floor {self.name}',
            'res_model': 'hotel.room.type',
            'view_mode': 'list,kanban,form',
            'domain': [('id', 'in', room_types.ids)],
        }

    def get_floor_availability_summary(self, start_date=None, end_date=None):
        """Get availability summary for this floor"""
        self.ensure_one()
        
        # If no dates provided, use today
        if not start_date:
            start_date = fields.Date.today()
        if not end_date:
            end_date = start_date
        
        rooms = self.room_ids
        summary = {
            'floor_id': self.id,
            'floor_name': self.name,
            'floor_number': self.floor_number,
            'total_rooms': len(rooms),
            'available_rooms': 0,
            'occupied_rooms': 0,
            'reserved_rooms': 0,
            'out_of_service_rooms': 0,
            'maintenance_required_rooms': 0,
            'availability_rate': 0,
            'rooms': []
        }
        
        for room in rooms:
            availability = room.get_availability(start_date, end_date)
            room_summary = {
                'room_id': room.id,
                'room_number': room.room_number,
                'room_type': room.room_type_id.name,
                'occupancy_state': room.occupancy_state,
                'housekeeping_state': room.housekeeping_state,
                'available': availability['available'],
                'maintenance_required': room.maintenance_required,
            }
            
            summary['rooms'].append(room_summary)
            
            # Count by status
            if room.occupancy_state == 'available':
                summary['available_rooms'] += 1
            elif room.occupancy_state == 'occupied':
                summary['occupied_rooms'] += 1
            elif room.occupancy_state == 'reserved':
                summary['reserved_rooms'] += 1
            
            if room.housekeeping_state == 'out_of_service':
                summary['out_of_service_rooms'] += 1
            
            if room.maintenance_required:
                summary['maintenance_required_rooms'] += 1
        
        # Calculate availability rate
        if summary['total_rooms'] > 0:
            summary['availability_rate'] = (summary['available_rooms'] / summary['total_rooms']) * 100
        
        return summary

    _sql_constraints = [
        ('floor_number_unique', 'UNIQUE(floor_number)', 
         'Floor number must be unique!'),
        ('floor_number_positive', 'CHECK (floor_number >= 0)', 
         'Floor number must be positive or zero!'),
    ]
