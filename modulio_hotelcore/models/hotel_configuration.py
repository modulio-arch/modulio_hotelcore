# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class HotelConfiguration(models.Model):
    _name = 'hotel.configuration'
    _description = 'Hotel Configuration'
    _rec_name = 'hotel_name'
    _order = 'hotel_name'

    # Basic Hotel Information
    hotel_name = fields.Char(
        string='Hotel Name',
        required=True,
        help='Name of the hotel'
    )
    hotel_code = fields.Char(
        string='Hotel Code',
        required=True,
        help='Unique code for the hotel (e.g., H001)'
    )
    description = fields.Text(
        string='Description',
        help='Description of the hotel'
    )
    address = fields.Text(
        string='Address',
        help='Hotel address'
    )
    city = fields.Char(
        string='City',
        help='City where the hotel is located'
    )
    state_id = fields.Many2one(
        'res.country.state',
        string='State/Province',
        help='State or province'
    )
    country_id = fields.Many2one(
        'res.country',
        string='Country',
        help='Country where the hotel is located'
    )
    zip = fields.Char(
        string='ZIP Code',
        help='ZIP or postal code'
    )
    phone = fields.Char(
        string='Phone',
        help='Hotel phone number'
    )
    email = fields.Char(
        string='Email',
        help='Hotel email address'
    )
    website = fields.Char(
        string='Website',
        help='Hotel website URL'
    )

    # Hotel Settings
    timezone = fields.Selection([
        ('UTC', 'UTC'),
        ('Asia/Jakarta', 'Asia/Jakarta (WIB)'),
        ('Asia/Makassar', 'Asia/Makassar (WITA)'),
        ('Asia/Jayapura', 'Asia/Jayapura (WIT)'),
        ('Asia/Singapore', 'Asia/Singapore'),
        ('Asia/Kuala_Lumpur', 'Asia/Kuala_Lumpur'),
        ('Asia/Bangkok', 'Asia/Bangkok'),
        ('Asia/Manila', 'Asia/Manila'),
        ('Asia/Tokyo', 'Asia/Tokyo'),
        ('Asia/Seoul', 'Asia/Seoul'),
        ('Asia/Shanghai', 'Asia/Shanghai'),
        ('Asia/Hong_Kong', 'Asia/Hong_Kong'),
        ('Asia/Dubai', 'Asia/Dubai'),
        ('Europe/London', 'Europe/London'),
        ('Europe/Paris', 'Europe/Paris'),
        ('Europe/Berlin', 'Europe/Berlin'),
        ('America/New_York', 'America/New_York'),
        ('America/Los_Angeles', 'America/Los_Angeles'),
        ('Australia/Sydney', 'Australia/Sydney'),
    ], string='Timezone', default='Asia/Jakarta', required=True,
       help='Hotel timezone for operations')

    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        required=True,
        default=lambda self: self.env.company.currency_id,
        help='Default currency for hotel operations'
    )

    # Check-in/Check-out Settings
    check_in_time = fields.Float(
        string='Check-in Time',
        default=14.0,
        help='Default check-in time (24-hour format, e.g., 14.0 for 2:00 PM)'
    )
    check_out_time = fields.Float(
        string='Check-out Time',
        default=12.0,
        help='Default check-out time (24-hour format, e.g., 12.0 for 12:00 PM)'
    )
    early_check_in_allowed = fields.Boolean(
        string='Allow Early Check-in',
        default=True,
        help='Allow guests to check-in before standard check-in time'
    )
    late_check_out_allowed = fields.Boolean(
        string='Allow Late Check-out',
        default=True,
        help='Allow guests to check-out after standard check-out time'
    )
    early_check_in_fee = fields.Monetary(
        string='Early Check-in Fee',
        currency_field='currency_id',
        help='Fee for early check-in (if applicable)'
    )
    late_check_out_fee = fields.Monetary(
        string='Late Check-out Fee',
        currency_field='currency_id',
        help='Fee for late check-out (if applicable)'
    )

    # Room Management Settings
    auto_housekeeping = fields.Boolean(
        string='Auto Housekeeping',
        default=False,
        help='Automatically change housekeeping status based on occupancy'
    )
    housekeeping_inspection_required = fields.Boolean(
        string='Housekeeping Inspection Required',
        default=True,
        help='Require inspection after cleaning before room is available'
    )
    maintenance_auto_assign = fields.Boolean(
        string='Auto Assign Maintenance',
        default=False,
        help='Automatically assign maintenance tasks to specific users'
    )
    room_status_auto_update = fields.Boolean(
        string='Auto Update Room Status',
        default=True,
        help='Automatically update room status based on check-in/check-out'
    )

    # Reservation Settings
    advance_booking_days = fields.Integer(
        string='Advance Booking Days',
        default=365,
        help='Maximum days in advance for booking'
    )
    minimum_stay_nights = fields.Integer(
        string='Minimum Stay Nights',
        default=1,
        help='Minimum number of nights for reservation'
    )
    maximum_stay_nights = fields.Integer(
        string='Maximum Stay Nights',
        default=30,
        help='Maximum number of nights for reservation'
    )
    cancellation_hours = fields.Integer(
        string='Cancellation Hours',
        default=24,
        help='Hours before check-in for free cancellation'
    )
    no_show_hours = fields.Integer(
        string='No-Show Hours',
        default=2,
        help='Hours after check-in time to consider as no-show'
    )

    # Pricing Settings
    base_price_currency = fields.Many2one(
        'res.currency',
        string='Base Price Currency',
        required=True,
        default=lambda self: self.env.company.currency_id,
        help='Currency for base room prices'
    )
    tax_included = fields.Boolean(
        string='Tax Included in Price',
        default=True,
        help='Whether taxes are included in room prices'
    )
    service_charge_rate = fields.Float(
        string='Service Charge Rate (%)',
        default=10.0,
        help='Service charge rate as percentage'
    )
    government_tax_rate = fields.Float(
        string='Government Tax Rate (%)',
        default=10.0,
        help='Government tax rate as percentage'
    )

    # Housekeeping Settings
    housekeeping_shift_start = fields.Float(
        string='Housekeeping Shift Start',
        default=8.0,
        help='Housekeeping shift start time (24-hour format)'
    )
    housekeeping_shift_end = fields.Float(
        string='Housekeeping Shift End',
        default=17.0,
        help='Housekeeping shift end time (24-hour format)'
    )
    housekeeping_rooms_per_staff = fields.Integer(
        string='Rooms per Housekeeping Staff',
        default=15,
        help='Average number of rooms per housekeeping staff member'
    )
    housekeeping_inspection_time = fields.Float(
        string='Housekeeping Inspection Time (minutes)',
        default=15.0,
        help='Average time for housekeeping inspection per room'
    )

    # Maintenance Settings
    maintenance_priority_levels = fields.Selection([
        ('3', '3 Levels (Low, Medium, High)'),
        ('5', '5 Levels (Very Low, Low, Medium, High, Critical)'),
    ], string='Maintenance Priority Levels', default='3',
       help='Number of priority levels for maintenance requests')

    maintenance_response_time = fields.Integer(
        string='Maintenance Response Time (hours)',
        default=4,
        help='Maximum response time for maintenance requests'
    )
    maintenance_escalation_hours = fields.Integer(
        string='Maintenance Escalation Time (hours)',
        default=24,
        help='Hours before escalating maintenance requests'
    )

    # Security Settings
    key_card_system = fields.Boolean(
        string='Key Card System',
        default=True,
        help='Hotel uses key card system for room access'
    )
    cctv_monitoring = fields.Boolean(
        string='CCTV Monitoring',
        default=True,
        help='Hotel has CCTV monitoring system'
    )
    security_24_7 = fields.Boolean(
        string='24/7 Security',
        default=True,
        help='Hotel has 24/7 security service'
    )
    guest_registration_required = fields.Boolean(
        string='Guest Registration Required',
        default=True,
        help='Require guest registration for all occupants'
    )

    # Integration Settings
    pms_integration = fields.Boolean(
        string='PMS Integration',
        default=False,
        help='Hotel uses external PMS system'
    )
    pms_system_name = fields.Char(
        string='PMS System Name',
        help='Name of the PMS system'
    )
    pms_api_url = fields.Char(
        string='PMS API URL',
        help='API URL for PMS integration'
    )
    pms_api_key = fields.Char(
        string='PMS API Key',
        help='API key for PMS integration'
    )

    # Reporting Settings
    daily_report_time = fields.Float(
        string='Daily Report Time',
        default=8.0,
        help='Time to generate daily reports (24-hour format)'
    )
    weekly_report_day = fields.Selection([
        ('0', 'Monday'),
        ('1', 'Tuesday'),
        ('2', 'Wednesday'),
        ('3', 'Thursday'),
        ('4', 'Friday'),
        ('5', 'Saturday'),
        ('6', 'Sunday'),
    ], string='Weekly Report Day', default='0',
       help='Day of the week to generate weekly reports')
    monthly_report_day = fields.Integer(
        string='Monthly Report Day',
        default=1,
        help='Day of the month to generate monthly reports'
    )

    # System Settings
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
        help='Whether this configuration is active'
    )

    # Computed Fields
    full_address = fields.Char(
        string='Full Address',
        compute='_compute_full_address',
        store=True,
        help='Complete address of the hotel'
    )
    timezone_display = fields.Char(
        string='Timezone Display',
        compute='_compute_timezone_display',
        help='Human-readable timezone display'
    )

    @api.depends('address', 'city', 'state_id', 'country_id', 'zip')
    def _compute_full_address(self):
        """Compute full address string"""
        for record in self:
            address_parts = []
            if record.address:
                address_parts.append(record.address)
            if record.city:
                address_parts.append(record.city)
            if record.state_id:
                address_parts.append(record.state_id.name)
            if record.country_id:
                address_parts.append(record.country_id.name)
            if record.zip:
                address_parts.append(record.zip)
            
            record.full_address = ', '.join(address_parts) if address_parts else ''

    @api.depends('timezone')
    def _compute_timezone_display(self):
        """Compute human-readable timezone display"""
        for record in self:
            timezone_map = {
                'UTC': 'UTC (Coordinated Universal Time)',
                'Asia/Jakarta': 'Asia/Jakarta (Western Indonesia Time - WIB)',
                'Asia/Makassar': 'Asia/Makassar (Central Indonesia Time - WITA)',
                'Asia/Jayapura': 'Asia/Jayapura (Eastern Indonesia Time - WIT)',
                'Asia/Singapore': 'Asia/Singapore (Singapore Time)',
                'Asia/Kuala_Lumpur': 'Asia/Kuala_Lumpur (Malaysia Time)',
                'Asia/Bangkok': 'Asia/Bangkok (Thailand Time)',
                'Asia/Manila': 'Asia/Manila (Philippines Time)',
                'Asia/Tokyo': 'Asia/Tokyo (Japan Time)',
                'Asia/Seoul': 'Asia/Seoul (Korea Time)',
                'Asia/Shanghai': 'Asia/Shanghai (China Time)',
                'Asia/Hong_Kong': 'Asia/Hong_Kong (Hong Kong Time)',
                'Asia/Dubai': 'Asia/Dubai (UAE Time)',
                'Europe/London': 'Europe/London (GMT/BST)',
                'Europe/Paris': 'Europe/Paris (CET/CEST)',
                'Europe/Berlin': 'Europe/Berlin (CET/CEST)',
                'America/New_York': 'America/New_York (EST/EDT)',
                'America/Los_Angeles': 'America/Los_Angeles (PST/PDT)',
                'Australia/Sydney': 'Australia/Sydney (AEST/AEDT)',
            }
            record.timezone_display = timezone_map.get(record.timezone, record.timezone)

    @api.constrains('hotel_code')
    def _check_hotel_code_unique(self):
        """Ensure hotel code is unique per company"""
        for record in self:
            if self.search_count([
                ('hotel_code', '=', record.hotel_code),
                ('company_id', '=', record.company_id.id),
                ('id', '!=', record.id)
            ]) > 0:
                raise ValidationError(_("Hotel code must be unique per company!"))

    @api.constrains('check_in_time', 'check_out_time')
    def _check_check_times(self):
        """Validate check-in and check-out times"""
        for record in self:
            if record.check_in_time < 0 or record.check_in_time >= 24:
                raise ValidationError(_("Check-in time must be between 0 and 23.99"))
            if record.check_out_time < 0 or record.check_out_time >= 24:
                raise ValidationError(_("Check-out time must be between 0 and 23.99"))
            if record.check_in_time == record.check_out_time:
                raise ValidationError(_("Check-in and check-out times cannot be the same"))

    @api.constrains('advance_booking_days', 'minimum_stay_nights', 'maximum_stay_nights')
    def _check_booking_settings(self):
        """Validate booking settings"""
        for record in self:
            if record.advance_booking_days < 1:
                raise ValidationError(_("Advance booking days must be at least 1"))
            if record.minimum_stay_nights < 1:
                raise ValidationError(_("Minimum stay nights must be at least 1"))
            if record.maximum_stay_nights < record.minimum_stay_nights:
                raise ValidationError(_("Maximum stay nights must be greater than or equal to minimum stay nights"))

    @api.constrains('service_charge_rate', 'government_tax_rate')
    def _check_tax_rates(self):
        """Validate tax rates"""
        for record in self:
            if record.service_charge_rate < 0 or record.service_charge_rate > 100:
                raise ValidationError(_("Service charge rate must be between 0 and 100"))
            if record.government_tax_rate < 0 or record.government_tax_rate > 100:
                raise ValidationError(_("Government tax rate must be between 0 and 100"))

    @api.model
    def get_hotel_config(self):
        """Get current hotel configuration"""
        config = self.search([('active', '=', True)], limit=1)
        if not config:
            # Create default configuration if none exists
            config = self.create({
                'hotel_name': 'Default Hotel',
                'hotel_code': 'H001',
                'description': 'Default hotel configuration',
            })
        return config

    @api.model
    def get_check_in_out_times(self):
        """Get check-in and check-out times"""
        config = self.get_hotel_config()
        return {
            'check_in_time': config.check_in_time,
            'check_out_time': config.check_out_time,
            'early_check_in_allowed': config.early_check_in_allowed,
            'late_check_out_allowed': config.late_check_out_allowed,
        }

    @api.model
    def get_booking_policies(self):
        """Get booking policies"""
        config = self.get_hotel_config()
        return {
            'advance_booking_days': config.advance_booking_days,
            'minimum_stay_nights': config.minimum_stay_nights,
            'maximum_stay_nights': config.maximum_stay_nights,
            'cancellation_hours': config.cancellation_hours,
            'no_show_hours': config.no_show_hours,
        }

    @api.model
    def get_pricing_settings(self):
        """Get pricing settings"""
        config = self.get_hotel_config()
        return {
            'base_price_currency': config.base_price_currency.id,
            'tax_included': config.tax_included,
            'service_charge_rate': config.service_charge_rate,
            'government_tax_rate': config.government_tax_rate,
        }

    @api.model
    def get_housekeeping_settings(self):
        """Get housekeeping settings"""
        config = self.get_hotel_config()
        return {
            'auto_housekeeping': config.auto_housekeeping,
            'housekeeping_inspection_required': config.housekeeping_inspection_required,
            'housekeeping_shift_start': config.housekeeping_shift_start,
            'housekeeping_shift_end': config.housekeeping_shift_end,
            'housekeeping_rooms_per_staff': config.housekeeping_rooms_per_staff,
            'housekeeping_inspection_time': config.housekeeping_inspection_time,
        }

    @api.model
    def get_maintenance_settings(self):
        """Get maintenance settings"""
        config = self.get_hotel_config()
        return {
            'maintenance_priority_levels': config.maintenance_priority_levels,
            'maintenance_response_time': config.maintenance_response_time,
            'maintenance_escalation_hours': config.maintenance_escalation_hours,
            'maintenance_auto_assign': config.maintenance_auto_assign,
        }

    @api.model
    def get_security_settings(self):
        """Get security settings"""
        config = self.get_hotel_config()
        return {
            'key_card_system': config.key_card_system,
            'cctv_monitoring': config.cctv_monitoring,
            'security_24_7': config.security_24_7,
            'guest_registration_required': config.guest_registration_required,
        }

    @api.model
    def get_integration_settings(self):
        """Get integration settings"""
        config = self.get_hotel_config()
        return {
            'pms_integration': config.pms_integration,
            'pms_system_name': config.pms_system_name,
            'pms_api_url': config.pms_api_url,
            'pms_api_key': config.pms_api_key,
        }

    @api.model
    def get_reporting_settings(self):
        """Get reporting settings"""
        config = self.get_hotel_config()
        return {
            'daily_report_time': config.daily_report_time,
            'weekly_report_day': config.weekly_report_day,
            'monthly_report_day': config.monthly_report_day,
        }

    def action_view_rooms(self):
        """Action to view all rooms"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Rooms - {self.hotel_name}',
            'res_model': 'hotel.room',
            'view_mode': 'list,kanban,form',
            'context': {'default_company_id': self.company_id.id},
        }

    def action_view_floors(self):
        """Action to view all floors"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Floors - {self.hotel_name}',
            'res_model': 'hotel.floor',
            'view_mode': 'list,kanban,form',
            'context': {'default_company_id': self.company_id.id},
        }

    def action_view_room_types(self):
        """Action to view all room types"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Room Types - {self.hotel_name}',
            'res_model': 'hotel.room.type',
            'view_mode': 'list,kanban,form',
            'context': {'default_company_id': self.company_id.id},
        }

    _sql_constraints = [
        ('hotel_code_company_unique', 'UNIQUE(hotel_code, company_id)', 
         'Hotel code must be unique per company!'),
    ]
