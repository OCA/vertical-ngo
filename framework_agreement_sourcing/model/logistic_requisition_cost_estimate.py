# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Nicolas Bessi
#    Copyright 2013 Camptocamp SA
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
from openerp.osv import orm
from openerp.tools.translate import _
from .logistic_requisition_source import AGR_PROC


class logistic_requisition_cost_estimate(orm.Model):
    """Add update of agreement price"""

    _inherit = "logistic.requisition.cost.estimate"

    def _update_agreement_source(self, cr, uid, source, context=None):
        """Update price of source line using related confirmed PO"""
        if source.procurement_method == AGR_PROC:
            self._link_po_lines_to_source(cr, uid, source, context=context)
            price = source.get_agreement_price_from_po()
            source.write({'unit_cost': price})
            source.refresh()

    def _link_po_lines_to_source(self, cr, uid, source, context=None):
        po_l_obj = self.pool['purchase.order.line']
        agr = source.framework_agreement_id
        line_ids = po_l_obj.search(
            cr, uid,
            [('order_id.framework_agreement_id', '=', agr.id),
             ('lr_source_line_id', '=', source.id),
             ('order_id.partner_id', '=', agr.supplier_id.id)],
            context=context)
        lines = po_l_obj.browse(cr, uid, line_ids, context=context)
        po_ids = ([line.order_id.id for line in lines
                   if line.product_id and line.product_id.type == 'product'])

        all_line_ids = po_l_obj.search(
            cr, uid,
            [('order_id', 'in', po_ids),
             ('product_id.type', '=', 'product')],
            context=context)

        po_l_obj.write(cr, uid, all_line_ids,
                       {'lr_source_line_id': source.id},
                       context=context)
        source.refresh()

    def _prepare_cost_estimate_line(self, cr, uid, sourcing, context=None):
        """Override in order to update agreement source line

        We update the price of source line that will be used in cost estimate

        """
        self._update_agreement_source(cr, uid, sourcing, context=context)
        res = super(logistic_requisition_cost_estimate,
                    self)._prepare_cost_estimate_line(cr, uid, sourcing,
                                                      context=context)

        if sourcing.procurement_method == AGR_PROC:
            res['type'] = 'make_to_order'
            res['sale_flow'] = 'direct_delivery'
        return res

    def _link_po_lines_to_so_lines(self, cr, uid, so, sources, context=None):
        """Naive implementation to link all PO lines to SO lines.

        For our actuall need we want to link all service line
        to SO real product lines.

        There should not be twice the same product on differents
        Agreement PO line so this case in not handled

        """

        so_lines = [x for x in so.order_line]
        po_lines = set(x.purchase_line_id for x in sources
                       if x.purchase_line_id and
                          x.purchase_line_id.product_id.type == 'product')
        product_dict = dict((x.product_id.id, x.id) for x in so_lines
                            if x.product_id and x.product_id.type == 'product')
        default = product_dict[product_dict.keys()[0]]
        if not product_dict:
            raise orm.except_orm(_('No stockable product in related PO'),
                                 _('Please add one'))
        for po_line in po_lines:
            key = po_line.product_id.id if po_line.product_id else False
            po_line.write({'sale_order_line_id': product_dict.get(key, default)})

    def cost_estimate(self, cr, uid, ids, context=None):
        """Override to link PO to cost_estimate

        We have to do this because when we source with agreement we do
        not copy the PO it is meaningless has we have no choice to make.
        But in tender flow you first cancel PO then the sale order mark
        canceled PO as dropshipping and then copy them.

        So you have to create link between SO and PO/PO line that are
        normally done when SO procurement generate PO and picking


        With agreement PO is confirmed before be marked as dropshipping.

        So we have to link it first"""
        so_model = self.pool['sale.order']
        po_model = self.pool['purchase.order']
        res = super(logistic_requisition_cost_estimate,
                    self).cost_estimate(cr, uid, ids, context=context)
        so_id = res['res_id']
        order = so_model.browse(cr, uid, so_id, context=context)
        # Can be optimized with a SQL or a search but
        # gain of perfo will not worth readability loss
        # for such small data set
        sources = [x.logistic_requisition_source_id for x in order.order_line
                   if x and x.logistic_requisition_source_id.procurement_method == AGR_PROC]
        po_ids = set(x.purchase_line_id.order_id.id for x in sources
                     if x.purchase_line_id)
        po_model.write(cr, uid, list(po_ids),
                       {'sale_id': so_id,
                        'sale_flow': 'direct_delivery'})
        self._link_po_lines_to_so_lines(cr, uid, order, sources, context=context)
        return res
