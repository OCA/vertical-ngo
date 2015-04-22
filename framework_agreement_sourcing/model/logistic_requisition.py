# -*- coding: utf-8 -*-
#    Author: Nicolas Bessi, Leonardo Pistone
#    Copyright 2013-2015 Camptocamp SA
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
from datetime import datetime

from openerp import models, api
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT


class LogisticsRequisitionLine(models.Model):
    _inherit = "logistic.requisition.line"

    @api.multi
    def _generate_default_source(self):
        """If there are relevant agreements, propose a source by agreement.

        Choosing an agreement is up to the user.

        Note: older versions of the module had logic to automatically choose
        one or more agreements.
        """
        Agreement = self.env['product.pricelist']
        _super = super(LogisticsRequisitionLine, self)
        new_source = _super._generate_default_source()

        req_date = datetime.strptime(self.requisition_id.date, DATETIME_FORMAT)

        suitable_agreements = Agreement.search([
            ('incoterm_id', '=', self.requisition_id.incoterm_id.id),
            ('incoterm_address', '=', self.requisition_id.incoterm_address),
            ('portfolio_id', '!=', False),
        ]).filtered(
            lambda a: a.portfolio_id.is_suitable_for(req_date,
                                                     self.product_id,
                                                     self.requested_qty)
        )

        if suitable_agreements:
            new_source.sourcing_method = 'fw_agreement'
            if len(suitable_agreements) == 1:
                new_source.framework_agreement_id = suitable_agreements

        return new_source
