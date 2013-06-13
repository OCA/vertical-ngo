# -*- coding: utf-8 -*-
##############################################################################
#
#    Author:  Joël Grand-Guillaume
#    Copyright 2013 Camptocamp SA
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more description.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import fields, osv, orm
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp


class LogisticRequisitionSplitLine(orm.TransientModel):
    _name = "logistic.requisition.split.line"
    _description = "Split Requisition Line"
    _columns = {
        'quantity': fields.float('Quantity',
                                 digits_compute=dp.get_precision('Product Unit of Measure')),
    }

    _defaults = {
        'quantity': 0,
    }

    def split(self, cr, uid, data, context=None):
        if context is None:
            context = {}
        rec_id = context.get('active_ids')
        if not rec_id:
            return
        line_obj = self.pool.get('logistic.requisition.line')
        quantity = self.browse(cr, uid, data[0], context=context).quantity or 0.0
        if not quantity:
            return
        if quantity < 0:
            raise osv.except_osv(_('Error'),
                                 _('Please provide a positive quantity '
                                   'to leave.'))

        for line in line_obj.browse(cr, uid, rec_id, context=context):
            if quantity == line.requested_qty:
                continue

            elif quantity > line.requested_qty:
                raise osv.except_osv(_('Error'),
                                     _('Total quantity after split exceeds '
                                       'the quantity to split for this line: '
                                       '"%s".') % line.description)

            quantity_rest = line.requested_qty - quantity

            budget_value = (line.budget_tot_price / line.requested_qty) * quantity
            line_obj.write(cr, uid, [line.id], {
                'requested_qty': quantity,
                'budget_tot_price': budget_value,
            })

            default_val = {
                'requested_qty': quantity_rest,
                'budget_tot_price': line.budget_tot_price - budget_value,
                'state': line.state,
                'logistic_user_id': line.logistic_user_id.id,
            }
            # TODO: Think to implement messaging posting on new
            # generated line, we want to explicit that we split the
            # line, warn the concerned users about it, etc..
            current_line = line_obj.copy(cr, uid, line.id,
                                         default=default_val,
                                         context=context)
        return {'type': 'ir.actions.act_window_close'}
