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
    def _generate_tender_pos(self):
        purch_req_so_lines = self.mapped('order_line').filtered(
            lambda rec: (
                rec.sourcing_method == 'procurement' and not rec.sourced_by))
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

    @api.multi
    def _duplicate_reused_bids(self):
        """ Duplicate selected bid """
        reuse_bid_so_lines = self.mapped('order_line').filtered(
            lambda rec: (
                rec.sourcing_method == 'reuse_bid'))
        tocopy = self.env['purchase.order']
        sources_per_bid = {}
        lrl_per_bid = {}
        for line in reuse_bid_so_lines:
            source = line.lr_source_id
            tocopy |= source.selected_bid_id
            bid_id = source.selected_bid_id.id
            if bid_id not in sources_per_bid:
                sources_per_bid[bid_id] = {}
            sources_per_bid[bid_id][source.selected_bid_line_id.id] = source.id
            lrl_per_bid[bid_id] = source.requisition_line_id

        # Copy bid and bid lines to a new draft po
        new_pos = self.env['purchase.order']
        for bid in tocopy:
            from_sources = sources_per_bid[bid.id]
            lrl = lrl_per_bid[bid.id]
            new_po = bid.with_context(reuse_from_source=from_sources).copy()
            data = lrl._prepare_duplicated_bid_data()
            data.update(requisition_id=bid.requisition_id.id)
            new_po.write(data)
            new_po.signal_workflow('draft_po')
            new_pos |= new_po
        po_lines = new_pos.mapped('order_line')

        # Update po lines with values of lr and lrs
        for pol in po_lines:
            source = pol.lr_source_line_id
            # remove purchase line which source nothing
            if not source:
                po_lines -= pol
                pol.unlink()
                continue
            data = source._prepare_duplicated_bid_line_data(pol)
            pol.write(data)

        # Update source_by on sale order lines
        for sol in reuse_bid_so_lines:
            for pol in po_lines:
                if sol.lr_source_id == pol.lr_source_line_id:
                    sol.sourced_by = pol
                    po_lines -= pol
                    break

    @api.multi
    def action_accepted(self):
        """ On acceptation of Cost Estimate, we generate PO
        for all line sourced by a tender

        Plus, we duplicate PO for reused bids

        """
        res = super(SaleOrder, self).action_accepted()
        self._generate_tender_pos()
        self._duplicate_reused_bids()
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
                lambda rec: rec.sourcing_method in ('procurement', 'reuse_bid')
            )
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

    @api.model
    def _get_date_planned(self, order, line, start_date):
        if line.lr_source_id:
            return line.lr_source_id.requisition_line_id.date_delivery
        else:
            return super(SaleOrder, self
                         )._get_date_planned(order, line, start_date)


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
        readonly=True,
    )
    sourcing_method = fields.Selection(
        related='lr_source_id.sourcing_method',
        selection=[
            ('procurement', 'Go to Tender'),
            ('reuse_bid', 'Use Existing Bid'),
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

        if 'price_unit' in res.get('value', {}):
            # warehouse dispatch must be only a transfert of good value
            # for products, we still want to charge services
            if context.get('sourcing_method') == 'wh_dispatch':
                product_model = self.pool['product.product']
                product = product_model.browse(cr, uid, product,
                                               context=context)
                if product.type != 'service':
                    source_id = context.get('lr_source_id')
                    source = self.pool['logistic.requisition.source'].browse(
                        cr, uid, source_id, context=context)
                    if source.requisition_id.requisition_type == 'donor_stock':
                        res['value']['price_unit'] = 0.0
        return res
