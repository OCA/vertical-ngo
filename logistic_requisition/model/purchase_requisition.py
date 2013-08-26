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
from openerp.tools import float_compare
from openerp import SUPERUSER_ID


# Used for the split of the requisition lines from purchase lines.
# Each requisition line is associated with a purchase line and
# its new quantity. `newline` is a boolean defining if the requisition
# line should be a new line or if we have to keep the existing one
# (a newline will be a split of the `requisition_line`).
CompletedItem = namedtuple('CompletedItem',
                           ('requisition_source',
                            'purchase_line',
                            'newline',
                            'quantity',
                           ))


class purchase_requisition(orm.Model):
    _inherit = 'purchase.requisition'

    _columns = {
        'logistic_requisition_source_ids': fields.one2many(
            'logistic.requisition.source', 'po_requisition_id',
            string='Logistic Requisition Sourcing Lines',
            readonly=True),
    }

    def _prepare_split_logistic_source(self, cr, uid, purchase_requisition, context=None):
        """ Prepare the split of the logistic requisition lines
        according to the selected lines """
        req_sources = purchase_requisition.logistic_requisition_source_ids
        if not req_sources:
            return []
        all_po_lines = [line for line in purchase_requisition.po_line_ids
                        if line.state == 'confirmed' and line.quantity_bid]
        assert all_po_lines, "Expected to have lines in the purchase order, got no lines"

        all_po_lines = sorted(all_po_lines,
                              key=attrgetter('quantity_bid'),
                              reverse=True)
        req_sources = sorted(req_sources,
                             key=attrgetter('proposed_qty'),
                             reverse=True)
        # requisition lines linked with the purchase order line and
        # completed with the final quantity
        dp_obj = self.pool.get('decimal.precision')
        precision = dp_obj.precision_get(cr, SUPERUSER_ID,
                                         'Product Unit of Measure')
        completed_items = []
        for sline in req_sources[:]:
            remaining = sline.proposed_qty
            newline = False
            po_lines = [po_line for po_line in all_po_lines
                        if sline == po_line.requisition_line_id.logistic_requisition_source_id]
            for po_line in po_lines:

                req_line = sline.requisition_line_id
                if req_line.product_id != po_line.product_id:
                    raise orm.except_orm(
                        _('Error'),
                        _("The product is not the same between the purchase "
                          "order line and the logistic requisition line %s. "
                          "This is not supported.") % sline.name)
                if req_line.requested_uom_id != po_line.product_uom:
                    raise orm.except_orm(
                        _('Error'),
                        _("The unit of measure is not the same between "
                          "the purchase order line and the logistic "
                          "requisition line %s. This is not supported.") %
                        sline.name)

                remaining = remaining - po_line.quantity_bid
                current = CompletedItem(requisition_source=sline,
                                        purchase_line=po_line,
                                        newline=newline,
                                        quantity=po_line.quantity_bid)
                completed_items.append(current)
                # the current req. line is completed, so
                # if we have another purchase line or a remaining
                # quantity, we will need to create a new line
                newline = True

            # returns 1 if left value is more than right value (`0` here)
            compare = float_compare(remaining, 0,
                                    precision_digits=precision)
            if compare == 1:
                # the selected quantity in purchase lines is less
                # than the requested quantity
                rest_item = CompletedItem(requisition_source=sline,
                                          purchase_line=None,
                                          newline=newline,
                                          quantity=remaining)
                completed_items.append(rest_item)
        return completed_items

    def _split_completed_items(self, cr, uid, id, context=None):
        """ Effectively split the logistic requisition source lines

        :param completed_items: list of CompletedItem instances
        """
        if isinstance(id, (tuple, list)):
            assert len(id) == 1, (
                "_split_completed_items() accepts only 1 ID, "
                "got: %s" % id)
            id = id[0]
        purchase_requisition = self.browse(cr, uid, id, context=context)
        completed_items = self._prepare_split_logistic_source(
            cr, uid, purchase_requisition, context=context)
        req_source_obj = self.pool.get('logistic.requisition.source')
        for item in completed_items:
            vals = {'price_is': 'fixed',
                    'proposed_qty': item.quantity,
                    }
            if item.purchase_line is not None:
                vals.update({
                    'unit_cost': item.purchase_line.price_unit,
                    'bid_line_id': item.purchase_line.id,
                })

            if item.newline:
                origin = item.requisition_source
                default_vals = {
                    'proposed_qty': item.quantity,
                    'date_eta': origin.date_eta,
                    'date_etd': origin.date_etd,
                    'transport_applicable': origin.transport_applicable,
                }
                if origin.transport_plan_id:
                    default_vals['transport_plan_id'] = origin.transport_plan_id.id
                # line_id = origin.split(item.quantity)
                line_id = req_source_obj.copy(cr, uid, origin.id,
                                              default=default_vals,
                                              context=context)
                vals.update({
                    'po_requisition_id': origin.po_requisition_id.id,
                })
            else:
                line_id = item.requisition_source.id
            req_source_obj.write(cr, uid, [line_id], vals, context=context)

    def close_callforbids_ok(self, cr, uid, ids, context=None):
        """ We have to split the logistic requisition lines according to
        the selected lines after the selection of the lines, when we
        click on the 'Confirm selection of lines'.
        """
        result = super(purchase_requisition, self).close_callforbids_ok(
            cr, uid, ids, context=context)
        self._split_completed_items(cr, uid, ids, context=context)
        return result

    def _prepare_po_line_from_tender(self, cr, uid, tender, line,
                                     purchase_id, context=None):
        """ Prepare the values to write in the purchase order line
        created for a line of the tender.

        :param tender: the source tender from which we generate a purchase order
        :param line: the source tender's line from which we generate a line
        :param purchase_id: the id of the new purchase
        """
        vals = super(purchase_requisition, self)._prepare_po_line_from_tender(
            cr, uid, tender, line, purchase_id, context=context)
        vals['from_bid_line_id'] = line.id
        return vals


class purchase_requisition_line(orm.Model):
    _inherit = 'purchase.requisition.line'
    _columns = {
        'logistic_requisition_source_id': fields.many2one(
            'logistic.requisition.source',
            string='Logistic Requisition Source Line',
            readonly=True),
    }
