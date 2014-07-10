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
from openerp.osv import fields, orm
from openerp.tools.translate import _


class logistic_requisition_cost_estimate(orm.TransientModel):
    _inherit = 'logistic.requisition.cost.estimate'

    def _check_requisition(self, cr, uid, requisition, context=None):
        """ Check the rules to create a cost estimate from the
        requisition

        :returns: list of tuples ('message, 'error_code')
        """
        errors = []
        if not requisition.budget_holder_id:
            error = (_('The requisition must be validated '
                       'by the Budget Holder.'),
                     'NO_BUDGET_VALID')
            errors.append(error)
        return errors
