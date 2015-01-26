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
from openerp import models, api, exceptions, _


class LogisticsRequisitionSource(models.Model):
    _inherit = 'logistic.requisition.source'

    @api.onchange('sourcing_method')
    def onchange_source_type_warning(self):
        if self.requisition_id.requisition_type == 'donor_stock':
            if self.sourcing_method not in ('wh_dispatch', 'other'):
                raise exceptions.Warning(_(
                    "Only 'Warehouse Dispatch' and 'Other' sourcing methods "
                    "can be used with Requestor Stock Dispatch logistics "
                    "requisition"))
            owner = self.requisition_id.partner_id.commercial_partner_id
            self.stock_owner_id = owner.id
