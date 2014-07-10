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
from openerp import netsvc
from openerp.osv import orm

SELECTED_STATE = ('agreement_selected', 'Agreement selected')
AGR_SELECT = 'agreement_selected'


class purchase_order(orm.Model):
    """Add workflow behavior"""

    _inherit = "purchase.order"

    def __init__(self, pool, cr):
        """Add a new state value using PO class property"""
        if SELECTED_STATE not in super(purchase_order, self).STATE_SELECTION:
            super(purchase_order, self).STATE_SELECTION.append(SELECTED_STATE)
        return super(purchase_order, self).__init__(pool, cr)

    def select_agreement(self, cr, uid, agr_id, context=None):
        """Pass PO in state 'Agreement selected'"""
        if isinstance(agr_id, (list, tuple)):
            assert len(agr_id) == 1
            agr_id = agr_id[0]
            wf_service = netsvc.LocalService("workflow")
        return wf_service.trg_validate(uid, 'purchase.order',
                                       agr_id, 'select_agreement', cr)

    def po_tender_agreement_selected(self, cr, uid, ids, context=None):
        """Workflow function that write state 'Agreement selected'"""
        return self.write(cr, uid, ids, {'state': AGR_SELECT},
                          context=context)


class purchase_order_line(orm.Model):
    """Add make_agreement function"""

    _inherit = "purchase.order.line"

    # Did you know a good way to supress SQL constraint to add
    # Python constraint...
    _sql_constraints = [
        ('quantity_bid', 'CHECK(true)',
         'Selected quantity must be less or equal than the quantity in the bid'),
    ]

    def _check_quantity_bid(self, cr, uid, ids, context=None):
        for line in self.browse(cr, uid, ids, context=context):
            if line.order_id.framework_agreement_id:
                continue
            if line.product_id.type == 'product' and  not line.quantity_bid <= line.product_qty:
                return False
        return True

    _constraints = [
        (_check_quantity_bid,
         'Selected quantity must be less or equal than the quantity in the bid',
         [])
    ]
    def _agreement_data(self, cr, uid, po_line, origin, context=None):
        """Get agreement values from PO line

        :param po_line: Po line records

        :returns: agreement dict to be used by orm.Model.create
        """
        vals = {}
        vals['supplier_id'] = po_line.order_id.partner_id.id
        vals['product_id'] = po_line.product_id.id
        vals['quantity'] = po_line.product_qty
        vals['delay'] = po_line.product_lead_time
        vals['origin'] = origin if origin else False
        return vals

    def make_agreement(self, cr, uid, line_id, origin, context=None):
        """ generate a draft framework agreement

        :returns: a record of LTA

        """
        agr_model = self.pool['framework.agreement']
        if isinstance(line_id, (list, tuple)):
            assert len(line_id) == 1
            line_id = line_id[0]
        current = self.browse(cr, uid, line_id, context=context)
        vals = self._agreement_data(cr, uid, current, origin, context=context)
        agr_id = agr_model.create(cr, uid, vals, context=context)
        return agr_model.browse(cr, uid, agr_id, context=context)
