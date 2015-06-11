# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright 2015 Camptocamp SA
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

from openerp import models, fields


class ngo_config_settings(models.TransientModel):
    _name = 'ngo.config.settings'
    _inherit = 'res.config.settings'

    module_framework_agreement_requisition = fields.Boolean(
        'Create tenders to negociate a framework agreements',
        help="To allow your NGO to manage tenders when negociating "
        "framework agreements from possible suppliers."
    )
    module_framework_agreement_sourcing = fields.Boolean(
        'Allow to source a logistics requisition with a framework agreement',
        help="if your NGO has framework agreements with suppliers "
        "which you use to source logistics requisitions."
    )
    module_logistic_budget = fields.Boolean(
        'Manage budget on logistics requisitions and cost estimates',
        help="adds the notion of budget and budget holer on logistics "
        "requisitions and logistics orders."
    )
    module_logistic_order_donation = fields.Boolean(
        'Manage in-kind donations',
        help="if your NGO has to manage logistics orders which are "
        "in-kind donations from other partners."
    )
    module_logistic_order_multicurrency = fields.Boolean(
        'Manage multiple currencies for logistics orders',
        help="to display the amount of the logistics order "
        "in the company currency using the exchange rate at "
        "the date of the order."
    )
    module_logistic_requisition = fields.Boolean(
        'Manage logistics requisitions and logistics orders',
        help="A Logistics requisition express a need that is "
        "requested somewhere. It allows to manage the sourcing "
        "of the needs before making a cost estimate to the requestor."
    )
    module_logistic_requisition_donation = fields.Boolean(
        'Manage donor stock dispatches as logistics requisitions',
        help="to create logistics requisition to dispatch stock "
        "stored in your warehouse and owned by other entities."
    )
    module_logistic_requisition_multicurrency = fields.Boolean(
        'Manage multiple currencies for logistics requisitions',
        help="to display the amounts on logistics requisitions in "
        "company currency.\n"
        "The amounts are converted from requisition currency to "
        "company currency at rates of requisition date.")
    module_ngo_purchase_requisition = fields.Boolean(
        'Manage purchase requisitions',
        help="to use the updated bid selection process")
    module_ngo_purchase = fields.Boolean(
        'Manage purchases and framework agreements',
        help="to manage purchases with a RFQ / Bid workflow, and "
        "various international transport documents on your purchase orders."
    )
    module_ngo_shipment_plan = fields.Boolean(
        'Manage shipment plans',
        help="to follow the shipment of your logistics orders and manage "
        "transit locations."
    )
