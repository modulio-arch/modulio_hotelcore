# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class HotelRoomAmenity(models.Model):
    _name = 'hotel.room.amenity'
    _description = 'Hotel Room Amenity Assignment'
    _order = 'room_id, amenity_id'
    _rec_name = 'display_name'

    # Basic Information
    room_id = fields.Many2one(
        'hotel.room',
        string='Room',
        required=True,
        index=True,
        ondelete='cascade',
        help='Room where the amenity is assigned'
    )
    amenity_id = fields.Many2one(
        'hotel.amenity',
        string='Amenity',
        required=True,
        index=True,
        ondelete='cascade',
        help='Amenity assigned to the room'
    )
    
    # Room Information (Related fields for easy access)
    room_number = fields.Char(
        related='room_id.room_number',
        string='Room Number',
        store=True,
        help='Room number for easy reference'
    )
    floor_id = fields.Many2one(
        related='room_id.floor_id',
        string='Floor',
        store=True,
        help='Floor where the room is located'
    )
    room_type_id = fields.Many2one(
        related='room_id.room_type_id',
        string='Room Type',
        store=True,
        help='Type of the room'
    )
    
    # Amenity Information (Related fields for easy access)
    amenity_name = fields.Char(
        related='amenity_id.name',
        string='Amenity Name',
        store=True,
        help='Name of the amenity'
    )
    amenity_code = fields.Char(
        related='amenity_id.code',
        string='Amenity Code',
        store=True,
        help='Code of the amenity'
    )
    amenity_category_id = fields.Many2one(
        related='amenity_id.category_id',
        string='Amenity Category',
        store=True,
        help='Category of the amenity'
    )
    amenity_type = fields.Selection(
        related='amenity_id.amenity_type',
        string='Amenity Type',
        store=True,
        help='Type of the amenity (free, paid, conditional)'
    )
    amenity_price = fields.Monetary(
        related='amenity_id.price',
        string='Amenity Price',
        store=True,
        help='Price of the amenity'
    )
    currency_id = fields.Many2one(
        related='amenity_id.currency_id',
        string='Currency',
        store=True,
        help='Currency for pricing'
    )

    # Assignment Details
    assignment_type = fields.Selection([
        ('included', 'Included'),
        ('optional', 'Optional'),
        ('upgrade', 'Upgrade'),
        ('conditional', 'Conditional'),
    ], string='Assignment Type', default='included', required=True,
       help='How the amenity is assigned to the room')
    
    is_available = fields.Boolean(
        string='Available',
        default=True,
        help='Whether this amenity is available in this room'
    )
    is_default = fields.Boolean(
        string='Default',
        default=False,
        help='Whether this is a default amenity for this room type'
    )
    
    # Pricing and Billing
    room_specific_price = fields.Monetary(
        string='Room Specific Price',
        currency_field='currency_id',
        help='Override price for this specific room (if different from amenity price)'
    )
    final_price = fields.Monetary(
        string='Final Price',
        currency_field='currency_id',
        compute='_compute_final_price',
        store=True,
        help='Final price for this amenity in this room'
    )
    
    # Usage and Analytics
    usage_count = fields.Integer(
        string='Usage Count',
        default=0,
        help='Number of times this amenity has been used in this room'
    )
    revenue_generated = fields.Monetary(
        string='Revenue Generated',
        currency_field='currency_id',
        compute='_compute_revenue_generated',
        store=True,
        help='Revenue generated from this amenity in this room'
    )
    last_used_date = fields.Datetime(
        string='Last Used Date',
        help='Date when this amenity was last used in this room'
    )
    
    # Notes and Special Instructions
    notes = fields.Text(
        string='Notes',
        help='Special notes or instructions for this amenity in this room'
    )
    special_instructions = fields.Text(
        string='Special Instructions',
        help='Special instructions for staff regarding this amenity'
    )
    
    # System Fields
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        related='room_id.company_id',
        store=True,
        help='Company of the room'
    )
    active = fields.Boolean(
        string='Active',
        default=True,
        help='Whether this assignment is active'
    )

    # Computed Fields
    display_name = fields.Char(
        string='Display Name',
        compute='_compute_display_name',
        store=True,
        help='Display name for the assignment'
    )

    @api.depends('room_number', 'amenity_name', 'assignment_type')
    def _compute_display_name(self):
        """Compute display name for the assignment"""
        for record in self:
            if record.room_number and record.amenity_name:
                record.display_name = f"Room {record.room_number} - {record.amenity_name} ({record.assignment_type})"
            else:
                record.display_name = f"Room Amenity Assignment - {record.id}"

    @api.depends('room_specific_price', 'amenity_price', 'amenity_type')
    def _compute_final_price(self):
        """Compute final price for this amenity in this room"""
        for record in self:
            if record.amenity_type == 'paid':
                if record.room_specific_price:
                    record.final_price = record.room_specific_price
                else:
                    record.final_price = record.amenity_price or 0.0
            else:
                record.final_price = 0.0

    @api.depends('usage_count', 'final_price', 'amenity_type')
    def _compute_revenue_generated(self):
        """Compute revenue generated from this amenity in this room"""
        for record in self:
            if record.amenity_type == 'paid' and record.final_price and record.usage_count:
                record.revenue_generated = record.usage_count * record.final_price
            else:
                record.revenue_generated = 0.0

    @api.constrains('room_id', 'amenity_id')
    def _check_unique_assignment(self):
        """Ensure unique assignment per room-amenity combination"""
        for record in self:
            if self.search_count([
                ('room_id', '=', record.room_id.id),
                ('amenity_id', '=', record.amenity_id.id),
                ('id', '!=', record.id)
            ]) > 0:
                raise ValidationError(_("This amenity is already assigned to this room!"))

    @api.constrains('room_specific_price', 'amenity_type')
    def _check_price_consistency(self):
        """Validate price consistency with amenity type"""
        for record in self:
            if record.amenity_type == 'free' and record.room_specific_price:
                raise ValidationError(_("Free amenities cannot have a room-specific price!"))
            if record.amenity_type == 'paid' and record.room_specific_price and record.room_specific_price < 0:
                raise ValidationError(_("Room-specific price cannot be negative!"))

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to set default values"""
        for vals in vals_list:
            # Set default assignment type based on amenity type
            if 'assignment_type' not in vals:
                amenity_id = vals.get('amenity_id')
                if amenity_id:
                    amenity = self.env['hotel.amenity'].browse(amenity_id)
                    if amenity.amenity_type == 'free':
                        vals['assignment_type'] = 'included'
                    elif amenity.amenity_type == 'paid':
                        vals['assignment_type'] = 'optional'
        return super().create(vals_list)

    def action_view_room(self):
        """Action to view the room"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Room - {self.room_number}',
            'res_model': 'hotel.room',
            'view_mode': 'form',
            'res_id': self.room_id.id,
            'target': 'current',
        }

    def action_view_amenity(self):
        """Action to view the amenity"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Amenity - {self.amenity_name}',
            'res_model': 'hotel.amenity',
            'view_mode': 'form',
            'res_id': self.amenity_id.id,
            'target': 'current',
        }

    def action_mark_used(self):
        """Mark amenity as used in this room"""
        self.ensure_one()
        self.write({
            'usage_count': self.usage_count + 1,
            'last_used_date': fields.Datetime.now(),
        })

    def action_mark_unavailable(self):
        """Mark amenity as unavailable in this room"""
        self.ensure_one()
        self.write({'is_available': False})

    def action_mark_available(self):
        """Mark amenity as available in this room"""
        self.ensure_one()
        self.write({'is_available': True})

    @api.model
    def get_room_amenities(self, room_id, available_only=True):
        """Get amenities for a specific room"""
        domain = [('room_id', '=', room_id)]
        if available_only:
            domain.append(('is_available', '=', True))
        
        return self.search(domain)

    @api.model
    def get_amenity_rooms(self, amenity_id, available_only=True):
        """Get rooms that have a specific amenity"""
        domain = [('amenity_id', '=', amenity_id)]
        if available_only:
            domain.append(('is_available', '=', True))
        
        return self.search(domain)

    @api.model
    def get_room_amenities_summary(self, room_id):
        """Get summary of amenities for a room"""
        assignments = self.search([('room_id', '=', room_id)])
        
        summary = {
            'total_amenities': len(assignments),
            'available_amenities': len(assignments.filtered('is_available')),
            'free_amenities': len(assignments.filtered(lambda a: a.amenity_type == 'free')),
            'paid_amenities': len(assignments.filtered(lambda a: a.amenity_type == 'paid')),
            'total_revenue': sum(assignment.revenue_generated for assignment in assignments),
            'total_usage': sum(assignment.usage_count for assignment in assignments),
            'amenities': assignments,
        }
        
        return summary

    @api.model
    def get_amenity_usage_summary(self, amenity_id):
        """Get summary of usage for an amenity across all rooms"""
        assignments = self.search([('amenity_id', '=', amenity_id)])
        
        summary = {
            'total_rooms': len(assignments),
            'available_rooms': len(assignments.filtered('is_available')),
            'total_usage': sum(assignment.usage_count for assignment in assignments),
            'total_revenue': sum(assignment.revenue_generated for assignment in assignments),
            'average_usage_per_room': sum(assignment.usage_count for assignment in assignments) / len(assignments) if assignments else 0,
            'assignments': assignments,
        }
        
        return summary

    _sql_constraints = [
        ('room_amenity_unique', 'UNIQUE(room_id, amenity_id)', 
         'Amenity can only be assigned once per room!'),
    ]
