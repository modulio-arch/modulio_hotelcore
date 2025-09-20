# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class HotelAmenity(models.Model):
    _name = 'hotel.amenity'
    _description = 'Hotel Amenity'
    _order = 'sequence, name'
    _rec_name = 'name'

    # Basic Information
    name = fields.Char(
        string='Amenity Name',
        required=True,
        index=True,
        help='Name of the amenity (e.g., WiFi, Swimming Pool, Gym)'
    )
    code = fields.Char(
        string='Amenity Code',
        required=True,
        index=True,
        help='Unique code for the amenity (e.g., WIFI, POOL, GYM)'
    )
    description = fields.Text(
        string='Description',
        help='Detailed description of the amenity'
    )
    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help='Order of amenities in lists'
    )

    # Category and Classification
    category_id = fields.Many2one(
        'hotel.amenity.category',
        string='Category',
        required=True,
        index=True,
        ondelete='restrict',
        help='Category of the amenity'
    )
    amenity_type = fields.Selection([
        ('free', 'Free'),
        ('paid', 'Paid'),
        ('conditional', 'Conditional'),
    ], string='Amenity Type', default='free', required=True,
       help='Type of amenity - free, paid, or conditional')

    # Pricing Information
    price = fields.Monetary(
        string='Price',
        currency_field='currency_id',
        help='Price for paid amenities'
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id,
        help='Currency for pricing'
    )
    price_type = fields.Selection([
        ('per_night', 'Per Night'),
        ('per_stay', 'Per Stay'),
        ('per_use', 'Per Use'),
        ('hourly', 'Hourly'),
        ('daily', 'Daily'),
    ], string='Price Type', default='per_night',
       help='How the price is calculated')

    # Availability and Access
    is_available = fields.Boolean(
        string='Available',
        default=True,
        help='Whether this amenity is currently available'
    )
    access_type = fields.Selection([
        ('public', 'Public'),
        ('guest_only', 'Guest Only'),
        ('room_only', 'Room Only'),
        ('restricted', 'Restricted'),
    ], string='Access Type', default='public',
       help='Who can access this amenity')
    requires_booking = fields.Boolean(
        string='Requires Booking',
        default=False,
        help='Whether this amenity requires advance booking'
    )
    max_capacity = fields.Integer(
        string='Maximum Capacity',
        help='Maximum number of people who can use this amenity'
    )
    operating_hours = fields.Text(
        string='Operating Hours',
        help='Operating hours for this amenity (e.g., 24/7, 6:00-22:00)'
    )

    # Location and Physical Details
    location = fields.Char(
        string='Location',
        help='Physical location of the amenity (e.g., Lobby, 3rd Floor, Pool Area)'
    )
    floor_id = fields.Many2one(
        'hotel.floor',
        string='Floor',
        help='Floor where the amenity is located'
    )
    room_number = fields.Char(
        string='Room Number',
        help='Specific room number if amenity is room-specific'
    )

    # Maintenance and Status
    maintenance_required = fields.Boolean(
        string='Maintenance Required',
        default=False,
        help='Whether this amenity requires maintenance'
    )
    last_maintenance_date = fields.Date(
        string='Last Maintenance Date',
        help='Date of last maintenance'
    )
    next_maintenance_date = fields.Date(
        string='Next Maintenance Date',
        help='Scheduled date for next maintenance'
    )
    maintenance_notes = fields.Text(
        string='Maintenance Notes',
        help='Notes about maintenance requirements'
    )

    # Usage and Analytics
    usage_count = fields.Integer(
        string='Usage Count',
        default=0,
        help='Number of times this amenity has been used'
    )
    revenue_generated = fields.Monetary(
        string='Revenue Generated',
        currency_field='currency_id',
        compute='_compute_revenue_generated',
        store=True,
        help='Total revenue generated from this amenity'
    )
    popularity_score = fields.Float(
        string='Popularity Score',
        default=0.0,
        help='Popularity score based on usage and ratings'
    )

    # System Fields
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
        help='Whether this amenity is active'
    )

    # Computed Fields
    display_name = fields.Char(
        string='Display Name',
        compute='_compute_display_name',
        store=True,
        help='Display name for the amenity'
    )
    full_location = fields.Char(
        string='Full Location',
        compute='_compute_full_location',
        store=True,
        help='Complete location information'
    )

    @api.depends('name', 'code')
    def _compute_display_name(self):
        """Compute display name for the amenity"""
        for record in self:
            if record.name and record.code:
                record.display_name = f"{record.name} ({record.code})"
            else:
                record.display_name = record.name or record.code

    @api.depends('location', 'floor_id', 'room_number')
    def _compute_full_location(self):
        """Compute full location information"""
        for record in self:
            location_parts = []
            if record.location:
                location_parts.append(record.location)
            if record.floor_id:
                location_parts.append(f"Floor {record.floor_id.floor_number}")
            if record.room_number:
                location_parts.append(f"Room {record.room_number}")
            
            record.full_location = ', '.join(location_parts) if location_parts else ''

    @api.depends('usage_count', 'price', 'price_type')
    def _compute_revenue_generated(self):
        """Compute total revenue generated from this amenity"""
        for record in self:
            if record.amenity_type == 'paid' and record.price and record.usage_count:
                if record.price_type == 'per_night':
                    # Assume average 2 nights per usage
                    record.revenue_generated = record.usage_count * record.price * 2
                elif record.price_type == 'per_stay':
                    record.revenue_generated = record.usage_count * record.price
                elif record.price_type == 'per_use':
                    record.revenue_generated = record.usage_count * record.price
                elif record.price_type == 'hourly':
                    # Assume average 2 hours per usage
                    record.revenue_generated = record.usage_count * record.price * 2
                elif record.price_type == 'daily':
                    record.revenue_generated = record.usage_count * record.price
                else:
                    record.revenue_generated = record.usage_count * record.price
            else:
                record.revenue_generated = 0.0

    @api.constrains('code')
    def _check_code_unique(self):
        """Ensure amenity code is unique per company"""
        for record in self:
            if self.search_count([
                ('code', '=', record.code),
                ('company_id', '=', record.company_id.id),
                ('id', '!=', record.id)
            ]) > 0:
                raise ValidationError(_("Amenity code must be unique per company!"))

    @api.constrains('price', 'amenity_type')
    def _check_price_consistency(self):
        """Validate price consistency with amenity type"""
        for record in self:
            if record.amenity_type == 'paid' and not record.price:
                raise ValidationError(_("Paid amenities must have a price!"))
            if record.amenity_type == 'free' and record.price:
                raise ValidationError(_("Free amenities cannot have a price!"))

    @api.constrains('max_capacity')
    def _check_max_capacity(self):
        """Validate maximum capacity"""
        for record in self:
            if record.max_capacity and record.max_capacity < 1:
                raise ValidationError(_("Maximum capacity must be at least 1!"))

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to set default values"""
        for vals in vals_list:
            if 'code' not in vals or not vals['code']:
                # Auto-generate code from name
                name = vals.get('name', '')
                if name:
                    vals['code'] = name.upper().replace(' ', '_').replace('-', '_')
        return super().create(vals_list)

    def action_view_usage_history(self):
        """Action to view usage history for this amenity"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Usage History - {self.name}',
            'res_model': 'hotel.amenity.usage',
            'view_mode': 'list,kanban,form',
            'domain': [('amenity_id', '=', self.id)],
            'context': {'default_amenity_id': self.id},
        }

    def action_schedule_maintenance(self):
        """Action to schedule maintenance for this amenity"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Schedule Maintenance - {self.name}',
            'res_model': 'hotel.maintenance.request',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_amenity_id': self.id,
                'default_maintenance_type': 'amenity',
            },
        }

    def action_mark_unavailable(self):
        """Mark amenity as unavailable"""
        self.ensure_one()
        self.write({
            'is_available': False,
            'maintenance_required': True,
        })

    def action_mark_available(self):
        """Mark amenity as available"""
        self.ensure_one()
        self.write({
            'is_available': True,
            'maintenance_required': False,
        })

    @api.model
    def get_amenities_by_category(self, category_id=None):
        """Get amenities grouped by category"""
        domain = [('active', '=', True)]
        if category_id:
            domain.append(('category_id', '=', category_id))
        
        amenities = self.search(domain)
        categories = {}
        
        for amenity in amenities:
            category = amenity.category_id
            if category.id not in categories:
                categories[category.id] = {
                    'category': category,
                    'amenities': []
                }
            categories[category.id]['amenities'].append(amenity)
        
        return categories

    @api.model
    def get_available_amenities(self, access_type=None):
        """Get available amenities filtered by access type"""
        domain = [
            ('active', '=', True),
            ('is_available', '=', True)
        ]
        if access_type:
            domain.append(('access_type', '=', access_type))
        
        return self.search(domain)

    @api.model
    def get_amenity_revenue_summary(self, start_date=None, end_date=None):
        """Get revenue summary for amenities"""
        domain = [('active', '=', True), ('amenity_type', '=', 'paid')]
        amenities = self.search(domain)
        
        total_revenue = sum(amenity.revenue_generated for amenity in amenities)
        total_usage = sum(amenity.usage_count for amenity in amenities)
        
        return {
            'total_amenities': len(amenities),
            'total_revenue': total_revenue,
            'total_usage': total_usage,
            'average_revenue_per_amenity': total_revenue / len(amenities) if amenities else 0,
            'amenities': amenities,
        }

    _sql_constraints = [
        ('code_company_unique', 'UNIQUE(code, company_id)', 
         'Amenity code must be unique per company!'),
    ]
