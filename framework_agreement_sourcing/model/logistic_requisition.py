# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Nicolas Bessi
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
#
##############################################################################
from openerp import models, api


class LogisticsRequisitionLine(models.Model):

    """Override to enable generation of source line"""

    _inherit = "logistic.requisition.line"

    @api.multi
    def _generate_default_source(self):
        """If there are relevant agreements, propose a source by agreement.

        Choosing an agreement is up to the user.

        Note: older versions of the module had logic to automatically choose
        one or more agreements.
        """
        _super = super(LogisticsRequisitionLine, self)
        new_source = _super._generate_default_source()

        Agreement = self.env['framework.agreement']
        ag_domain = Agreement.get_agreement_domain(
            self.product_id.id,
            self.requested_qty,
            None,
            self.requisition_id.date,
            self.requisition_id.incoterm_id.id,
            self.requisition_id.incoterm_address,
        )
        if Agreement.search(ag_domain):
            new_source.sourcing_method = 'fw_agreement'
        return new_source
