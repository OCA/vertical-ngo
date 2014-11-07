# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright 2013-2014 Camptocamp SA
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp import models, fields, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    incoterm_address = fields.Char(
        'Incoterm Place',
        help="Incoterm Place of Delivery. "
             "International Commercial Terms are a series of "
             "predefined commercial terms used in "
             "international transactions.")
    delivery_time = fields.Char('Delivery time')


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.model
    def _get_po_location_usage(self, purchase_order_line):
        """Retrieve the destination location usage of a PO
        from a PO line

        :param purchase_order_line: record of `purchase.order.line` Model
        :type purchase_order_line: :py:class:`openerp.models.Model`
        :return: PO location usage
        :rtype: str

        """
        return purchase_order_line.order_id.location_id.usage

    @api.model
    def _route_from_usage(self, usage):
        """Return the routes to assing on SO lines
        based on a location usage.

        If nothing no match return None

        :param usage: stock.location Model usage
        :type usage: str

        :return: a record of `stock.location.route`
        :rtype: :py:class:`openerp.models.Model` or None
        """
        if usage == 'customer':
            return self.env.ref('stock_dropshipping.route_drop_shipping')
        elif usage == 'internal':
            return self.env.ref('stock.route_warehouse0_mto')
        else:
            return None

    @api.one
    @api.onchange('sourced_by')
    @api.constrains('sourced_by')
    def set_route_form_so(self):
        """Set route on SO line based on fields sourced_by.

        Wee look for the PO related
        to current SO line by the sourced_by fields.

        If the PO has a destination location with usage
        "customer" we apply the dropshipping route to current SO line.

        If the PO has a destination location with usage
        "internal" we apply the make to order route to current SO line.

        As there is no trigger decorator that works on
        non computed fields we use constrains decorator instead.
        """
        if not self.sourced_by:
            return
        usage = self._get_po_location_usage(self.sourced_by)
        route = self._route_from_usage(usage)
        self.route_id = route
