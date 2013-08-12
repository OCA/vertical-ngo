# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Guewen Baconnier
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

from collections import namedtuple
from operator import attrgetter
from openerp.osv import orm, fields
from openerp.tools.translate import _
from openerp.tools import float_is_zero
from openerp import SUPERUSER_ID


CompletedLine = namedtuple('CompletedLine',
                           ('requisition_line',
                            'purchase_line',
                            'newline',
                            'quantity',
                           ))


class purchase_requisition(orm.Model):
    _inherit = 'purchase.requisition'

    _columns = {
        'logistic_requisition_line_ids': fields.one2many(
            'logistic.requisition.line', 'po_requisition_id',
            string='Logistic Requisition Lines',
            readonly=True),
    }

    def generate_po(self, cr, uid, ids, context=None):
        result = super(purchase_requisition, self).generate_po(
            cr, uid, ids, context=context)
        assert len(ids) == 1, "generate_po accepts only 1 ID, got: %s" % ids
        purch_req = self.browse(cr, uid, ids[0], context=context)
        requisition_lines = purch_req.logistic_requisition_line_ids
        if not requisition_lines:
            return result
        all_po_lines = purch_req.po_line_ids
        assert all_po_lines, "Expected to have lines in the purchase order, got no lines"

        all_po_lines = sorted(all_po_lines,
                              key=attrgetter('quantity_bid'),
                              reverse=True)
        requisition_lines = sorted(requisition_lines,
                                   key=attrgetter('proposed_qty'),
                                   reverse=True)
        # requisition lines linked with the purchase order line and
        # completed with the final quantity
        dp_obj = self.pool.get('decimal.precision')
        precision = dp_obj.precision_get(cr, SUPERUSER_ID,
                                         'Product Unit of Measure')
        completed_items = []
        for rline in requisition_lines[:]:
            remaining = rline.proposed_qty
            newline = False
            po_lines = [po_line for po_line in all_po_lines
                        if rline == po_line.requisition_line_id.logistic_requisition_line_id]
            for po_line in po_lines:

                if rline.product_id != po_line.product_id:
                    raise orm.except_orm(
                        _('Error'),
                        _("The product is not the same between the purchase "
                          "order line and the logistic requisition line. "
                          "This is not supported."))
                if rline.requested_uom_id != po_line.product_uom:
                    raise orm.except_orm(
                        _('Error'),
                        _("The unit of measure is not the same between "
                          "the purchase order line and the logistic "
                          "requisition line. This is not supported."))

                current_rest = remaining - po_line.quantity_bid
                if (float_is_zero(current_rest, precision_digits=precision) or
                        po_line.quantity_bid > remaining):
                    current = CompletedLine(requisition_line=rline,
                                            purchase_line=po_line,
                                            newline=newline,
                                            quantity=po_line.quantity_bid)
                    completed_items.append(current)
                    remaining = 0.
                else:
                    current = CompletedLine(requisition_line=rline,
                                            purchase_line=po_line,
                                            newline=newline,
                                            quantity=po_line.quantity_bid)
                    completed_items.append(current)
                    remaining = current_rest
                # the current req. line is completed, so
                # if we have another purchase line or a remaining
                # quantity, we will need to create a new line
                newline = True
            assert float_is_zero(remaining, precision), (
                "All the quantity should have been purchased, rest: %f" %
                remaining)

        req_line_obj = self.pool.get('logistic.requisition.line')
        for item in completed_items:
            vals = {'proposed_qty': item.quantity,
                    'price_is': 'fixed',
                    'unit_cost': item.purchase_line.price_unit,
                    'purchase_line_id': item.purchase_line.id,
                    }

            if item.newline:
                origin = item.requisition_line
                new_vals = vals.copy()
                new_vals.update({
                    'state': origin.state,
                    'logistic_user_id': origin.logistic_user_id.id,
                    'requested_qty': origin.requested_qty,
                    'po_requisition_id': origin.po_requisition_id.id,
                    'date_eta': origin.date_eta,
                    'date_etd': origin.date_etd,
                    'cost_estimate_id': origin.cost_estimate_id.id,
                    'transport_plan_id': origin.transport_plan_id.id,
                })
                req_line_obj.copy(cr, uid,
                                  item.requisition_line.id,
                                  default=new_vals,
                                  context=context)
            else:
                item.requisition_line.write(vals)
        return result


class purchase_requisition_line(orm.Model):
    _inherit = 'purchase.requisition.line'
    _columns = {
        'logistic_requisition_line_id': fields.many2one(
            'logistic.requisition.line',
            string='Logistic Requisition Line',
            readonly=True),
    }
