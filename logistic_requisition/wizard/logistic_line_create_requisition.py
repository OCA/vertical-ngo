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

from openerp.tools.translate import _
from openerp.osv import fields, orm


class LogisticRequisitionSourceCreateRequisition(orm.TransientModel):
    _name = "logistic.requisition.source.create.requisition"
    _description = "Create Purchase Requisition From Requisition Source"


    _columns = {
        'pricelist_id': fields.many2one('product.pricelist',
                                          string='Pricelist / Currency',
                                          required=True),
    }

    def default_get(self, cr, uid, fields_list, context=None):
        """Take the first line pricelist as default"""
        if context is None:
            context = {}
        defaults = super(LogisticRequisitionSourceCreateRequisition, self).\
            default_get(cr, uid, fields_list, context=context)
        line_obj = self.pool.get('logistic.requisition.source')
        line_ids = context['active_ids']
        pricelist_id = None
        line = line_obj.browse(cr, uid, line_ids, context=context)[0]
        pricelist_id = line_obj._get_purchase_pricelist_from_currency(
                cr,
                uid,
                line.requisition_id.pricelist_id.currency_id.id,
                context=context
                )
        defaults['pricelist_id'] = pricelist_id
        return defaults

    def create_po_requisition(self, cr, uid, ids, context=None):
        form = self.browse(cr, uid, ids, context=context)[0]
        source_obj = self.pool.get('logistic.requisition.source')
        requisition_id = source_obj._action_create_po_requisition(
            cr, uid, context.get('active_ids', []), 
            pricelist=form.pricelist_id.id, context=context)
        return {
            'name': _('Purchase Requisition'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'purchase.requisition',
            'res_id': requisition_id,
            'view_id': False,
            'type': 'ir.actions.act_window',
        }
