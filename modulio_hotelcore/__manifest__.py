# -*- coding: utf-8 -*-
{
    'name': 'Hotel Core',
    'version': '18.0.1.0.5',
    'category': 'Modulio',
    'summary': 'Core hotel management module providing room types, rooms, and basic security',
    'description': """
Hotel Core Module
=================

This module provides the fundamental structure for hotel management:

* Room Types (Standard, Deluxe, Suite)
* Room Management (room number, floor, room type)
* Room Status Machine (Vacant Ready → Reserved → Occupied → Dirty → Inspected → Out of Service)
* Basic Security Groups (Hotel User, Hotel Manager)

This module is essential for Front Office and Housekeeping modules as they depend on room entities.
    """,
    'author': 'Modulio',
    'website': 'https://www.modulio.id',
    'depends': ['base', 'mail'],
    'data': [
        'security/hotel_security.xml',
        'security/ir.model.access.csv',
        'data/hotel_demo_data.xml',
        'views/res_config_settings_view.xml',
        'views/hotel_room_type_views.xml',
        'views/hotel_room_views.xml',
        'views/hotel_room_blocking_views.xml',
        'views/hotel_room_availability_calendar.xml',
        'views/hotel_dashboard_action.xml',
        'views/hotel_menu.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'modulio_hotelcore/static/src/js/hotel_dashboard.js',
            'modulio_hotelcore/static/src/xml/hotel_dashboard.xml',
            'modulio_hotelcore/static/src/scss/hotel_dashboard.scss',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
