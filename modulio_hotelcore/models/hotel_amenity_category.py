# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class HotelAmenityCategory(models.Model):
    _name = 'hotel.amenity.category'
    _description = 'Hotel Amenity Category'
    _order = 'sequence, name'
    _rec_name = 'name'

    # Basic Information
    name = fields.Char(
        string='Category Name',
        required=True,
        index=True,
        help='Name of the amenity category (e.g., Technology, Recreation, Dining)'
    )
    code = fields.Char(
        string='Category Code',
        required=True,
        index=True,
        help='Unique code for the category (e.g., TECH, REC, DINE)'
    )
    description = fields.Text(
        string='Description',
        help='Description of the amenity category'
    )
    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help='Order of categories in lists'
    )

    # Visual and Display
    icon = fields.Char(
        string='Icon',
        help='Icon class for display (e.g., fa-wifi, fa-swimming-pool)'
    )
    color = fields.Char(
        string='Color',
        default='#007bff',
        help='Color code for display (e.g., #007bff)'
    )

    # Related Amenities
    amenity_ids = fields.One2many(
        'hotel.amenity',
        'category_id',
        string='Amenities',
        help='Amenities in this category'
    )
    amenity_count = fields.Integer(
        string='Amenity Count',
        compute='_compute_amenity_count',
        store=True,
        help='Number of amenities in this category'
    )
    active_amenity_count = fields.Integer(
        string='Active Amenity Count',
        compute='_compute_amenity_count',
        store=True,
        help='Number of active amenities in this category'
    )

    # Analytics
    total_usage = fields.Integer(
        string='Total Usage',
        compute='_compute_analytics',
        store=True,
        help='Total usage count for all amenities in this category'
    )
    total_revenue = fields.Monetary(
        string='Total Revenue',
        currency_field='currency_id',
        compute='_compute_analytics',
        store=True,
        help='Total revenue from all amenities in this category'
    )
    average_popularity = fields.Float(
        string='Average Popularity',
        compute='_compute_analytics',
        store=True,
        help='Average popularity score for amenities in this category'
    )

    # System Fields
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id,
        help='Currency for revenue calculations'
    )
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
        help='Whether this category is active'
    )

    # Computed Fields
    display_name = fields.Char(
        string='Display Name',
        compute='_compute_display_name',
        store=True,
        help='Display name for the category'
    )

    @api.depends('name', 'code')
    def _compute_display_name(self):
        """Compute display name for the category"""
        for record in self:
            if record.name and record.code:
                record.display_name = f"{record.name} ({record.code})"
            else:
                record.display_name = record.name or record.code

    @api.depends('amenity_ids', 'amenity_ids.active', 'amenity_ids.usage_count', 
                 'amenity_ids.revenue_generated', 'amenity_ids.popularity_score')
    def _compute_amenity_count(self):
        """Compute amenity counts"""
        for record in self:
            record.amenity_count = len(record.amenity_ids)
            record.active_amenity_count = len(record.amenity_ids.filtered('active'))

    @api.depends('amenity_ids', 'amenity_ids.usage_count', 'amenity_ids.revenue_generated', 
                 'amenity_ids.popularity_score')
    def _compute_analytics(self):
        """Compute analytics for the category"""
        for record in self:
            active_amenities = record.amenity_ids.filtered('active')
            
            record.total_usage = sum(amenity.usage_count for amenity in active_amenities)
            record.total_revenue = sum(amenity.revenue_generated for amenity in active_amenities)
            
            if active_amenities:
                record.average_popularity = sum(amenity.popularity_score for amenity in active_amenities) / len(active_amenities)
            else:
                record.average_popularity = 0.0

    @api.constrains('code')
    def _check_code_unique(self):
        """Ensure category code is unique per company"""
        for record in self:
            if self.search_count([
                ('code', '=', record.code),
                ('company_id', '=', record.company_id.id),
                ('id', '!=', record.id)
            ]) > 0:
                raise ValidationError(_("Category code must be unique per company!"))

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

    def action_view_amenities(self):
        """Action to view amenities in this category"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Amenities - {self.name}',
            'res_model': 'hotel.amenity',
            'view_mode': 'list,kanban,form',
            'domain': [('category_id', '=', self.id)],
            'context': {'default_category_id': self.id},
        }

    def action_view_analytics(self):
        """Action to view analytics for this category"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Analytics - {self.name}',
            'res_model': 'hotel.amenity',
            'view_mode': 'list,kanban,form',
            'domain': [('category_id', '=', self.id), ('active', '=', True)],
            'context': {
                'default_category_id': self.id,
                'group_by': ['amenity_type'],
            },
        }

    @api.model
    def get_category_summary(self):
        """Get summary of all categories"""
        categories = self.search([('active', '=', True)])
        
        summary = {
            'total_categories': len(categories),
            'total_amenities': sum(cat.amenity_count for cat in categories),
            'total_active_amenities': sum(cat.active_amenity_count for cat in categories),
            'total_usage': sum(cat.total_usage for cat in categories),
            'total_revenue': sum(cat.total_revenue for cat in categories),
            'categories': []
        }
        
        for category in categories:
            summary['categories'].append({
                'id': category.id,
                'name': category.name,
                'code': category.code,
                'amenity_count': category.amenity_count,
                'active_amenity_count': category.active_amenity_count,
                'total_usage': category.total_usage,
                'total_revenue': category.total_revenue,
                'average_popularity': category.average_popularity,
            })
        
        return summary

    _sql_constraints = [
        ('code_company_unique', 'UNIQUE(code, company_id)', 
         'Category code must be unique per company!'),
    ]
