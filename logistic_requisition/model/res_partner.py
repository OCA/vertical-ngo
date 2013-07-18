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
from .logistic_requisition import REQUESTER_TYPE


class res_partner(orm.Model):
    _inherit = 'res.partner'

    _columns = {
        'requester_type': fields.selection(REQUESTER_TYPE,
                                           string='Requester Type'),
    }

    def _commercial_fields(self, cr, uid, context=None):
        fields = super(res_partner, self)._commercial_fields(cr, uid, context=context)
        fields.append('requester_type')
        return fields
