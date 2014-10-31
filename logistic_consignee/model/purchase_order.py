# -*- coding: utf-8 -*-
#
#
#    Author: Yannick Vaucher
#    Copyright 2014 Camptocamp SA
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


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    consignee_id = fields.Many2one(
        'res.partner', 'Consignee',
        help="The person to whom the shipment is to be delivered.")

    @api.multi
    def action_picking_create(self):
        """ Propagate value of consignee_id to the created picking """
        res = super(PurchaseOrder, self).action_picking_create()

        for order in self:
            order.picking_ids.write({'consignee_id': order.consignee_id.id})
        return res
