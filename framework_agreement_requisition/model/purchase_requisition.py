# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Nicolas Bessi
#    Copyright 2013, 2014 Camptocamp SA
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
from itertools import chain
from openerp.osv import orm, fields
from openerp.tools.translate import _
from openerp import models, api
from .purchase import AGR_SELECT as PO_AGR_SELECT

SELECTED_STATE = ('agreement_selected', 'Agreement selected')
AGR_SELECT = 'agreement_selected'


class PurchaseRequisition(models.Model):

    _inherit = "purchase.requisition"

    @api.multi
    def open_wizard_confirm_generate_agreement(self):

        view = self.env.ref(
            'framework_agreement_requisition.'
            'confirm_generate_agreement_form_view'
        )

        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'confirm.generate.agreement',
            'view_id': view.id,
            'views': [(view.id, 'form')],
            'target': 'new',
            'context': self.env.context,
        }

    @api.model
    def _prepare_purchase_order(self, requisition, supplier):
        _super = super(PurchaseRequisition, self)
        values = _super._prepare_purchase_order(requisition,
                                                supplier)
        values.update(
            {'for_agreement': requisition.framework_agreement_tender,
             'agreement_expected_date': requisition.agreement_end_date,
             })
        return values


class PurchaseRequisitionClassic(orm.Model):
    """Add support to negociate LTA using tender process"""

    def __init__(self, pool, cr):
        """Nasty hack to add fields to select fields

        We do this in order not to compromising other state added
        by other addons that are not in inheritance chain...

        """
        sel = super(PurchaseRequisitionClassic, self)._columns['state']
        if SELECTED_STATE not in sel.selection:
            sel.selection.append(SELECTED_STATE)
        super(PurchaseRequisitionClassic, self).__init__(pool, cr)

    _inherit = "purchase.requisition"
    _columns = {
        'framework_agreement_tender': fields.boolean('Negociate Agreement'),
        'agreement_end_date': fields.date('LTA expected valitidy period'),
    }

    def tender_agreement_selected(self, cr, uid, ids, context=None):
        """Workflow function that write state 'Agreement selected'"""
        return self.write(cr, uid, ids, {'state': AGR_SELECT},
                          context=context)

    def select_agreement(self, cr, uid, agr_id, context=None):
        """Pass tender to state 'Agreement selected'"""
        if isinstance(agr_id, (list, tuple)):
            assert len(agr_id) == 1
            agr_id = agr_id[0]
        return self.signal_workflow(cr, uid, [agr_id], 'select_agreement',
                                    context=context)

    def _agreement_selected(self, cr, uid, ids, context=None):
        """Tells tender that an agreement has been selected"""
        if isinstance(ids, (int, long)):
            ids = [ids]
        generated = []
        for req in self.browse(cr, uid, ids, context=context):
            if not req.framework_agreement_tender:
                raise orm.except_orm(_('Invalid tender'),
                                     _('Request is not of type agreement'))
            self.select_agreement(cr, uid, req.id, context=context)
            req.refresh()
            if req.state != AGR_SELECT:
                raise RuntimeError('requisition %s does not pass to state'
                                   ' agreement_selected' %
                                   req.name)
            rfqs = chain.from_iterable(req_line.purchase_line_ids
                                       for req_line in req.line_ids)
            po_to_select = []
            po_to_cancel = []
            for rfq in rfqs:
                if rfq.state == 'confirmed':
                    agr_record = rfq.make_agreement(rfq.id, req.name)
                    generated.append(agr_record)
                    po_to_select.append(rfq.order_id)
                else:
                    po_to_cancel.append(rfq.order_id)

            if not po_to_select:
                raise orm.except_orm(_('No confirmed RFQ related to tender'),
                                     _('Please choose at least one'))

            for p_order in set(po_to_select):
                p_order.select_agreement()
                p_order.refresh()
                if p_order.state != PO_AGR_SELECT:
                    raise RuntimeError(
                        'Purchase order %s does not pass to %s' %
                        (p_order.name, PO_AGR_SELECT))
            for p_order in set(po_to_cancel):
                self.signal_workflow(cr, uid, [p_order.id], 'purchase_cancel',
                                     context=context)
        return generated

    def agreement_selected(self, cr, uid, ids, context=None):
        agrements = self._agreement_selected(cr, uid, ids, context=context)
        a_ids = [x.id for x in agrements]
        return {
            'name': _('Generated Agreements'),
            'view_mode': 'tree,form',
            'res_model': 'framework.agreement',
            'domain': [('id', 'in', a_ids)],
            'target': 'current',
            'view_id': False,
            'context': {},
            'type': 'ir.actions.act_window',
        }
