# -*- coding: utf-8 -*-
##############################################################################
# #    Author:  Joël Grand-Guillaume #    Copyright 2013 Camptocamp SA
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

from openerp.osv import fields, orm
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp


class LogisticRequisitionSplitLine(orm.TransientModel):
    _name = "logistic.requisition.split.source.line"
    _description = "Split Requisition Source Line"
    _columns = {
        'remaining': fields.float(
            'Remaining',
            digits_compute=dp.get_precision('Product Unit of Measure')),
    }

    _defaults = {
        'remaining': 0,
    }

    def split(self, cr, uid, ids, context=None):
        """ Split a line in 2 lines, according to a remaining quantity.

        The remaining quantity is the value which stay in the selected line.
        """
        if isinstance(ids, (tuple, list)):
            assert len(ids) == 1, "One ID only expected, got: %s" % ids
            ids = ids[0]
        if context is None:
            context = {}
        remaining = self.browse(cr, uid, ids, context=context).remaining or 0.0
        line_ids = context.get('active_ids')
        source_obj = self.pool.get('logistic.requisition.source')
        for line in source_obj.browse(cr, uid, line_ids, context=context):
            quantity = line.proposed_qty - remaining
            if quantity < 0:
                raise orm.except_orm(_('Error'),
                                     _('Split quantity exceeds '
                                       'the quantity of this line: %s') %
                                     line.name)
            line.split(quantity)
        return {'type': 'ir.actions.act_window_close'}
