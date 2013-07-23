# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Guewen Baconnier
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


class purchase_requisition(orm.Model):
    _inherit = 'purchase.requisition'

    _columns = {
        'logistic_requisition_line_ids': fields.one2many(
            'logistic.requisition.line', 'po_requisition_id',
            string='Logistic Requisition Lines',
            readonly=True),
    }

    def generate_po(self, cr, uid, id, context=None):
        result = super(purchase_requisition, self).generate_po(
            cr, uid, id, context=context)
        assert len(id) == 1, "generate_po accept only 1 ID"
        purch_req = self.browse(cr, uid, id[0], context=context)
        requisition_line = purch_req.logistic_requisition_line_ids
        if not requisition_line:
            return result
        assert len(requisition_line) == 1, (
            "A purchase.requisition for several logistic.requisition.line "
            "is not supported")
        requisition_line = requisition_line[0]
        requisition_line.write({'price_is': 'fixed'})

        # generate_po has canceled all the po and created a new one
        # in 'draftpo' state
        # purch_order = [po for po in purch_req.purchase_ids
        #                if po.state == 'draftpo']
        # assert len(purch_order) == 1, (
        #     "Should have 1 draft po, got: %d" % len(purch_order))
        # purch_order = purch_order[0]
        return result
