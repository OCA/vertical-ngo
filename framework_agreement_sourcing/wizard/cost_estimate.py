# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Nicolas Bessi
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
##############################################################################
from openerp.osv import orm
from openerp.tools.translate import _


class logistic_requisition_cost_estimate(orm.TransientModel):

    """Add update of agreement price"""

    _inherit = "logistic.requisition.cost.estimate"

    def _prepare_cost_estimate_line(self, cr, uid, sourcing, context=None):
        """Override in order to update agreement source line

        """
        res = super(logistic_requisition_cost_estimate,
                    self)._prepare_cost_estimate_line(cr, uid, sourcing,
                                                      context=context)

        if sourcing.sourcing_method == 'fw_agreement':
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

        so_lines = [x for x in so.order_line if x.product_id]
        po_lines = set(x.purchase_line_id for x in sources
                       if x.purchase_line_id)
        product_dict = dict((x.product_id.id, x.id) for x in so_lines
                            if x.product_id)
        default = product_dict[product_dict.keys()[0]]
        if not product_dict:
            raise orm.except_orm(_('No stockable product in related PO'),
                                 _('Please add one'))
        for po_line in po_lines:
            key = po_line.product_id.id if po_line.product_id else False
            po_line.write(
                {'sale_order_line_id': product_dict.get(key, default)})

    def cost_estimate(self, cr, uid, ids, context=None):
        """Override to link PO to cost_estimate$

        In a normal flow, when you chose a bid as the winning one, the bid is
        dupplicated to generate the draft PO. On this action, it link the LRS
        to the generated PO line.

        In a tender flow, we don't dupplicate the bid, it's only a PO. The link
        between the LRS and the PO line should then be created here.

        This is for the drop shipping to work propely cause in that case, SO
        and PO are linked together.
        """
        so_model = self.pool['sale.order']
        po_model = self.pool['purchase.order']

        assert len(ids) == 1

        wizard = self.browse(cr, uid, ids, context=context)

        res = super(logistic_requisition_cost_estimate,
                    self).cost_estimate(cr, uid, ids, context=context)
        so_id = res['res_id']
        order = so_model.browse(cr, uid, so_id, context=context)

        sources = []

        for lrl in wizard.line_ids:
            for source in lrl.source_ids:
                if source.sourcing_method == 'fw_agreement':
                    sources.append(source)

        po_ids = set(x.purchase_line_id.order_id.id for x in sources
                     if x.purchase_line_id)
        if po_ids:
            po_model.write(cr, uid, list(po_ids),
                           {'sale_id': so_id,
                            'sale_flow': 'direct_delivery'})
            self._link_po_lines_to_so_lines(
                cr, uid, order, sources, context=context)
        return res
