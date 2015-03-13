# -*- coding: utf-8 -*-
#
#
#    Author: Yannick Vaucher
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
from openerp import models, api


class LogisticsRequisitionLine(models.Model):
    _inherit = 'logistic.requisition.line'

    @api.multi
    def _prepare_donor_source(self):
        """ Search and add dispatch location

        If only one location match, we set it.
        If multiple location match, we let the field empty so the user must
        set it.
        Otherwise if no location match we prefill the sourcing type as other

        :param self: requisition line record set
        :returns: dict of values to create a source line

        """
        values = self._prepare_source(qty=self.requested_qty)
        owner = self.requisition_id.partner_id.commercial_partner_id
        search_domain = [
            ('owner_id', '=', owner.id),
            ('product_id', '=', self.product_id.id),
            ('qty', '>', 0)]
        quant_groups = self.env['stock.quant'].read_group(
            search_domain, ['location_id', 'qty'], ['location_id'])
        location_ids = [q['location_id'][0] for q in quant_groups]
        sourcing_method = 'wh_dispatch' if location_ids else 'other'
        values['sourcing_method'] = sourcing_method
        if sourcing_method == 'wh_dispatch':
            values['stock_owner_id'] = owner.id
        if len(location_ids) == 1:
            wh_model = self.env['stock.warehouse']
            wh = wh_model.search([('lot_stock_id', '=', location_ids[0])])
            values['dispatch_warehouse_id'] = wh.id
        return values

    @api.multi
    def _generate_donor_source(self):
        """Generate 1 source line for one requisition line

        This is done by creating a warehouse dispatch source
        Where source location owner is Requisting entity

        :param self: requisition line record set

        """
        src_model = self.env['logistic.requisition.source']
        values = self._prepare_donor_source()
        src_model.create(values)

    @api.multi
    def _generate_sources(self):
        """Generate one or n source line(s) per requisition line.

        Add creation of source for donor' stock warehouse dispatch

        :param self: requisition line record set

        """
        self.ensure_one()
        if self.source_ids:
            return
        if self.requisition_id.requisition_type == 'donor_stock':
            self._generate_donor_source()
            return
        super(LogisticsRequisitionLine, self)._generate_sources()
