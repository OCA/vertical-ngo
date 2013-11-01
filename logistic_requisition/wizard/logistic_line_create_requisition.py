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

from openerp.osv import orm
from openerp.tools.translate import _


class LogisticRequisitionSourceCreateRequisition(orm.TransientModel):
    _name = "logistic.requisition.source.create.requisition"
    _description = "Create Purchase Requisition From Requisition Source"

    def create_po_requisition(self, cr, uid, ids, context=None):
        source_obj = self.pool.get('logistic.requisition.source')
        requisition_id = source_obj._action_create_po_requisition(
            cr, uid, context.get('active_ids', []), context=context)
        return {
            'name': _('Purchase Requisition'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'purchase.requisition',
            'res_id': requisition_id,
            'view_id': False,
            'type': 'ir.actions.act_window',
        }
