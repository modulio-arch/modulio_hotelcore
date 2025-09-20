# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class HotelMaintenanceCategory(models.Model):
    _name = 'hotel.maintenance.category'
    _description = 'Hotel Maintenance Category'
    _order = 'sequence, name'
    _rec_name = 'name'

    # Basic Information
    name = fields.Char(
        string='Category Name',
        required=True,
        index=True,
        help='Name of the maintenance category (e.g., Electrical, Plumbing, HVAC)'
    )
    code = fields.Char(
        string='Category Code',
        required=True,
        index=True,
        help='Unique code for the category (e.g., ELEC, PLUMB, HVAC)'
    )
    description = fields.Text(
        string='Description',
        help='Description of the maintenance category'
    )
    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help='Order of categories in lists'
    )

    # Category Details
    maintenance_type = fields.Selection([
        ('room', 'Room Maintenance'),
        ('amenity', 'Amenity Maintenance'),
        ('floor', 'Floor Maintenance'),
        ('general', 'General Maintenance'),
        ('emergency', 'Emergency Maintenance'),
    ], string='Maintenance Type', required=True, default='general',
       help='Type of maintenance this category applies to')

    # Response and Escalation
    response_time_hours = fields.Integer(
        string='Response Time (hours)',
        default=4,
        help='Expected response time in hours'
    )
    escalation_time_hours = fields.Integer(
        string='Escalation Time (hours)',
        default=24,
        help='Time before escalation in hours'
    )
    default_priority = fields.Selection([
        ('1', 'Very Low'),
        ('2', 'Low'),
        ('3', 'Medium'),
        ('4', 'High'),
        ('5', 'Critical'),
    ], string='Default Priority', default='3',
       help='Default priority for requests in this category')

    # Cost and Resources
    estimated_cost_range_min = fields.Monetary(
        string='Min Estimated Cost',
        currency_field='currency_id',
        help='Minimum estimated cost for this category'
    )
    estimated_cost_range_max = fields.Monetary(
        string='Max Estimated Cost',
        currency_field='currency_id',
        help='Maximum estimated cost for this category'
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id,
        help='Currency for cost calculations'
    )

    # Skills and Requirements
    required_skills = fields.Text(
        string='Required Skills',
        help='Skills required for this category of maintenance'
    )
    required_certifications = fields.Text(
        string='Required Certifications',
        help='Certifications required for this category'
    )
    safety_requirements = fields.Text(
        string='Safety Requirements',
        help='Safety requirements for this category'
    )

    # Related Requests
    request_ids = fields.One2many(
        'hotel.maintenance.request',
        'category_id',
        string='Maintenance Requests',
        help='Maintenance requests in this category'
    )
    request_count = fields.Integer(
        string='Request Count',
        compute='_compute_request_count',
        store=True,
        help='Number of requests in this category'
    )
    active_request_count = fields.Integer(
        string='Active Request Count',
        compute='_compute_request_count',
        store=True,
        help='Number of active requests in this category'
    )

    # Analytics
    total_requests = fields.Integer(
        string='Total Requests',
        compute='_compute_analytics',
        store=True,
        help='Total number of requests in this category'
    )
    completed_requests = fields.Integer(
        string='Completed Requests',
        compute='_compute_analytics',
        store=True,
        help='Number of completed requests'
    )
    average_duration = fields.Float(
        string='Average Duration (hours)',
        compute='_compute_analytics',
        store=True,
        help='Average duration of completed requests'
    )
    average_cost = fields.Monetary(
        string='Average Cost',
        currency_field='currency_id',
        compute='_compute_analytics',
        store=True,
        help='Average cost of completed requests'
    )
    total_cost = fields.Monetary(
        string='Total Cost',
        currency_field='currency_id',
        compute='_compute_analytics',
        store=True,
        help='Total cost of all requests in this category'
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

    @api.depends('request_ids', 'request_ids.active')
    def _compute_request_count(self):
        """Compute request counts"""
        for record in self:
            record.request_count = len(record.request_ids)
            record.active_request_count = len(record.request_ids.filtered('active'))

    @api.depends('request_ids', 'request_ids.status', 'request_ids.actual_duration', 
                 'request_ids.actual_cost')
    def _compute_analytics(self):
        """Compute analytics for the category"""
        for record in self:
            all_requests = record.request_ids.filtered('active')
            completed_requests = all_requests.filtered(lambda r: r.status == 'completed')
            
            record.total_requests = len(all_requests)
            record.completed_requests = len(completed_requests)
            
            if completed_requests:
                record.average_duration = sum(completed_requests.mapped('actual_duration')) / len(completed_requests)
                record.average_cost = sum(completed_requests.mapped('actual_cost')) / len(completed_requests)
            else:
                record.average_duration = 0.0
                record.average_cost = 0.0
            
            record.total_cost = sum(all_requests.mapped('actual_cost'))

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

    @api.constrains('estimated_cost_range_min', 'estimated_cost_range_max')
    def _check_cost_range(self):
        """Validate cost range"""
        for record in self:
            if record.estimated_cost_range_min and record.estimated_cost_range_max:
                if record.estimated_cost_range_min > record.estimated_cost_range_max:
                    raise ValidationError(_("Minimum cost cannot be greater than maximum cost!"))

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

    def action_view_requests(self):
        """Action to view requests in this category"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Maintenance Requests - {self.name}',
            'res_model': 'hotel.maintenance.request',
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
            'res_model': 'hotel.maintenance.request',
            'view_mode': 'list,kanban,form',
            'domain': [('category_id', '=', self.id), ('active', '=', True)],
            'context': {
                'default_category_id': self.id,
                'group_by': ['status', 'priority'],
            },
        }

    @api.model
    def get_category_summary(self):
        """Get summary of all categories"""
        categories = self.search([('active', '=', True)])
        
        summary = {
            'total_categories': len(categories),
            'total_requests': sum(cat.total_requests for cat in categories),
            'completed_requests': sum(cat.completed_requests for cat in categories),
            'total_cost': sum(cat.total_cost for cat in categories),
            'categories': []
        }
        
        for category in categories:
            summary['categories'].append({
                'id': category.id,
                'name': category.name,
                'code': category.code,
                'maintenance_type': category.maintenance_type,
                'total_requests': category.total_requests,
                'completed_requests': category.completed_requests,
                'average_duration': category.average_duration,
                'average_cost': category.average_cost,
                'total_cost': category.total_cost,
            })
        
        return summary

    @api.model
    def get_categories_by_type(self, maintenance_type):
        """Get categories filtered by maintenance type"""
        return self.search([
            ('active', '=', True),
            ('maintenance_type', '=', maintenance_type)
        ])

    _sql_constraints = [
        ('code_company_unique', 'UNIQUE(code, company_id)', 
         'Category code must be unique per company!'),
    ]
