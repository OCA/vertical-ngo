# -*- coding: utf-8 -*-

from openerp.osv import fields, orm


class logistic_requisition_line_cost_estimate(orm.TransientModel):
    _name = 'logistic.requisition.line.cost.estimate'
    _description = 'Create cost estimate of logistic requisition lines'

    def cost_estimate(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        line_ids = context.get('active_ids')
        if not line_ids:
            return
        line_obj = self.pool.get('logistic.requisition.line')
        return line_obj.button_create_cost_estimate(cr, uid, line_ids,
                                                    context=context)
