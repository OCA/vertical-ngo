# -*- coding: utf-8 -*-
#
#
#    Author: Guewen Baconnier
#    Copyright 2013-2014 Camptocamp SA
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
from openerp.osv import orm, fields
from ..model.logistic_requisition import logistic_requisition as base_requisition


class logistic_requisition_cancel(orm.TransientModel):
    """ Ask a reason for the logistic requisition cancellation."""
    _name = 'logistic.requisition.cancel'
    _description = __doc__

    _columns = {
        'reason_id': fields.many2one('logistic.requisition.cancel.reason',
                                     string='Reason',
                                     required=True),
    }

    def confirm_cancel(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        if isinstance(ids, (list, tuple)):
            assert len(ids) == 1, "1 ID expected"
            ids = ids[0]
        act_close = {'type': 'ir.actions.act_window_close'}
        requisition_ids = context.get('active_ids')
        if requisition_ids is None:
            return act_close
        form = self.browse(cr, uid, ids, context=context)
        req_obj = self.pool.get('logistic.requisition')
        req_obj._do_cancel(cr, uid,
                           requisition_ids,
                           form.reason_id.id,
                           context=context)
        return act_close
