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

from openerp.osv import orm, fields


class transport_plan(orm.Model):
    _inherit = 'transport.plan'

    def _get_requisition_id(self, cr, uid, ids, field_name, arg, context=None):
        """ Only 1 requisition is allowed for a transport plan, because
        we can't split the transport's cost estimations between several
        requisitions. So we search for the requisition of the first line
        """
        req_ids = {}
        for plan in self.browse(cr, uid, ids, context=context):
            req_id = False
            if plan.logistic_requisition_line_ids:
                lines = plan.logistic_requisition_line_ids[0]
                req_id = lines.requisition_id.id
            req_ids[plan.id] = req_id
        return req_ids

    def _get_tp_from_lr_line(self, cr, uid, ids, context=None):
        lr_line_obj = self.pool.get('logistic.requisition.line')
        tp_ids = set()
        for line in lr_line_obj.browse(cr, uid, ids, context=context):
            if line.transport_plan_id:
                tp_ids.add(line.transport_plan_id.id)
        return list(tp_ids)

    def _get_product_id(self, cr, uid, context=None):
        data_obj = self.pool.get('ir.model.data')
        try:
            __, res_id = data_obj.get_object_reference(cr, uid,
                                                       'logistic_requisition',
                                                       'product_transport')
        except ValueError:
            return
        else:
            return res_id

    _columns = {
        'logistic_requisition_line_ids': fields.one2many(
            'logistic.requisition.line', 'transport_plan_id',
            string='Logistic Requisition Lines',
            readonly=True),
        'logistic_requisition_id': fields.function(
            _get_requisition_id,
            type='many2one',
            relation='logistic.requisition',
            store={
                'transport.plan': (lambda self, cr, uid, ids, c=None: ids,
                                   ['logistic_requisition_line_ids'], 10),
                'logistic.requisition.line': (_get_tp_from_lr_line,
                                              ['transport_plan_id'],
                                              10),
            },
            string='Requisition'),
        'product_id': fields.many2one(
            'product.product',
            string='Product',
            help='Product used for the transport, '
                 'will be used in the cost estimate')
    }

    _defaults = {
        'product_id': _get_product_id,
    }

    def _logistic_requisition_unique(self, cr, uid, ids, context=None):
        for plan in self.browse(cr, uid, ids, context=context):
            if not plan.logistic_requisition_id:
                continue
            requisition_id = plan.logistic_requisition_id
            for line in plan.logistic_requisition_line_ids:
                if line.requisition_id != requisition_id:
                    return False
        return True

    _constraints = [
        (_logistic_requisition_unique,
         "A transport plan cannot be linked to lines of different "
         "logistic requisitions.",
         ['logistic_requisition_line_ids']),
    ]
