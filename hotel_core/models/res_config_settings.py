# -*- coding: utf-8 -*-

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    modulio_hotelcore_event_closes_inventory = fields.Boolean(
        string='Event Closes Inventory',
        help='If enabled, Event blockings will close inventory (set occupancy to Out of Service).',
        config_parameter='modulio_hotelcore.event_closes_inventory',
    )

    modulio_hotelcore_require_inspected_to_sell = fields.Boolean(
        string='Require Inspected to Sell',
        help='If enabled, a room must be Inspected (housekeeping) to be sellable.',
        config_parameter='modulio_hotelcore.require_inspected_to_sell',
    )


