# -*- coding: utf-8 -*-
##############################################################################
#
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
##############################################################################
from openerp import models, fields, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    incoterm_address = fields.Char(
        'Incoterm Place',
        help="Incoterm Place of Delivery. "
             "International Commercial Terms are a series of "
             "predefined commercial terms used in "
             "international transactions.")
    delivery_time = fields.Char('Delivery time')
    cost_estimate_only = fields.Boolean(
        'Cost Estimate Only',
        default=False)
    currency_id = fields.Many2one(
        related='pricelist_id.currency_id',
        co_model='res.currency',
        string='Currency')
    remark = fields.Text('Remarks / Description')

    @api.multi
    def action_quotation_send(self):
        """ Add the action we want to perform in case the user
        complete finally sends an email with designed wizard.

        """
        res = super(SaleOrder, self).action_quotation_send()
        if self.cost_estimate_only:
            res['context'].update(mark_cost_estimate_as_done=True)
        return res


class mail_compose_message(models.Model):
    _inherit = 'mail.compose.message'

    @api.multi
    def send_mail(self):
        context = self.env.context
        if (context.get('default_model') == 'sale.order'
                and 'default_res_id' in context
                and 'mark_cost_estimate_as_done' in context):
            res_id = context.get('default_res_id')
            sale_order = self.env['sale.order'].browse(res_id)
            sale_order.signal_workflow('cost_estimate_only_sent')
        return super(mail_compose_message, self).send_mail()
