# -*- coding: utf-8 -*-
#
#
#    Authors: Alexandre Fayolle
#    Copyright 2015 Camptocamp SA
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more description.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#
from openerp import models, api


class StockMove(models.Model):
    _inherit = 'stock.move'

    @api.depends('picking_id.picking_type_id.code',
                 'picking_id.picking_type_id.warehouse_id.partner_id',
                 'picking_id.group_id.procurement_ids.purchase_id.partner_id')
    @api.one
    def _get_ship_addresses(self):
        super(StockMove, self)._get_ship_addresses()

        ref_donation = 'logistic_order_donation.picking_type_donation'
        if self.picking_id.picking_type_id == self.env.ref(ref_donation):
            self.ship_from_address_id = self.picking_id.group_id.mapped(
                'procurement_ids.sale_line_id.order_id.partner_id')
            self.ship_to_address_id = self.partner_id
