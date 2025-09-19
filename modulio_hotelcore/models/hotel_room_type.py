# -*- coding: utf-8 -*-

from odoo import models, fields, api


class HotelRoomType(models.Model):
    _name = 'hotel.room.type'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Hotel Room Type'
    _order = 'sequence, name'

    name = fields.Char(
        string='Room Type Name',
        required=True,
        tracking=True,
        help='Name of the room type (e.g., Standard, Deluxe, Suite)'
    )
    code = fields.Char(
        string='Code',
        required=True,
        tracking=True,
        help='Short code for the room type'
    )
    description = fields.Text(
        string='Description',
        help='Detailed description of the room type'
    )
    max_occupancy = fields.Integer(
        string='Max Occupancy',
        default=2,
        help='Maximum number of guests that can occupy this room type'
    )
    size_sqm = fields.Float(
        string='Size (sqm)',
        help='Room size in square meters'
    )
    base_price = fields.Monetary(
        string='Base Price',
        currency_field='currency_id',
        tracking=True,
        help='Base price for this room type'
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id,
        required=True,
        ondelete='restrict'
    )
    amenities = fields.Text(
        string='Amenities',
        help='List of amenities included in this room type'
    )
    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help='Order of room types in lists'
    )
    room_count = fields.Integer(
        string='Room Count',
        compute='_compute_room_count',
        store=True,
        help='Number of rooms of this type'
    )
    room_ids = fields.One2many(
        'hotel.room',
        'room_type_id',
        string='Rooms',
        help='Rooms of this type'
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True,
        index=True,
        ondelete='restrict'
    )

    @api.depends('room_ids')
    def _compute_room_count(self):
        for record in self:
            record.room_count = len(record.room_ids)

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to ensure code uniqueness"""
        for vals in vals_list:
            if 'code' in vals and vals['code']:
                vals['code'] = vals['code'].upper()
        return super().create(vals_list)

    def write(self, vals):
        """Override write to ensure code uniqueness"""
        if 'code' in vals and vals['code']:
            vals['code'] = vals['code'].upper()
        return super().write(vals)

    def action_view_rooms(self):
        """Action to view rooms of this room type"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Rooms - {self.name}',
            'res_model': 'hotel.room',
            'view_mode': 'list,kanban,form',
            'domain': [('room_type_id', '=', self.id)],
            'context': {'default_room_type_id': self.id},
        }

    @api.model
    def get_room_types_with_availability(self, start_date, end_date):
        """Get room types with availability count for booking integration"""
        room_types = self.search([])
        result = []
        
        for room_type in room_types:
            available_rooms = self.env['hotel.room'].get_available_rooms(
                start_date, end_date, room_type.id
            )
            
            result.append({
                'room_type_id': room_type.id,
                'name': room_type.name,
                'code': room_type.code,
                'max_occupancy': room_type.max_occupancy,
                'base_price': room_type.base_price,
                'currency_id': room_type.currency_id.id,
                'available_count': len(available_rooms),
                'total_rooms': room_type.room_count,
                'available_rooms': available_rooms,
            })
        
        return result

    @api.model
    def get_room_type_pricing(self, room_type_id, start_date, end_date):
        """Get room type pricing for booking integration"""
        room_type = self.browse(room_type_id)
        if not room_type.exists():
            return None
        
        # Calculate total nights
        start = fields.Date.from_string(start_date)
        end = fields.Date.from_string(end_date)
        nights = (end - start).days
        
        return {
            'room_type_id': room_type.id,
            'name': room_type.name,
            'code': room_type.code,
            'base_price': room_type.base_price,
            'currency_id': room_type.currency_id.id,
            'nights': nights,
            'total_price': room_type.base_price * nights,
            'max_occupancy': room_type.max_occupancy,
            'amenities': room_type.amenities,
        }

    @api.model
    def get_room_type_availability_summary(self, start_date, end_date):
        """Get availability summary for all room types (integration point)"""
        room_types = self.search([])
        summary = {
            'total_room_types': len(room_types),
            'total_rooms': sum(rt.room_count for rt in room_types),
            'available_rooms': 0,
            'room_types': []
        }
        
        for room_type in room_types:
            available_rooms = self.env['hotel.room'].get_available_rooms(
                start_date, end_date, room_type.id
            )
            
            room_type_data = {
                'room_type_id': room_type.id,
                'name': room_type.name,
                'code': room_type.code,
                'total_rooms': room_type.room_count,
                'available_rooms': len(available_rooms),
                'availability_rate': (len(available_rooms) / room_type.room_count * 100) if room_type.room_count > 0 else 0,
            }
            
            summary['room_types'].append(room_type_data)
            summary['available_rooms'] += len(available_rooms)
        
        return summary

    _sql_constraints = [
        ('code_unique', 'UNIQUE(code)', 'Room type code must be unique!'),
        ('name_unique', 'UNIQUE(name)', 'Room type name must be unique!'),
    ]
