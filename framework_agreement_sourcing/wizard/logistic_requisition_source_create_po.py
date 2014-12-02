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
from openerp.tools.translate import _
from openerp.exceptions import except_orm


class logistic_requisition_source_po_creator(orm.TransientModel):

    _name = 'logistic.requisition.source.create.agr.po'

    _columns = {
        'pricelist_id': fields.many2one('product.pricelist',
                                        string='Pricelist / Currency',
                                        required=True),
        'framework_currency_ids': fields.many2many(
            'framework.agreement.pricelist',
            rel='framework_agr_id_po_create_rel',
            string='Available Currency',
            readonly=True)
    }

    def _get_source_ids(self, cr, uid, context=None):
        if context is None:
            context = {}
        if context.get('active_model') == 'logistic.requisition.source':
            source_ids = context['active_ids']
        elif context.get('active_model') == 'logistic.requisition.line':
            line_model = self.pool['logistic.requisition.line']
            line_ids = context['active_ids']
            lines = line_model.browse(cr, uid, line_ids, context=context)
            source_ids = [source.id for line in lines
                          for source in line.source_ids]
        else:
            raise except_orm(_('Wrong active model'),
                             _('This wizard can only be used with '
                               'Logistics Requisition Lines or Sources.'))
        return source_ids

    def default_get(self, cr, uid, fields_list, context=None):
        """ Take the pricelist of the lrs by default. Show the
        available choice for the user.
        """
        defaults = super(logistic_requisition_source_po_creator, self).\
            default_get(cr, uid, fields_list, context=context)
        source_model = self.pool['logistic.requisition.source']
        fmwk_price_obj = self.pool['framework.agreement.pricelist']
        source_ids = self._get_source_ids(cr, uid, context=context)
        pricelist_id = None
        source = next((x for x in source_model.browse(cr, uid, source_ids,
                                                      context=context) if
                      x.framework_agreement_id), None)
        if not source:
            raise except_orm(_('No sourcing line with agreement selected'),
                             _('Please correct selection'))
        pricelist_id = source_model._get_purchase_pricelist_from_currency(
            cr,
            uid,
            source.requisition_id.pricelist_id.currency_id.id,
            context=context
        ).id
        defaults['pricelist_id'] = pricelist_id

        frwk_ids = fmwk_price_obj.search(
            cr, uid,
            [('framework_agreement_id', '=',
              source.framework_agreement_id.id)],
            context=context
        )
        defaults['framework_currency_ids'] = frwk_ids
        return defaults

    def _make_purchase_order(self, cr, uid, pricelist, source_ids,
                             context=None):
        """Create PO from source line ids"""
        lr_model = self.pool['logistic.requisition.source']
        po_id = lr_model.make_purchase_order(cr, uid, source_ids,
                                             pricelist, context=context)
        return po_id

    def action_create_agreement_po_requisition(self, cr, uid, ids,
                                               context=None):
        """ Implement buttons that create PO from selected source lines"""
        act_obj = self.pool['ir.actions.act_window']
        source_ids = self._get_source_ids(cr, uid, context=context)
        if not source_ids:
            raise except_orm(_('No sourcing line Found'),
                             _('No sourcing line were found, '
                               'please create one.'))
        form = self.browse(cr, uid, ids, context=context)[0]
        pricelist = form.pricelist_id

        available_curr = [
            x.currency_id for x in form.framework_currency_ids]
        if available_curr and pricelist.currency_id not in available_curr:
            raise except_orm(_('User Error'), _(
                'You must chose a pricelist that is in the same currency '
                'than one of the available in the framework agreement.'))
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
