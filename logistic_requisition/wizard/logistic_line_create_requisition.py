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

from openerp.osv.orm import TransientModel
from openerp.osv import fields, osv
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp

class LogisticRequisitionLineCreateRequisition(TransientModel):
    _name = "logistic.requisition.line.create.requisition"
    _description = "Create Purchase Requisition From Request Line"

    def create_po_requisition(self, cr, uid, ids, context=None):
        line_obj = self.pool.get('logistic.requisition.line')
        if context is None:
            context = {}
        requisition_id = line_obj._action_create_po_requisition(cr, uid, context.get('active_ids',[]), context)
        return {
            # 'domain': "[('id','=', "requisition_id")]",
            'name': _('Purchase Requisition'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'purchase.requisition',
            'res_id': requisition_id,
            'view_id': False,
            'type': 'ir.actions.act_window',
        }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
