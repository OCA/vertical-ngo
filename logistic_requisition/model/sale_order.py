# -*- coding: utf-8 -*-
#
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
#
from openerp import models, fields, api
from .logistic_requisition import LogisticRequisitionSource


# TODO: We want to deconnect the SO from the LR and LRS. The goal would be
# to be able to create manually a SO (cost estimate) withou using the wizard
# from an LRL. So, if I provide all the needed infos and link to other documents
# it should work.

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    requisition_id = fields.Many2one('logistic.requisition',
                                     'Logistic Requisition',
                                     ondelete='restrict',
                                     copy=False)


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    logistic_requisition_source_id = fields.Many2one(
        'logistic.requisition.source',
        'Requisition Source',
        ondelete='restrict')
    price_is = fields.Selection(
        LogisticRequisitionSource.PRICE_IS_SELECTION,
        string='Price is',
        help="When the price is an estimation, the final price may change. "
             "I.e. it is not based on a request for quotation.",
        default='fixed')
    account_code = fields.Char('Account Code', size=32)

    # TODO: The purchase_requisition from where to generate
    # the draft PO should in v8 be taken from a link on the SO line.
    # We should not get back to the LRS for that.
    @api.multi
    def button_confirm(self):
        """ When a sale order is confirmed, we'll also generate the
        purchase order on the purchase requisition of the logistic
        requisition which has created the sales order lines.

        E.g.
        I create a logistic requisition with 2 lines.
        On each line, I create a purchase requisition, I select the
        purchase lines and confirm the selection.
        Then, a sales order is generated from the logistic requisition, a line
        is created for each logistic requisition line.
        When this sale order is confirmed, for each line, I have to go
        back to the logistic requisition line, and generate the purchase
        order for the purchase requisition.
        """
        result = super(SaleOrderLine, self).button_confirm()
        purchase_requisitions = set()
        for line in self:
            source = line.logistic_requisition_source_id
            if not source:
                continue
            # TODO : Take that link from SO Line
            purchase_req = source.po_requisition_id
            if purchase_req:
                purchase_requisitions.add(purchase_req)
        # Beware! generate_po() accepts a list of ids, but discards the
        # ids > 1.
        # We can't call it 2 times on a purchase_requisition,
        # and 2 lines may have the same one.
        for purchase_requisition in purchase_requisitions:
            purchase_requisition.generate_po()
        return result
