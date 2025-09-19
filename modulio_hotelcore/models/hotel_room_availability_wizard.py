# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta


class HotelRoomAvailabilityWizard(models.TransientModel):
    _name = 'hotel.room.availability.wizard'
    _description = 'Hotel Room Availability Wizard'

    start_date = fields.Date(
        string='Start Date',
        required=True,
        default=lambda self: fields.Date.today(),
        help='Start date for availability check'
    )
    end_date = fields.Date(
        string='End Date',
        required=True,
        default=lambda self: fields.Date.today() + timedelta(days=30),
        help='End date for availability check'
    )
    room_type_id = fields.Many2one(
        'hotel.room.type',
        string='Room Type',
        help='Filter by room type'
    )
    floor = fields.Integer(
        string='Floor',
        help='Filter by floor number'
    )

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        """Validate that start_date is before end_date"""
        for record in self:
            if record.start_date and record.end_date and record.start_date > record.end_date:
                raise ValidationError("Start date must be before or equal to end date.")

    def action_apply_filter(self):
        """Apply the filter and return to calendar view"""
        self.ensure_one()
        
        # Prepare domain for filtering
        domain = []
        
        if self.room_type_id:
            domain.append(('room_type_id', '=', self.room_type_id.id))
        
        if self.floor:
            domain.append(('floor', '=', self.floor))
        
        # Return action with filtered calendar view
        return {
            'type': 'ir.actions.act_window',
            'name': f'Room Availability - {self.start_date} to {self.end_date}',
            'res_model': 'hotel.room',
            'view_mode': 'calendar,list,form',
            'view_id': False,
            'domain': domain,
            'context': {
                'start_date': self.start_date,
                'end_date': self.end_date,
                'room_type_id': self.room_type_id.id if self.room_type_id else False,
                'floor': self.floor or False,
            },
            'target': 'current',
        }

    def action_get_availability_report(self):
        """Generate availability report for the selected period"""
        self.ensure_one()
        
        # Get all rooms based on filters
        domain = []
        if self.room_type_id:
            domain.append(('room_type_id', '=', self.room_type_id.id))
        if self.floor:
            domain.append(('floor', '=', self.floor))
        
        rooms = self.env['hotel.room'].search(domain)
        
        # Generate availability data
        availability_data = []
        for room in rooms:
            availability = room.get_availability(self.start_date, self.end_date)
            availability_data.append(availability)
        
        # Create report data
        report_data = {
            'start_date': self.start_date,
            'end_date': self.end_date,
            'room_type': self.room_type_id.name if self.room_type_id else 'All Types',
            'floor': self.floor if self.floor else 'All Floors',
            'rooms': availability_data,
            'total_rooms': len(rooms),
            'available_rooms': len([r for r in availability_data if r['available']]),
            'blocked_rooms': len([r for r in availability_data if not r['not_blocked']]),
            'status_breakdown': self._get_status_breakdown(availability_data),
        }
        
        # Return report action (you can create a report view for this)
        return {
            'type': 'ir.actions.act_window',
            'name': f'Availability Report - {self.start_date} to {self.end_date}',
            'res_model': 'hotel.room.availability.report',
            'view_mode': 'list,form',
            'context': {'report_data': report_data},
            'target': 'new',
        }

    def _get_status_breakdown(self, availability_data):
        """Get breakdown of room statuses"""
        status_count = {}
        for room_data in availability_data:
            status = room_data['status']
            status_count[status] = status_count.get(status, 0) + 1
        return status_count
