# -*- coding: utf-8 -*-

from openerp.osv import fields, orm


class logistic_requisition_line_assign(orm.TransientModel):
    _name = 'logistic.requisition.line.assign'
    _description = 'Assign a logistic requisition line'

    _columns = {
        'logistic_user_id': fields.many2one(
            'res.users',
            'Logistic Specialist',
            required=True,
            help="Logistic Specialist in charge of the "
                 "Logistic Requisition Line"),
    }

    def assign(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        line_ids = context.get('active_ids')
        if not line_ids:
            return
        form = self.browse(cr, uid, ids[0], context=context)
        line_obj = self.pool.get('logistic.requisition.line')
        line_obj.write(cr, uid, line_ids,
                       {'logistic_user_id': form.logistic_user_id.id},
                       context=context)
        return {'type': 'ir.actions.act_window_close'}
