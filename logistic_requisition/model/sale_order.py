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

    lr_count = fields.Integer(
        compute='_count_logistic_requisition'
    )
    lr_source_count = fields.Integer(
        compute='_count_lr_source'
    )
    lr_purchase_count = fields.Integer(
        compute='_count_lr_purchase'
    )

    @api.multi
    def action_accepted(self):
        """ On acceptation of Cost Estimate, we generate PO
        for all line sourced by a tender

        """
        res = super(SaleOrder, self).action_accepted()
        purch_req_so_lines = self.mapped('order_line').filtered(
            lambda rec: (rec.sourcing_method == 'procurement'
                         and not rec.sourced_by))
        # As multiple source lines can lead to the same purchase
        # requisition. First we list them. And then we generate
        # PO only once for each purchase requisition.
        todo = self.env['purchase.requisition']
        for line in purch_req_so_lines:
            source = line.lr_source_id
            if not source.purchase_line_id:
                todo |= source.po_requisition_id

        for purch_req in todo:
            purch_req.generate_po()

        for line in purch_req_so_lines:
            line.sourced_by = line.lr_source_id.purchase_line_id
        return res

    @api.multi
    def _get_relevant_purchases(self):
        sourced_lines = self.order_line.filtered(lambda rec: rec.sourced_by)
        purchases = sourced_lines.mapped('sourced_by.order_id')

        if self.state == 'draft':
            # If line is not sourced and is tender,
            # check for existing bid
            unsourced_lines = self.order_line - sourced_lines
            unsourced_lines = unsourced_lines.filtered(
                lambda rec: rec.sourcing_method == 'procurement')
            bids = unsourced_lines.mapped('lr_source_id.selected_bid_id')
            purchases |= bids
        return purchases

    @api.one
    @api.depends('requisition_id')
    def _count_logistic_requisition(self):
        """ Set lr_count field """
        self.lr_count = len(self.requisition_id)

    @api.one
    @api.depends('order_line.lr_source_id')
    def _count_lr_source(self):
        """ Set lr_source_count field """
        sources = self.order_line.mapped('lr_source_id')
        self.lr_source_count = len(sources)

    @api.one
    @api.depends('order_line.sourced_by',
                 'order_line.lr_source_id.selected_bid_id')
    def _count_lr_purchase(self):
        """ Set lr_purchase_count field """
        purchases = self._get_relevant_purchases()
        self.lr_purchase_count = len(purchases)

    @api.multi
    def action_open_logistic_requisition(self):
        action_ref = 'logistic_requisition.action_logistic_requisition'
        action_dict = self.env.ref(action_ref).read()[0]
        action_dict['domain'] = [('id', 'in', [self.requisition_id.id])]
        return action_dict

    @api.multi
    def action_open_lr_sources(self):
        action_ref = 'logistic_requisition.action_logistic_requisition_source'
        action_dict = self.env.ref(action_ref).read()[0]
        sources = self.order_line.mapped('lr_source_id')
        action_dict['domain'] = [('id', 'in', sources.ids)]
        return action_dict

    @api.multi
    def action_open_lr_purchases(self):
        """ Open Bids and Purchase order sourcing this cost estimate """
        self.ensure_one()
        action_ref = 'purchase.purchase_form_action'
        action_dict = self.env.ref(action_ref).read()[0]
        purchases = self._get_relevant_purchases()
        action_dict['domain'] = [('id', 'in', purchases.ids)]
        del action_dict['help']

        return action_dict


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
