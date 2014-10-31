# -*- coding: utf-8 -*-
#
#
#    Author: Yannick Vaucher
#    Copyright 2014 Camptocamp SA
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
from openerp import models, fields, api
from openerp import SUPERUSER_ID


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    consignee_id = fields.Many2one(
        'res.partner',
        string='Consignee',
        required=True,
        help="The person to whom the shipment is to be delivered.")

    @api.cr
    def init(self, cr):
        """set SUPERUSER_ID as consignee_id for existing sale orders
        """
        cr.execute('SELECT COUNT(id) FROM sale_order'
                   ' WHERE consignee_id IS NULL')
        count = cr.fetchone()[0]
        if count:
            cr.execute('UPDATE sale_order SET consignee_id=%s'
                       ' WHERE consignee_id IS NULL', (SUPERUSER_ID,))
            cr.execute('ALTER TABLE sale_order ALTER COLUMN consignee_id'
                       ' SET NOT NULL')
