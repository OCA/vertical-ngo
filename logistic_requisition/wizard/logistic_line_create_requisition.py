# -*- coding: utf-8 -*-
#
#
#    Author:  Joël Grand-Guillaume
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
from openerp import models, fields, api
from openerp.tools.translate import _


class LogisticsRequisitionSourceCreateRequisition(models.TransientModel):
    _name = "logistic.requisition.source.create.requisition"
    _description = "Create Purchase Requisition From Requisition Source"

    pricelist_id = fields.Many2one(
        'product.pricelist',
        string='Pricelist / Currency',
        required=True)

    @api.model
    def default_get(self, fields_list):
        """Take the first line pricelist as default"""
        defaults = super(LogisticsRequisitionSourceCreateRequisition, self
                         ).default_get(fields_list)
        line_obj = self.env['logistic.requisition.source']
        line_ids = self.env.context['active_ids']
        pricelist_id = None
        line = line_obj.browse(line_ids[0])
        pricelist_id = line_obj._get_purchase_pricelist_from_currency(
            line.requisition_id.pricelist_id.currency_id.id,
            )
        defaults['pricelist_id'] = pricelist_id.id
        return defaults

    @api.multi
    def create_po_requisition(self):
        self.ensure_one()
        source_obj = self.env['logistic.requisition.source']
        source = source_obj.browse(self.env.context['active_ids'])
        requisition_id = source._action_create_po_requisition(
            pricelist=self.pricelist_id)
        return {
            'name': _('Purchase Requisition'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'purchase.requisition',
            'res_id': requisition_id.id,
            'view_id': False,
            'type': 'ir.actions.act_window',
        }
