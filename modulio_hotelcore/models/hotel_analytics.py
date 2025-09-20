# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta


class HotelAnalytics(models.Model):
    _name = 'hotel.analytics'
    _description = 'Hotel Analytics Dashboard'
    _rec_name = 'name'
    _order = 'create_date desc'

    name = fields.Char(
        string='Dashboard Name',
        required=True,
        default=lambda self: _('Hotel Analytics Dashboard'),
        help='Name of the analytics dashboard'
    )
    
    # Date Range
    start_date = fields.Date(
        string='Start Date',
        required=True,
        default=lambda self: fields.Date.today() - timedelta(days=30),
        help='Start date for analytics period'
    )
    end_date = fields.Date(
        string='End Date',
        required=True,
        default=fields.Date.today,
        help='End date for analytics period'
    )
    
    # Basic KPIs
    total_rooms = fields.Integer(
        string='Total Rooms',
        compute='_compute_basic_kpis',
        store=True,
        help='Total number of rooms in the hotel'
    )
    available_rooms = fields.Integer(
        string='Available Rooms',
        compute='_compute_basic_kpis',
        store=True,
        help='Number of available rooms'
    )
    occupied_rooms = fields.Integer(
        string='Occupied Rooms',
        compute='_compute_basic_kpis',
        store=True,
        help='Number of occupied rooms'
    )
    reserved_rooms = fields.Integer(
        string='Reserved Rooms',
        compute='_compute_basic_kpis',
        store=True,
        help='Number of reserved rooms'
    )
    out_of_service_rooms = fields.Integer(
        string='Out of Service Rooms',
        compute='_compute_basic_kpis',
        store=True,
        help='Number of out of service rooms'
    )
    
    # Occupancy Metrics
    occupancy_rate = fields.Float(
        string='Occupancy Rate (%)',
        compute='_compute_occupancy_metrics',
        store=True,
        help='Overall occupancy rate percentage'
    )
    average_daily_rate = fields.Monetary(
        string='Average Daily Rate',
        currency_field='currency_id',
        compute='_compute_revenue_metrics',
        store=True,
        help='Average daily rate across all room types'
    )
    revenue_per_available_room = fields.Monetary(
        string='RevPAR',
        currency_field='currency_id',
        compute='_compute_revenue_metrics',
        store=True,
        help='Revenue per available room'
    )
    
    # Revenue Metrics
    total_revenue = fields.Monetary(
        string='Total Revenue',
        currency_field='currency_id',
        compute='_compute_revenue_metrics',
        store=True,
        help='Total revenue for the period'
    )
    room_revenue = fields.Monetary(
        string='Room Revenue',
        currency_field='currency_id',
        compute='_compute_revenue_metrics',
        store=True,
        help='Revenue from room bookings'
    )
    amenity_revenue = fields.Monetary(
        string='Amenity Revenue',
        currency_field='currency_id',
        compute='_compute_revenue_metrics',
        store=True,
        help='Revenue from amenities'
    )
    
    # Performance Metrics
    average_stay_duration = fields.Float(
        string='Average Stay Duration (Days)',
        compute='_compute_performance_metrics',
        store=True,
        help='Average length of stay'
    )
    booking_cancellation_rate = fields.Float(
        string='Cancellation Rate (%)',
        compute='_compute_performance_metrics',
        store=True,
        help='Rate of booking cancellations'
    )
    customer_satisfaction_score = fields.Float(
        string='Customer Satisfaction Score',
        compute='_compute_performance_metrics',
        store=True,
        help='Average customer satisfaction rating'
    )
    
    # Maintenance Metrics
    maintenance_requests_count = fields.Integer(
        string='Maintenance Requests',
        compute='_compute_maintenance_metrics',
        store=True,
        help='Number of maintenance requests in period'
    )
    maintenance_completion_rate = fields.Float(
        string='Maintenance Completion Rate (%)',
        compute='_compute_maintenance_metrics',
        store=True,
        help='Percentage of completed maintenance requests'
    )
    average_maintenance_duration = fields.Float(
        string='Average Maintenance Duration (Hours)',
        compute='_compute_maintenance_metrics',
        store=True,
        help='Average time to complete maintenance'
    )
    
    # System Fields
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id,
        required=True,
        ondelete='restrict'
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
        help='Whether this dashboard is active'
    )

    @api.depends('start_date', 'end_date')
    def _compute_basic_kpis(self):
        """Compute basic room KPIs using centralized service"""
        for record in self:
            if not record.start_date or not record.end_date:
                record.total_rooms = 0
                record.available_rooms = 0
                record.occupied_rooms = 0
                record.reserved_rooms = 0
                record.out_of_service_rooms = 0
                continue
                
            # Use centralized analytics service
            room_metrics = self.env['hotel.analytics.service']._get_room_metrics()
            record.total_rooms = room_metrics['total_rooms']
            record.available_rooms = room_metrics['available_rooms']
            record.occupied_rooms = room_metrics['occupied_rooms']
            record.reserved_rooms = room_metrics['reserved_rooms']
            record.out_of_service_rooms = room_metrics['out_of_service_rooms']

    @api.depends('total_rooms', 'occupied_rooms', 'reserved_rooms')
    def _compute_occupancy_metrics(self):
        """Compute occupancy-related metrics"""
        for record in self:
            if record.total_rooms > 0:
                occupied_and_reserved = record.occupied_rooms + record.reserved_rooms
                record.occupancy_rate = (occupied_and_reserved / record.total_rooms) * 100
            else:
                record.occupancy_rate = 0.0

    @api.depends('start_date', 'end_date')
    def _compute_revenue_metrics(self):
        """Compute revenue-related metrics"""
        for record in self:
            if not record.start_date or not record.end_date:
                record.total_revenue = 0.0
                record.room_revenue = 0.0
                record.amenity_revenue = 0.0
                record.average_daily_rate = 0.0
                record.revenue_per_available_room = 0.0
                continue
                
            # Placeholder for revenue calculation
            # In real implementation, this would query actual booking/revenue data
            record.total_revenue = 0.0
            record.room_revenue = 0.0
            record.amenity_revenue = 0.0
            record.average_daily_rate = 0.0
            record.revenue_per_available_room = 0.0

    @api.depends('start_date', 'end_date')
    def _compute_performance_metrics(self):
        """Compute performance-related metrics"""
        for record in self:
            if not record.start_date or not record.end_date:
                record.average_stay_duration = 0.0
                record.booking_cancellation_rate = 0.0
                record.customer_satisfaction_score = 0.0
                continue
                
            # Placeholder for performance calculation
            # In real implementation, this would query actual booking/guest data
            record.average_stay_duration = 0.0
            record.booking_cancellation_rate = 0.0
            record.customer_satisfaction_score = 0.0

    @api.depends('start_date', 'end_date')
    def _compute_maintenance_metrics(self):
        """Compute maintenance-related metrics using centralized service"""
        for record in self:
            if not record.start_date or not record.end_date:
                record.maintenance_requests_count = 0
                record.maintenance_completion_rate = 0.0
                record.average_maintenance_duration = 0.0
                continue
                
            # Use centralized analytics service
            maintenance_metrics = self.env['hotel.analytics.service']._get_maintenance_metrics(
                record.start_date, record.end_date
            )
            record.maintenance_requests_count = maintenance_metrics['maintenance_requests_count']
            record.maintenance_completion_rate = maintenance_metrics['maintenance_completion_rate']
            record.average_maintenance_duration = maintenance_metrics['average_maintenance_duration']

    def action_refresh_analytics(self):
        """Refresh analytics data"""
        self.ensure_one()
        # Force recomputation of all computed fields
        self._compute_basic_kpis()
        self._compute_occupancy_metrics()
        self._compute_revenue_metrics()
        self._compute_performance_metrics()
        self._compute_maintenance_metrics()
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Analytics Refreshed'),
                'message': _('Dashboard data has been updated successfully.'),
                'type': 'success',
                'sticky': False,
            }
        }

    def action_export_analytics(self):
        """Export analytics data to CSV"""
        self.ensure_one()
        
        # Prepare data for export
        export_data = {
            'dashboard_name': self.name,
            'period': f"{self.start_date} to {self.end_date}",
            'export_date': fields.Datetime.now(),
            'kpis': {
                'total_rooms': self.total_rooms,
                'available_rooms': self.available_rooms,
                'occupied_rooms': self.occupied_rooms,
                'reserved_rooms': self.reserved_rooms,
                'out_of_service_rooms': self.out_of_service_rooms,
                'occupancy_rate': self.occupancy_rate,
                'total_revenue': self.total_revenue,
                'room_revenue': self.room_revenue,
                'amenity_revenue': self.amenity_revenue,
                'average_daily_rate': self.average_daily_rate,
                'revenue_per_available_room': self.revenue_per_available_room,
                'average_stay_duration': self.average_stay_duration,
                'booking_cancellation_rate': self.booking_cancellation_rate,
                'customer_satisfaction_score': self.customer_satisfaction_score,
                'maintenance_requests_count': self.maintenance_requests_count,
                'maintenance_completion_rate': self.maintenance_completion_rate,
                'average_maintenance_duration': self.average_maintenance_duration,
            }
        }
        
        # Create CSV content
        csv_content = self._generate_csv_content(export_data)
        
        # Create attachment
        import base64
        attachment = self.env['ir.attachment'].create({
            'name': f'hotel_analytics_export_{fields.Date.today()}.csv',
            'type': 'binary',
            'datas': base64.b64encode(csv_content.encode('utf-8')),
            'mimetype': 'text/csv',
            'res_model': 'hotel.analytics',
            'res_id': self.id,
        })
        
        # Return download action
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'new',
        }

    def _generate_csv_content(self, data):
        """Generate CSV content from analytics data"""
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow(['Hotel Analytics Export'])
        writer.writerow(['Dashboard:', data['dashboard_name']])
        writer.writerow(['Period:', data['period']])
        writer.writerow(['Export Date:', data['export_date']])
        writer.writerow([])  # Empty row
        
        # KPIs Section
        writer.writerow(['Key Performance Indicators'])
        writer.writerow(['Metric', 'Value'])
        writer.writerow(['Total Rooms', data['kpis']['total_rooms']])
        writer.writerow(['Available Rooms', data['kpis']['available_rooms']])
        writer.writerow(['Occupied Rooms', data['kpis']['occupied_rooms']])
        writer.writerow(['Reserved Rooms', data['kpis']['reserved_rooms']])
        writer.writerow(['Out of Service Rooms', data['kpis']['out_of_service_rooms']])
        writer.writerow(['Occupancy Rate (%)', data['kpis']['occupancy_rate']])
        writer.writerow([])  # Empty row
        
        # Revenue Section
        writer.writerow(['Revenue Metrics'])
        writer.writerow(['Metric', 'Value'])
        writer.writerow(['Total Revenue', data['kpis']['total_revenue']])
        writer.writerow(['Room Revenue', data['kpis']['room_revenue']])
        writer.writerow(['Amenity Revenue', data['kpis']['amenity_revenue']])
        writer.writerow(['Average Daily Rate', data['kpis']['average_daily_rate']])
        writer.writerow(['Revenue per Available Room', data['kpis']['revenue_per_available_room']])
        writer.writerow([])  # Empty row
        
        # Performance Section
        writer.writerow(['Performance Metrics'])
        writer.writerow(['Metric', 'Value'])
        writer.writerow(['Average Stay Duration (Days)', data['kpis']['average_stay_duration']])
        writer.writerow(['Booking Cancellation Rate (%)', data['kpis']['booking_cancellation_rate']])
        writer.writerow(['Customer Satisfaction Score', data['kpis']['customer_satisfaction_score']])
        writer.writerow([])  # Empty row
        
        # Maintenance Section
        writer.writerow(['Maintenance Metrics'])
        writer.writerow(['Metric', 'Value'])
        writer.writerow(['Maintenance Requests', data['kpis']['maintenance_requests_count']])
        writer.writerow(['Maintenance Completion Rate (%)', data['kpis']['maintenance_completion_rate']])
        writer.writerow(['Average Maintenance Duration (Hours)', data['kpis']['average_maintenance_duration']])
        
        return output.getvalue()

    @api.model
    def get_dashboard_summary(self):
        """Get a summary of all analytics data for dashboard display"""
        dashboard = self.search([], limit=1)
        if not dashboard:
            dashboard = self.create({
                'name': _('Hotel Analytics Dashboard'),
                'start_date': fields.Date.today() - timedelta(days=30),
                'end_date': fields.Date.today(),
            })
        
        return {
            'total_rooms': dashboard.total_rooms,
            'available_rooms': dashboard.available_rooms,
            'occupied_rooms': dashboard.occupied_rooms,
            'reserved_rooms': dashboard.reserved_rooms,
            'out_of_service_rooms': dashboard.out_of_service_rooms,
            'occupancy_rate': dashboard.occupancy_rate,
            'average_daily_rate': dashboard.average_daily_rate,
            'revenue_per_available_room': dashboard.revenue_per_available_room,
            'total_revenue': dashboard.total_revenue,
            'room_revenue': dashboard.room_revenue,
            'amenity_revenue': dashboard.amenity_revenue,
            'average_stay_duration': dashboard.average_stay_duration,
            'booking_cancellation_rate': dashboard.booking_cancellation_rate,
            'customer_satisfaction_score': dashboard.customer_satisfaction_score,
            'maintenance_requests_count': dashboard.maintenance_requests_count,
            'maintenance_completion_rate': dashboard.maintenance_completion_rate,
            'average_maintenance_duration': dashboard.average_maintenance_duration,
        }
