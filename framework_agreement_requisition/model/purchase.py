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
from openerp import api, models
from openerp.osv import orm, fields

SELECTED_STATE = ('agreement_selected', 'Agreement selected')
AGR_SELECT = 'agreement_selected'


class purchase_order(orm.Model):
    """Add workflow behavior"""

    _inherit = "purchase.order"

    _columns = {
        'for_agreement': fields.boolean('For Framework Agreement'),
        'agreement_expected_date': fields.date('LTA expected valitidy period'),
        'agreement_promised_date': fields.date('LTA promised valitidy period'),
    }

    def __init__(self, pool, cr):
        """Add a new state value using PO class property"""
        if SELECTED_STATE not in super(purchase_order, self).STATE_SELECTION:
            super(purchase_order, self).STATE_SELECTION.append(SELECTED_STATE)
        super(purchase_order, self).__init__(pool, cr)

    @api.cr_uid_id_context
    def select_agreement(self, cr, uid, agr_id, context=None):
        """Pass PO in state 'Agreement selected'"""
        if isinstance(agr_id, (list, tuple)):
            assert len(agr_id) == 1
            agr_id = agr_id[0]
        return self.signal_workflow(cr, uid, [agr_id], 'select_agreement',
                                    context=context)

    def po_tender_agreement_selected(self, cr, uid, ids, context=None):
        """Workflow function that write state 'Agreement selected'"""
        return self.write(cr, uid, ids, {'state': AGR_SELECT},
                          context=context)


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    # Did you know a good way to supress SQL constraint to add
    # Python constraint...
    _sql_constraints = [(
        'quantity_bid',
        'CHECK(true)',
        'Selected quantity must be less or equal than the quantity in the bid'
    )]

    @api.multi
    def _check_quantity_bid(self):
        for line in self:
            if line.order_id.framework_agreement_id:
                continue
            if (
                line.product_id.type == 'product' and
                not line.quantity_bid <= line.product_qty
            ):
                return False
        return True

    _constraints = [(
        _check_quantity_bid,
        'Selected quantity must be less or equal than the quantity in the bid',
        []
    )]

    @api.multi
    def _agreement_data(self, origin):
        self.ensure_one()
        Portfolio = self.pool['framework.agreement.portfolio']
        return {
            'portfolio_id': Portfolio.get_from_supplier(
                self.order_id.partner_id)[0],
            'product_id': self.product_id.id,
            'quantity': self.product_qty,
            'delay': self.product_id.seller_delay,
            'origin': origin if origin else False,
        }

    @api.multi
    def make_agreement(self, origin):
        return self.pool['framework.agreement'].create(
            self._agreement_data(origin))
