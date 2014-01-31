# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Nicolas Bessi
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


class logistic_requisition_source_po_creator(orm.TransientModel):

    _name = 'logistic.requisition.source.create.agr.po'

    _columns = {
        'pricelist_id': fields.many2one('product.pricelist',
                                          string='Pricelist / Currency',
                                          required=True),
    }

    def _make_purchase_order(self, cr, uid, pricelist, source_ids, context=None):
        """Create PO from source line ids"""
        lr_model = self.pool['logistic.requisition.source']
        po_id = lr_model.make_purchase_order(cr, uid, source_ids,
                                              pricelist, context=context)
        return po_id

    def action_create_agreement_po_requisition(self, cr, uid, ids, context=None):
        """ Implement buttons that create PO from selected source lines"""
        act_obj = self.pool['ir.actions.act_window']
        source_ids = context['active_ids']
        pricelist = None # place holder for Joel pl browse record
        po_id = self._make_purchase_order(cr, uid, pricelist, source_ids,
                                           context=context)
        # TODO : update LRS price from PO depending on the chosen currency
        
        res = act_obj.for_xml_id(cr, uid,
                                 'purchase', 'purchase_rfq', context=context)
        res.update({'domain': [('id', '=', po_id)],
                    'res_id': po_id,
                    'context': '{}',
                    'search_view_id': False,
                    })
        return res
