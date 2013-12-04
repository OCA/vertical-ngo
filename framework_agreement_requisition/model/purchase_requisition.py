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
from itertools import chain
from openerp import netsvc
from openerp.osv import orm, fields
from openerp.tools.translate import _


class purchase_requisition(orm.Model):
    """Add support to negociate LTA using tender process"""

    _inherit = "purchase.requisition"
    _columns = {
        'framework_agreement_tender': fields.boolean('Negociate Agreement'),
        'state': fields.selection([('draft', 'Draft'),
                                   ('in_progress', 'Confirmed'),
                                   ('open', 'Bids Selection'),
                                   ('closed', 'Bids Selected'),
                                   ('done', 'PO Created'),
                                   ('agreement_selected', 'Agreement selected'),
                                   ('cancel', 'Canceled')],
                                  'Status',
                                  track_visibility='onchange',
                                  required=True),
    }

    def tender_agreement_selected(self, cr, uid, ids, context=None):
        """Workflow function that write state 'Agreement selected'"""
        return self.write(cr, uid, ids, {'state': 'agreement_selected'},
                          context=context)

    def select_agreement(self, cr, uid, agr_id, context=None):
        """Pass tender to state 'Agreement selected'"""
        if isinstance(agr_id, (list, tuple)):
            assert len(agr_id) == 1
            agr_id = agr_id[0]
        wf_service = netsvc.LocalService("workflow")
        return wf_service.trg_validate(uid, 'purchase.requisition',
                                       agr_id, 'select_agreement', cr)

    def agreement_selected(self, cr, uid, ids, context=None):
        """Tells tender that an agreement has been selected"""
        if isinstance(ids, (int, long)):
            ids = [ids]
        for req in self.browse(cr, uid, ids, context=context):
            if not req.framework_agreement_tender:
                raise orm.except_orm(_('Invalid tender'),
                                     _('Request is not of type agreement'))
            self.select_agreement(cr, uid, req.id, context=context)
            req.refresh()
            if req.state != 'agreement_selected':
                raise RuntimeError('requisiton %s does not pass to state'
                                   ' agreement_selected' %
                                   req.name)
            rfqs = chain.from_iterable(req_line.purchase_line_ids
                                       for req_line in req.line_ids)
            rfqs = [rfq for rfq in rfqs if rfq.state == 'confirmed']
            if not rfqs:
                raise orm.except_orm(_('No confirmed RFQ related to tender'),
                                     _('Please choose at least one'))
            for rfq in rfqs:
                rfq.make_agreement(req.name)
                p_order = rfq.order_id
                p_order.select_agreement()
                p_order.refresh()
                if p_order.state != 'agreement_selected':
                    raise RuntimeError('Purchase order %s does not pass to state'
                                       ' agreement_selected' %
                                       p_order.name)
        return True
