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
from openerp.osv import orm, fields
from openerp.tools.translate import _


ToAssignLine = namedtuple('ToAssignLine',
                          ('line',
                           'new_line',
                           'quantity'))


AssignedLine = namedtuple('AssignedLine',
                          ('line',  # existing line of logistic.requisition.line
                           'new_line',  # True if a new line should be created
                                        # instead of using the `line`
                           'quantity',  # quantity of products assigned
                           'purchase_line'  # purchase.order.line linked
                           ))



class purchase_requisition(orm.Model):
    _inherit = 'purchase.requisition'

    _columns = {
        'logistic_requisition_line_ids': fields.one2many(
            'logistic.requisition.line', 'po_requisition_id',
            string='Logistic Requisition Lines',
            readonly=True),
    }

    def generate_po(self, cr, uid, id, context=None):
        result = super(purchase_requisition, self).generate_po(
            cr, uid, id, context=context)
        assert len(id) == 1, "generate_po accept only 1 ID"
        purch_req = self.browse(cr, uid, id[0], context=context)
        requisition_lines = purch_req.logistic_requisition_line_ids
        if not requisition_lines:
            return result

        complete = []
        to_assign = []
        for line in requisition_lines:
            if line.purchase_line_id:
                continue  # skip lines already assigned to a purchase line
            product_id = line.product_id.id
            to_assign.append(ToAssignLine(line=line,
                                          new_line=False,
                                          quantity=line.requested_qty))

        purch_orders = [po for po in purch_req.purchase_ids
                        if po.state == 'draftpo']
        po_lines = [line for purch in purch_orders
                    for line in purch.order_line]

        for po_line in po_lines:
            for req_line in to_assign[:]:
                if req_line.line.product_id != po_line.product_id:
                    continue
                # TODO: conversion of uom to implement
                if req_line.line.requested_uom_id != po_line.product_uom:
                    raise orm.except_orm(
                        _('Error'),
                        _('Different unit of measure are not supported.'))
                if req_line.quantity <= po_line.quantity_bid:
                    assigned_line = AssignedLine(
                        line=req_line.line,
                        new_line=req_line.new_line,
                        quantity=req_line.quantity,
                        purchase_line=po_line)
                    if req_line.quantity < po_line.quantity_bid:
                        # TODO: deal with the extra qty
                        pass
                    to_assign.remove(req_line)
                    complete.append(assigned_line)
                    break
                elif req_line.quantity > po_line.quantity_bid:
                    assigned_qty = po_line.quantity_bid
                    remaining_qty = req_line.quantity - assigned_qty
                    assigned_line = AssignedLine(
                        line=req_line.line,
                        new_line=req_line.new_line,
                        quantity=assigned_qty,
                        purchase_line=po_line)
                    remaining_line = ToAssignLine(
                        line=req_line.line,
                        new_line=True,
                        quantity=remaining_qty)
                    to_assign.remove(req_line)
                    to_assign.append(remaining_line)
                    complete.append(assigned_line)
                    break

        for assigned in complete:
            vals = {'requested_qty': assigned.quantity,
                    'proposed_qty': assigned.quantity,
                    'price_is': 'fixed',
                    'unit_cost': assigned.purchase_line.price_unit,
                    'purchase_line_id': assigned.purchase_line.id,
                    }

            if assigned.new_line:
                req_line_obj = self.pool.get('logistic.requisition.line')
                new_vals = vals.copy()
                new_vals.update({'state': assigned.line.state})
                # TODO use the split wizard
                req_line_obj.copy(cr, uid,
                                  assigned.line.id,
                                  default=new_vals,
                                  context=context)
            else:
                assigned.line.write(vals)

        return result
