# -*- coding: utf-8 -*-

from odoo import models, api, _
from odoo.exceptions import AccessError


class HotelRoomType(models.Model):
    _inherit = 'hotel.room.type'

    @api.model
    def check_access_rights(self, operation, raise_exception=True):
        """Override access rights check with custom error message"""
        result = super().check_access_rights(operation, raise_exception=False)
        
        if not result and raise_exception:
            if operation == 'create':
                raise AccessError(_(
                    "🏨 Hotel Room Type Creation Restricted\n\n"
                    "You don't have permission to create new room types.\n\n"
                    "This operation is only allowed for Hotel Managers.\n\n"
                    "Please contact your Hotel Manager or Administrator to:\n"
                    "• Create new room types (Standard, Deluxe, Suite, etc.)\n"
                    "• Configure room pricing and amenities\n"
                    "• Set up room capacity and features\n\n"
                    "As a Hotel User, you can:\n"
                    "• View existing room types\n"
                    "• Manage occupancy/housekeeping and maintenance\n"
                    "• Update room information"
                ))
            elif operation == 'write':
                raise AccessError(_(
                    "🏨 Room Type Modification Restricted\n\n"
                    "You don't have permission to modify room types.\n\n"
                    "This operation is only allowed for Hotel Managers.\n\n"
                    "Please contact your Hotel Manager or Administrator to:\n"
                    "• Update room type details\n"
                    "• Change pricing and amenities\n"
                    "• Modify room capacity settings\n\n"
                    "As a Hotel User, you can:\n"
                    "• View room type information\n"
                    "• Manage individual room occupancy/housekeeping\n"
                    "• Update room maintenance notes"
                ))
            elif operation == 'unlink':
                raise AccessError(_(
                    "🏨 Room Type Deletion Restricted\n\n"
                    "You don't have permission to delete room types.\n\n"
                    "This operation is only allowed for Hotel Managers.\n\n"
                    "Please contact your Hotel Manager or Administrator to:\n"
                    "• Remove unused room types\n"
                    "• Archive old room configurations\n\n"
                    "As a Hotel User, you can:\n"
                    "• View all room types\n"
                    "• Manage occupancy/housekeeping and maintenance"
                ))
        
        return result

    def toggle_active(self):
        """Disable toggle_active for Hotel Room Type - Archive/Unarchive not allowed"""
        raise AccessError(_(
            "🏨 Archive/Unarchive Not Available\n\n"
            "Archive and unarchive functionality is not available for room types.\n\n"
            "If you need to manage room types:\n"
            "• Delete unused room types permanently\n"
            "• Create new room types as needed\n"
            "• Use occupancy/housekeeping states for availability control\n\n"
            "For availability control, use:\n"
            "• Occupancy: Out of Service / Available / Reserved / Occupied\n"
            "• Housekeeping: Dirty / Clean / Inspected"
        ))


class HotelRoom(models.Model):
    _inherit = 'hotel.room'

    @api.model
    def check_access_rights(self, operation, raise_exception=True):
        """Override access rights check with custom error message"""
        result = super().check_access_rights(operation, raise_exception=False)
        
        if not result and raise_exception:
            if operation == 'create':
                raise AccessError(_(
                    "🏨 Hotel Room Creation Restricted\n\n"
                    "You don't have permission to create new rooms.\n\n"
                    "This operation is only allowed for Hotel Managers.\n\n"
                    "Please contact your Hotel Manager or Administrator to:\n"
                    "• Add new rooms to the hotel\n"
                    "• Set up room numbers and floor assignments\n"
                    "• Configure room types and features\n\n"
                    "As a Hotel User, you can:\n"
                    "• View all rooms and their occupancy/housekeeping states\n"
                    "• Update occupancy (Reserve/Check-in/Check-out) and housekeeping (Clean/Inspect)\n"
                    "• Manage room maintenance and notes"
                ))
            elif operation == 'unlink':
                raise AccessError(_(
                    "🏨 Hotel Room Deletion Restricted\n\n"
                    "You don't have permission to delete rooms.\n\n"
                    "This operation is only allowed for Hotel Managers.\n\n"
                    "Please contact your Hotel Manager or Administrator to:\n"
                    "• Remove rooms from the system\n"
                    "• Archive unused room records\n\n"
                    "As a Hotel User, you can:\n"
                    "• View all rooms and their occupancy/housekeeping states\n"
                    "• Update room information and maintenance notes\n"
                    "• Change room status as needed"
                ))
        
        return result

    def toggle_active(self):
        """Disable toggle_active for Hotel Room - Archive/Unarchive not allowed"""
        raise AccessError(_(
            "🏨 Archive/Unarchive Not Available\n\n"
            "Archive and unarchive functionality is not available for rooms.\n\n"
            "If you need to manage rooms:\n"
            "• Delete unused rooms permanently\n"
            "• Create new rooms as needed\n"
            "• Use occupancy/housekeeping states for availability control\n\n"
            "For availability control, use:\n"
            "• Occupancy: Out of Service / Available / Reserved / Occupied\n"
            "• Housekeeping: Dirty / Clean / Inspected"
        ))

