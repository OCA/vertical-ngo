# -*- coding: utf-8 -*-
#
#
#    Copyright 2014 Camptocamp SA
#    Author: Yannick Vaucher
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
#
from openerp import models, fields, api
from openerp.tools.translate import _


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.one
    @api.depends('order_type')
    def _get_line_route_id(self):
        """Compute default order line route id"""
        route_id = False
        if self.order_type == 'donation':
            ref = 'logistic_order_donation.route_donation'
            route_id = self.env['ir.model.data'].xmlid_to_res_id(ref)
        self.line_route_id = route_id

    line_route_id = fields.Many2one(
        compute="_get_line_route_id",
        comodel_name='stock.location.route')

    @api.model
    def get_order_type_selection(self):
        selection = super(SaleOrder, self).get_order_type_selection()
        selection.append(('donation', 'In-Kind Donation'))
        return selection


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.one
    def _origin_address(self):
        super(SaleOrderLine, self)._origin_address()
        donation_route = self.env.ref('logistic_order_donation.route_donation')
        if self.route_id == donation_route:
            address = self.order_id.partner_id
            self.origin_address_id = address

    def product_id_change_with_wh(self, cr, uid, ids,
                                  pricelist, product,
                                  qty=0,
                                  uom=False,
                                  qty_uos=0,
                                  uos=False,
                                  name='',
                                  partner_id=False,
                                  lang=False,
                                  update_tax=True,
                                  date_order=False,
                                  packaging=False,
                                  fiscal_position=False,
                                  flag=False,
                                  warehouse_id=False,
                                  context=None):
        res = super(SaleOrderLine, self).product_id_change_with_wh(
            cr, uid, ids,
            pricelist, product, qty, uom,
            qty_uos, uos, name, partner_id,
            lang, update_tax, date_order,
            packaging, fiscal_position, flag,
            warehouse_id,
            context=context)
        # use web_context_tunnel
        if context.get('order_type') == 'donation' and res['warning']:
            warning = res['warning']['message']
            warning_start = warning.find(_("Not enough stock ! : "))
            if warning_start != -1:
                warning_end = warning.find('\n\n', warning_start) + 2
                warning = warning[:warning_start] + warning[warning_end:]
                if warning:
                    res['warning']['message'] = warning
                else:
                    del res['warning']

        if 'price_unit' in res.get('value', {}):
            if context.get('order_type') == 'donation':
                product_model = self.pool['product.product']
                product = product_model.browse(cr, uid, product,
                                               context=context)
                if product.type != 'service':
                    res['value']['price_unit'] = 0.0
        return res
