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


class PurchaseRequisition(models.Model):
    _inherit = "purchase.requisition"
    _description = "Call for Bids"

    consignee_id = fields.Many2one(
        'res.partner',
        'Consignee',
        help="Person responsible of delivery")

    @api.model
    def _prepare_purchase_order(self, requisition, supplier):
        values = super(PurchaseRequisition, self
                       )._prepare_purchase_order(requisition, supplier)
        values['consignee_id'] = requisition.consignee_id.id
        return values
