# -*- coding: utf-8 -*-
#
#
#    Copyright 2015 Camptocamp SA
#    Author: Yannick Vaucher
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


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    sourcing_method = fields.Selection(
        selection_add=[('donation', "In-kind Donation")],
        compute='_get_sourcing_method',
        related=False
    )

    # Limited selection for view
    sourcing_method_donation = fields.Selection(
        selection=[('donation', "In-kind Donation"),
                   ('other', "Other")],
        string="Sourcing Method",
        default="donation",
    )

    # field for visibility on view
    order_type = fields.Selection(
        related='order_id.order_type',
        selection=[
            ('standard', 'Standard'),
            ('cost_estimate_only', 'Cost Estimate Only'),
            ('donation', 'In-Kind Donation')
        ]
    )

    @api.one
    @api.depends('lr_source_id.sourcing_method',
                 'order_id.order_type',
                 'sourcing_method_donation')
    def _get_sourcing_method(self):
        """Compute value of sourcing_method

        Sourcing method is related of lr_source_id.sourcing_method
        Unless lr_source_id is not set
        In case of donation it takes the value from sourcing_method_donation
        Otherwise it is 'Other'
        """
        method = 'other'
        if self.lr_source_id:
            method = self.lr_source_id.sourcing_method
        elif self.order_id.order_type == 'donation':
            method = self.sourcing_method_donation
        self.sourcing_method = method
