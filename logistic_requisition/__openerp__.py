# -*- coding: utf-8 -*-
##############################################################################
#
#    Author:  Joël Grand-Guillaume, Jacques-Etienne Baudoux, Guewen Baconnier
#    Copyright 2013 Camptocamp SA
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more description.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{"name": "Logistic Requisition",
 "version": "0.2",
 "author": "Camptocamp",
 "license": "AGPL-3",
 "category": "Purchase Management",
 'complexity': "normal",
 "images": [],
 "website": "http://www.camptocamp.com",
 "description": """
This module allows you to manage your Logistic Requisitions.
============================================================

A Logistic requisition express a need that is requested somewhere. It allows to 
manage the sourcing of the needs before making a cost estimate to the requestor.

This invert the logic that is in standard in OpenERP in the way that the sourcing 
of the procuremnt is made before the order confirmation and we built the link incase 
of validation. In standard, th SO confirmation generate the procurement then it
generate the needed procurement.

The sourcing can be of various type:
 
 * Warehouse dispatch: You will deliver the requested goods from one of your 
 stock location
 * Procurement : You will go for tender to chose the best supplier for the 
 requiredgoods
 * Framework agreement : You will use the existing Framework agreement
 * Other : Nothing of those choices. In that case, the line can be selected
and included in either a PO or a tender

The simple process is the following:

 * LR are recorded as the to represent the need of the customer/requestor
 * LR are confirm and sourced of different way (dispatch, tender, ..)
 * If sourced from tender, you need to go all along the tendering process (CBA).
 Once you chose one bid, the system will automatically put back the prices 
 information on the sourcing line of the LR.
  * You can create a cost estimate from sourced LR lines for your 
 resquestor/customer
 * If the requestor accept the cost estimate, his validation will automatically:
   * Create the link between the chosen winning bid and the line sourced this way. 
     A new draft PO will be generatedand managed as drop shipping.
   * Lines sourced as a dispatch will create a delivery order. 
   * Lines sourced a LTA will create a PO of type LTA
""",
 "depends": ["transport_plan",
             "purchase",
             "purchase_requisition_extended",
             "mail",
             "logistic_order",
             ],
 "demo": ['data/logistic_requisition_demo.xml'],
 "data": ["wizard/logistic_line_create_requisition_view.xml",
          "wizard/assign_line_view.xml",
          "wizard/transport_plan_view.xml",
          "wizard/cost_estimate_view.xml",
          "wizard/logistic_requisition_cancel_view.xml",
          "security/logistic_requisition.xml",
          "security/ir.model.access.csv",
          "data/logistic_requisition_data.xml",
          "data/logistic_requisition_sequence.xml",
          "view/logistic_requisition.xml",
          "view/sale_order.xml",
          "view/transport_plan.xml",
          "view/cancel_reason.xml",
          "view/purchase_requisition.xml",
          "report/logistic_requisition_report.xml",
          "data/logistic.requisition.cancel.reason.csv",
          ],
 "test": ['test/line_assigned.yml',
          'test/requisition_create_cost_estimate.yml',
          'test/requisition_cancel_reason.yml',
          'test/transport_plan.yml',
          'test/transport_plan_to_cost_estimate.yml',
          'test/transport_plan_from_lr_line_wizard.yml',
          'test/logistic_requisition_report_test.yml',
          'test/test_picking_by_location_address.yml',
          ],
 'installable': True,
 'auto_install': False,
 }
