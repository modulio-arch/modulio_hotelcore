# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class HotelMaintenanceRequest(models.Model):
    _name = 'hotel.maintenance.request'
    _description = 'Hotel Maintenance Request'
    _order = 'priority desc, create_date desc'
    _rec_name = 'display_name'

    # Basic Information
    name = fields.Char(
        string='Request Number',
        required=True,
        index=True,
        default=lambda self: _('New'),
        help='Unique request number'
    )
    title = fields.Char(
        string='Title',
        required=True,
        help='Brief title of the maintenance request'
    )
    description = fields.Text(
        string='Description',
        required=True,
        help='Detailed description of the maintenance issue'
    )

    # Related Objects
    room_id = fields.Many2one(
        'hotel.room',
        string='Room',
        index=True,
        ondelete='cascade',
        help='Room that requires maintenance'
    )
    amenity_id = fields.Many2one(
        'hotel.amenity',
        string='Amenity',
        index=True,
        ondelete='cascade',
        help='Amenity that requires maintenance'
    )
    floor_id = fields.Many2one(
        'hotel.floor',
        string='Floor',
        index=True,
        ondelete='cascade',
        help='Floor that requires maintenance'
    )

    # Room Information (Related fields for easy access)
    room_number = fields.Char(
        related='room_id.room_number',
        string='Room Number',
        store=True,
        help='Room number for easy reference'
    )
    floor_number = fields.Integer(
        related='room_id.floor',
        string='Floor Number',
        store=True,
        help='Floor number for easy reference'
    )
    room_type_id = fields.Many2one(
        related='room_id.room_type_id',
        string='Room Type',
        store=True,
        help='Type of the room'
    )

    # Maintenance Details
    maintenance_type = fields.Selection([
        ('room', 'Room Maintenance'),
        ('amenity', 'Amenity Maintenance'),
        ('floor', 'Floor Maintenance'),
        ('general', 'General Maintenance'),
        ('emergency', 'Emergency Maintenance'),
    ], string='Maintenance Type', required=True, default='room',
       help='Type of maintenance request')

    category_id = fields.Many2one(
        'hotel.maintenance.category',
        string='Category',
        required=True,
        index=True,
        ondelete='restrict',
        help='Category of the maintenance request'
    )

    priority = fields.Selection([
        ('1', 'Very Low'),
        ('2', 'Low'),
        ('3', 'Medium'),
        ('4', 'High'),
        ('5', 'Critical'),
    ], string='Priority', default='3', required=True,
       help='Priority level of the maintenance request')

    status = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('assigned', 'Assigned'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('on_hold', 'On Hold'),
    ], string='Status', default='draft', required=True, index=True,
       help='Current status of the maintenance request')

    # Assignment and Responsibility
    requested_by = fields.Many2one(
        'res.users',
        string='Requested By',
        required=True,
        default=lambda self: self.env.user,
        index=True,
        help='User who requested the maintenance'
    )
    assigned_to = fields.Many2one(
        'res.users',
        string='Assigned To',
        index=True,
        help='User assigned to perform the maintenance'
    )
    department_id = fields.Many2one(
        'hr.department',
        string='Department',
        help='Department responsible for the maintenance'
    )

    # Scheduling
    requested_date = fields.Datetime(
        string='Requested Date',
        required=True,
        default=fields.Datetime.now,
        help='Date when the maintenance was requested'
    )
    scheduled_date = fields.Datetime(
        string='Scheduled Date',
        help='Scheduled date for the maintenance'
    )
    start_date = fields.Datetime(
        string='Start Date',
        help='Actual start date of the maintenance'
    )
    completion_date = fields.Datetime(
        string='Completion Date',
        help='Actual completion date of the maintenance'
    )
    estimated_duration = fields.Float(
        string='Estimated Duration (hours)',
        help='Estimated duration in hours'
    )
    actual_duration = fields.Float(
        string='Actual Duration (hours)',
        compute='_compute_actual_duration',
        store=True,
        help='Actual duration in hours'
    )

    # Cost and Resources
    estimated_cost = fields.Monetary(
        string='Estimated Cost',
        currency_field='currency_id',
        help='Estimated cost for the maintenance'
    )
    actual_cost = fields.Monetary(
        string='Actual Cost',
        currency_field='currency_id',
        help='Actual cost for the maintenance'
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id,
        help='Currency for cost calculations'
    )

    # Parts and Materials
    parts_required = fields.Text(
        string='Parts Required',
        help='List of parts required for the maintenance'
    )
    parts_ordered = fields.Boolean(
        string='Parts Ordered',
        default=False,
        help='Whether required parts have been ordered'
    )
    parts_received = fields.Boolean(
        string='Parts Received',
        default=False,
        help='Whether required parts have been received'
    )

    # Work Details
    work_performed = fields.Text(
        string='Work Performed',
        help='Description of work performed'
    )
    work_notes = fields.Text(
        string='Work Notes',
        help='Additional notes about the work performed'
    )
    quality_check = fields.Boolean(
        string='Quality Check',
        default=False,
        help='Whether quality check has been performed'
    )
    quality_notes = fields.Text(
        string='Quality Notes',
        help='Notes from quality check'
    )

    # Follow-up and Resolution
    resolution = fields.Text(
        string='Resolution',
        help='How the issue was resolved'
    )
    follow_up_required = fields.Boolean(
        string='Follow-up Required',
        default=False,
        help='Whether follow-up is required'
    )
    follow_up_date = fields.Date(
        string='Follow-up Date',
        help='Date for follow-up check'
    )
    customer_satisfaction = fields.Selection([
        ('1', 'Very Dissatisfied'),
        ('2', 'Dissatisfied'),
        ('3', 'Neutral'),
        ('4', 'Satisfied'),
        ('5', 'Very Satisfied'),
    ], string='Customer Satisfaction',
       help='Customer satisfaction rating')

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
        help='Whether this request is active'
    )

    # Computed Fields
    display_name = fields.Char(
        string='Display Name',
        compute='_compute_display_name',
        store=True,
        help='Display name for the request'
    )
    is_overdue = fields.Boolean(
        string='Is Overdue',
        compute='_compute_is_overdue',
        store=True,
        help='Whether the request is overdue'
    )
    days_since_request = fields.Integer(
        string='Days Since Request',
        compute='_compute_days_since_request',
        store=True,
        help='Number of days since the request was made'
    )

    @api.depends('name', 'title', 'room_number')
    def _compute_display_name(self):
        """Compute display name for the request"""
        for record in self:
            if record.room_number and record.title:
                record.display_name = f"{record.name} - {record.title} (Room {record.room_number})"
            elif record.title:
                record.display_name = f"{record.name} - {record.title}"
            else:
                record.display_name = record.name or f"Maintenance Request - {record.id}"

    @api.depends('scheduled_date', 'status')
    def _compute_is_overdue(self):
        """Compute if the request is overdue"""
        for record in self:
            if record.scheduled_date and record.status in ['submitted', 'assigned', 'in_progress']:
                record.is_overdue = fields.Datetime.now() > record.scheduled_date
            else:
                record.is_overdue = False

    @api.depends('requested_date')
    def _compute_days_since_request(self):
        """Compute days since request was made"""
        for record in self:
            if record.requested_date:
                delta = fields.Datetime.now() - record.requested_date
                record.days_since_request = delta.days
            else:
                record.days_since_request = 0

    @api.depends('start_date', 'completion_date')
    def _compute_actual_duration(self):
        """Compute actual duration of the maintenance"""
        for record in self:
            if record.start_date and record.completion_date:
                delta = record.completion_date - record.start_date
                record.actual_duration = delta.total_seconds() / 3600  # Convert to hours
            else:
                record.actual_duration = 0.0

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to generate request number"""
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('hotel.maintenance.request') or _('New')
        return super().create(vals_list)

    def action_submit(self):
        """Submit the maintenance request"""
        self.ensure_one()
        if self.status != 'draft':
            raise ValidationError(_("Only draft requests can be submitted!"))
        
        self.write({
            'status': 'submitted',
            'requested_date': fields.Datetime.now(),
        })

    def action_assign(self, user_id):
        """Assign the maintenance request to a user"""
        self.ensure_one()
        if self.status not in ['submitted', 'assigned']:
            raise ValidationError(_("Only submitted or assigned requests can be reassigned!"))
        
        self.write({
            'status': 'assigned',
            'assigned_to': user_id,
        })

    def action_start(self):
        """Start the maintenance work"""
        self.ensure_one()
        if self.status != 'assigned':
            raise ValidationError(_("Only assigned requests can be started!"))
        
        self.write({
            'status': 'in_progress',
            'start_date': fields.Datetime.now(),
        })

    def action_complete(self):
        """Complete the maintenance work"""
        self.ensure_one()
        if self.status != 'in_progress':
            raise ValidationError(_("Only in-progress requests can be completed!"))
        
        self.write({
            'status': 'completed',
            'completion_date': fields.Datetime.now(),
        })

    def action_cancel(self):
        """Cancel the maintenance request"""
        self.ensure_one()
        if self.status in ['completed', 'cancelled']:
            raise ValidationError(_("Completed or cancelled requests cannot be cancelled!"))
        
        self.write({'status': 'cancelled'})

    def action_hold(self):
        """Put the maintenance request on hold"""
        self.ensure_one()
        if self.status not in ['assigned', 'in_progress']:
            raise ValidationError(_("Only assigned or in-progress requests can be put on hold!"))
        
        self.write({'status': 'on_hold'})

    def action_resume(self):
        """Resume the maintenance request from hold"""
        self.ensure_one()
        if self.status != 'on_hold':
            raise ValidationError(_("Only on-hold requests can be resumed!"))
        
        self.write({'status': 'in_progress'})

    def action_view_room(self):
        """Action to view the room"""
        self.ensure_one()
        if not self.room_id:
            raise ValidationError(_("No room associated with this request!"))
        
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
        if not self.amenity_id:
            raise ValidationError(_("No amenity associated with this request!"))
        
        return {
            'type': 'ir.actions.act_window',
            'name': f'Amenity - {self.amenity_id.name}',
            'res_model': 'hotel.amenity',
            'view_mode': 'form',
            'res_id': self.amenity_id.id,
            'target': 'current',
        }

    @api.model
    def get_maintenance_summary(self, start_date=None, end_date=None):
        """Get maintenance summary for a period"""
        domain = [('active', '=', True)]
        if start_date:
            domain.append(('requested_date', '>=', start_date))
        if end_date:
            domain.append(('requested_date', '<=', end_date))
        
        requests = self.search(domain)
        
        summary = {
            'total_requests': len(requests),
            'by_status': {},
            'by_priority': {},
            'by_type': {},
            'overdue_count': len(requests.filtered('is_overdue')),
            'total_cost': sum(requests.mapped('actual_cost')),
            'average_duration': sum(requests.mapped('actual_duration')) / len(requests) if requests else 0,
        }
        
        # Count by status
        for status in ['draft', 'submitted', 'assigned', 'in_progress', 'completed', 'cancelled', 'on_hold']:
            summary['by_status'][status] = len(requests.filtered(lambda r: r.status == status))
        
        # Count by priority
        for priority in ['1', '2', '3', '4', '5']:
            summary['by_priority'][priority] = len(requests.filtered(lambda r: r.priority == priority))
        
        # Count by type
        for mtype in ['room', 'amenity', 'floor', 'general', 'emergency']:
            summary['by_type'][mtype] = len(requests.filtered(lambda r: r.maintenance_type == mtype))
        
        return summary

    @api.model
    def get_overdue_requests(self):
        """Get all overdue maintenance requests"""
        return self.search([
            ('active', '=', True),
            ('is_overdue', '=', True),
            ('status', 'in', ['submitted', 'assigned', 'in_progress'])
        ])

    @api.model
    def get_technician_workload(self, user_id, start_date=None, end_date=None):
        """Get workload for a specific technician"""
        domain = [
            ('assigned_to', '=', user_id),
            ('status', 'in', ['assigned', 'in_progress', 'on_hold'])
        ]
        if start_date:
            domain.append(('scheduled_date', '>=', start_date))
        if end_date:
            domain.append(('scheduled_date', '<=', end_date))
        
        return self.search(domain)

    _sql_constraints = [
        ('name_unique', 'UNIQUE(name)', 
         'Maintenance request number must be unique!'),
    ]
