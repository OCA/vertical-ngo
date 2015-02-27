# -*- coding: utf-8 -*-
#
#
#    Author: Yannick Vaucher, Leonardo Pistone
#    Copyright 2014-2015 Camptocamp SA
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
from openerp import models, fields
from openerp import SUPERUSER_ID


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    LO_STATES = {
        'cancel': [('readonly', True)],
        'progress': [('readonly', True)],
        'manual': [('readonly', True)],
        'shipping_except': [('readonly', True)],
        'invoice_except': [('readonly', True)],
        'done': [('readonly', True)],
    }

    consignee_id = fields.Many2one(
        'res.partner',
        string='Consignee',
        required=True,
        states=LO_STATES,
        help="The person to whom the shipment is to be delivered.")

    def _auto_init(self, cr, context):
        """Fill in the required consignee column with default values.

        This is similar to the solution used in mail_alias.py in the core.

        The installation of the module will succeed with no errors, and the
        column will be required immediately (the previous solution made it
        required only on the first module update after installation).

        """

        # create the column non required
        self._columns['consignee_id'].required = False
        super(SaleOrder, self)._auto_init(cr, context=context)

        # fill in the empty records
        no_consignee_ids = self.search(cr, SUPERUSER_ID, [
            ('consignee_id', '=', False)
        ], context=context)
        self.write(cr, SUPERUSER_ID, no_consignee_ids,
                   {'consignee_id': SUPERUSER_ID}, context)

        # make the column required again
        self._columns['consignee_id'].required = True
        super(SaleOrder, self)._auto_init(cr, context=context)
