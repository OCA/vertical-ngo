# -*- coding: utf-8 -*-
#
#
#    Author: Yannick Vaucher
#    Copyright 2013-2015 Camptocamp SA
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
from .logistic_requisition import LogisticsRequisitionSource


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    requisition_id = fields.Many2one('logistic.requisition',
                                     'Logistics Requisition',
                                     ondelete='restrict',
                                     copy=False)

    @api.multi
    def action_accepted(self):
        """ On acceptation of Cost Estimate, we generate PO
        for all line sourced by a tender

        """
        res = super(SaleOrder, self).action_accepted()
        purchase_line_model = self.env['purchase.order.line']
        purch_req_so_lines = self.mapped('order_line').filtered(
            lambda rec: (rec.sourcing_method == 'procurement'
                         and not rec.sourced_by))
        todo = self.env['purchase.requisition'].browse()
        for line in purch_req_so_lines:
            source = line.lr_source_id
            if not source.purchase_line_id:
                todo |= source.po_requisition_id

        for purch_req in todo:
            purch_req.generate_po()

        for line in purch_req_so_lines:
            line.sourced_by = line.lr_source_id.purchase_line_id
        return res


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    price_is = fields.Selection(
        LogisticsRequisitionSource.PRICE_IS_SELECTION,
        string='Price is',
        help="When the price is an estimation, the final price may change. "
             "I.e. it is not based on a request for quotation.",
        default='fixed')
    lr_source_id = fields.Many2one(
        'logistic.requisition.source',
        'Logistics Requisition Source',
    )
    sourcing_method = fields.Selection(
        related='lr_source_id.sourcing_method',
        selection=[
            ('procurement', 'Tender'),
            ('wh_dispatch', 'Warehouse Dispatch'),
            ('fw_agreement', 'Framework Agreement'),
            ('other', 'Other'),
            ],
    )
    # Replace draft by draftpo in domain
    # This to bridge sale_quotation_sourcing and purchase_rfq_bid_workflow
    sourced_by = fields.Many2one(
        domain="[('product_id', '=', product_id),"
               " ('order_id.state', 'in', ['draftpo', 'confirmed'])]")
