# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime, timedelta


class HotelAnalyticsService(models.Model):
    _name = 'hotel.analytics.service'
    _description = 'Hotel Analytics Service - Centralized Analytics Data Provider'

    @api.model
    def get_hotel_kpis(self, start_date=None, end_date=None):
        """
        Centralized method to get all hotel KPIs
        This serves as single source of truth for all analytics
        """
        if not start_date:
            start_date = fields.Date.today() - timedelta(days=30)
        if not end_date:
            end_date = fields.Date.today()
            
        return {
            'rooms': self._get_room_metrics(),
            'revenue': self._get_revenue_metrics(start_date, end_date),
            'occupancy': self._get_occupancy_metrics(start_date, end_date),
            'maintenance': self._get_maintenance_metrics(start_date, end_date),
            'amenities': self._get_amenity_metrics(start_date, end_date),
            'performance': self._get_performance_metrics(start_date, end_date),
        }

    def _get_room_metrics(self):
        """Get room-related metrics"""
        rooms = self.env['hotel.room'].search([])
        
        return {
            'total_rooms': len(rooms),
            'clean_rooms': len(rooms.filtered(lambda r: r.state == 'clean')),
            'check_in_rooms': len(rooms.filtered(lambda r: r.state == 'check_in')),
            'check_out_rooms': len(rooms.filtered(lambda r: r.state == 'check_out')),
            'dirty_rooms': len(rooms.filtered(lambda r: r.state == 'dirty')),
            'make_up_room_rooms': len(rooms.filtered(lambda r: r.state == 'make_up_room')),
            'inspected_rooms': len(rooms.filtered(lambda r: r.state == 'inspected')),
            'out_of_service_rooms': len(rooms.filtered(lambda r: r.state == 'out_of_service')),
            'out_of_order_rooms': len(rooms.filtered(lambda r: r.state == 'out_of_order')),
            'house_use_rooms': len(rooms.filtered(lambda r: r.state == 'house_use')),
        }

    def _get_revenue_metrics(self, start_date, end_date):
        """Get revenue-related metrics"""
        # Placeholder for revenue calculation
        # In real implementation, this would query actual booking/revenue data
        return {
            'total_revenue': 0.0,
            'room_revenue': 0.0,
            'amenity_revenue': 0.0,
            'average_daily_rate': 0.0,
            'revenue_per_available_room': 0.0,
        }

    def _get_occupancy_metrics(self, start_date, end_date):
        """Get occupancy-related metrics"""
        room_metrics = self._get_room_metrics()
        total_rooms = room_metrics['total_rooms']
        occupied_rooms = room_metrics['occupied_rooms']
        reserved_rooms = room_metrics['reserved_rooms']
        
        if total_rooms > 0:
            occupancy_rate = ((occupied_rooms + reserved_rooms) / total_rooms) * 100
        else:
            occupancy_rate = 0.0
            
        return {
            'occupancy_rate': occupancy_rate,
            'average_stay_duration': 0.0,  # Placeholder
            'total_nights_sold': 0,  # Placeholder
        }

    def _get_maintenance_metrics(self, start_date, end_date):
        """Get maintenance-related metrics"""
        maintenance_requests = self.env['hotel.maintenance.request'].search([
            ('requested_date', '>=', start_date),
            ('requested_date', '<=', end_date)
        ])
        
        completed_requests = maintenance_requests.filtered(lambda r: r.status == 'completed')
        
        return {
            'maintenance_requests_count': len(maintenance_requests),
            'maintenance_completion_rate': (len(completed_requests) / len(maintenance_requests)) * 100 if maintenance_requests else 0.0,
            'average_maintenance_duration': sum(completed_requests.mapped('actual_duration')) / len(completed_requests) if completed_requests else 0.0,
        }

    def _get_amenity_metrics(self, start_date, end_date):
        """Get amenity-related metrics"""
        amenities = self.env['hotel.amenity'].search([])
        
        return {
            'total_amenities': len(amenities),
            'available_amenities': len(amenities.filtered('is_available')),
            'amenity_usage_count': sum(amenities.mapped('usage_count')),
            'amenity_revenue': sum(amenities.mapped('revenue_generated')),
        }

    def _get_performance_metrics(self, start_date, end_date):
        """Get performance-related metrics"""
        # Placeholder for performance calculation
        return {
            'booking_cancellation_rate': 0.0,
            'customer_satisfaction_score': 0.0,
            'no_show_rate': 0.0,
        }

    @api.model
    def get_room_type_analytics(self, room_type_ids=None):
        """Get analytics for specific room types"""
        if not room_type_ids:
            room_types = self.env['hotel.room.type'].search([])
        else:
            room_types = self.env['hotel.room.type'].browse(room_type_ids)
        
        analytics_data = []
        for room_type in room_types:
            analytics_data.append({
                'id': room_type.id,
                'name': room_type.name,
                'code': room_type.code,
                'total_revenue': room_type.total_revenue,
                'occupancy_rate': room_type.occupancy_rate,
                'average_daily_rate': room_type.average_daily_rate,
                'booking_count': room_type.booking_count,
                'customer_satisfaction_score': room_type.customer_satisfaction_score,
                'is_premium': room_type.is_premium,
                'is_suite': room_type.is_suite,
            })
        
        return analytics_data

    @api.model
    def get_revenue_analytics(self, start_date=None, end_date=None):
        """Get specialized revenue analytics"""
        if not start_date:
            start_date = fields.Date.today() - timedelta(days=30)
        if not end_date:
            end_date = fields.Date.today()
            
        room_types = self.env['hotel.room.type'].search([])
        
        return {
            'room_types': room_types.read([
                'name', 'code', 'total_revenue', 'monthly_revenue', 'daily_revenue',
                'average_daily_rate', 'revenue_per_available_room', 'room_count'
            ]),
            'summary': {
                'total_revenue': sum(room_types.mapped('total_revenue')),
                'average_daily_rate': sum(room_types.mapped('average_daily_rate')) / len(room_types) if room_types else 0,
                'total_room_count': sum(room_types.mapped('room_count')),
            }
        }

    @api.model
    def get_occupancy_analytics(self, start_date=None, end_date=None):
        """Get specialized occupancy analytics"""
        if not start_date:
            start_date = fields.Date.today() - timedelta(days=30)
        if not end_date:
            end_date = fields.Date.today()
            
        room_types = self.env['hotel.room.type'].search([])
        
        return {
            'room_types': room_types.read([
                'name', 'code', 'occupancy_rate', 'monthly_occupancy_rate',
                'total_nights_sold', 'monthly_nights_sold', 'average_length_of_stay', 'room_count'
            ]),
            'summary': {
                'average_occupancy_rate': sum(room_types.mapped('occupancy_rate')) / len(room_types) if room_types else 0,
                'total_nights_sold': sum(room_types.mapped('total_nights_sold')),
                'total_room_count': sum(room_types.mapped('room_count')),
            }
        }

    @api.model
    def get_performance_analytics(self, start_date=None, end_date=None):
        """Get specialized performance analytics"""
        if not start_date:
            start_date = fields.Date.today() - timedelta(days=30)
        if not end_date:
            end_date = fields.Date.today()
            
        room_types = self.env['hotel.room.type'].search([])
        
        return {
            'room_types': room_types.read([
                'name', 'code', 'booking_count', 'monthly_booking_count',
                'cancellation_rate', 'no_show_rate', 'customer_satisfaction_score', 'room_count'
            ]),
            'summary': {
                'total_bookings': sum(room_types.mapped('booking_count')),
                'average_cancellation_rate': sum(room_types.mapped('cancellation_rate')) / len(room_types) if room_types else 0,
                'average_satisfaction': sum(room_types.mapped('customer_satisfaction_score')) / len(room_types) if room_types else 0,
            }
        }

    @api.model
    def get_market_analytics(self, start_date=None, end_date=None):
        """Get specialized market analytics"""
        if not start_date:
            start_date = fields.Date.today() - timedelta(days=30)
        if not end_date:
            end_date = fields.Date.today()
            
        room_types = self.env['hotel.room.type'].search([])
        
        return {
            'room_types': room_types.read([
                'name', 'code', 'market_share', 'competitive_index',
                'demand_forecast', 'seasonal_demand_factor', 'room_count'
            ]),
            'summary': {
                'total_market_share': sum(room_types.mapped('market_share')),
                'average_competitive_index': sum(room_types.mapped('competitive_index')) / len(room_types) if room_types else 0,
                'average_demand_forecast': sum(room_types.mapped('demand_forecast')) / len(room_types) if room_types else 0,
            }
        }
