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
from openerp.osv import orm


class procurement_order(orm.Model):
    _inherit = 'procurement.order'

    def action_po_assign(self, cr, uid, ids, context=None):
        """ Called from the workflow to assign the purchase order to a
        procurement.

        Normally, it creates a purchase order for the procurement.
        Here, we check if it already exists and in such case, we just
        update the state and keep the assigned purchase order. A
        purchase order is already assigned to the procurement when a
        `sale.order` is created from a logistic requisition which has
        already a `purchase.order`.

        """
        assert len(ids) == 1, "Expected only 1 ID, got: %r" % ids
        procurement = self.read(cr, uid, ids[0], ['purchase_id', 'state'],
                                context=context, load='_classic_write')
        if procurement['purchase_id']:
            self.write(cr, uid, ids, {'state': 'running'}, context=context)
            return procurement['purchase_id']
        return super(procurement_order, self).action_po_assign(
            cr, uid, ids, context=context)
