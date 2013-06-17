# -*- coding: utf-8 -*-
##############################################################################
#
#    Author:  Joël Grand-Guillaume
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
 "version": "0.1",
 "author": "Camptocamp",
 "license": "AGPL-3",
 "category": "Purchase Management",
 'complexity': "normal",
 "images": [],
 "website": "http://www.camptocamp.com",
 "description": """
This module allows you to manage your Logistic Requisitions.
============================================================

A Logistic requisition express a need that is requested somewhere.

""",
 "depends": ["transport_plan",
             "purchase",
             "purchase_requisition",
             "ifrc_purchase_requisition", #FIXME: until that module is restructered and moved into ngo-addons
             "mail",
             "logistic_order",
             ],
 "demo": ['data/logistic_requisition_demo.xml'],
 "data": ["wizard/logistic_requisition_split_line_view.xml",
          "wizard/logistic_line_create_requisition_view.xml",
          "wizard/assign_line_view.xml",
          "wizard/cost_estimate_line_view.xml",
          "security/logistic_requisition.xml",
          "security/ir.model.access.csv",
          "data/logistic_requisition_data.xml",
          "data/logistic_requisition_sequence.xml",
          "view/logistic_requisition_view.xml",
          "view/sale_order.xml",
          "logistic_requisition_report.xml",
          "logistic_workflow.xml",
          ],
 "auto_install": False,
 "test": [],
 "installable": True,
 }
