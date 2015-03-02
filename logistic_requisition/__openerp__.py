# -*- coding: utf-8 -*-
#
#
#    Author: Joël Grand-Guillaume, Jacques-Etienne Baudoux, Guewen Baconnier
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

{"name": "Logistics Requisition",
 "version": "1.4",
 "author": "Camptocamp,Odoo Community Association (OCA)",
 "license": "AGPL-3",
 "category": "Purchase Management",
 'complexity': "normal",
 "images": [],
 "website": "http://www.camptocamp.com",
 "depends": ["sale_sourced_by_line",
             "sale_owner_stock_sourcing",
             "stock_dropshipping",
             "purchase",
             "purchase_requisition_bid_selection",
             "mail",
             "logistic_order",
             "logistic_consignee",
             "ngo_purchase",
             "transport_information",
             "purchase_requisition_transport_document",
             "purchase_requisition_delivery_address",
             ],
 "demo": ['data/logistic_requisition_demo.xml'],
 "data": ["wizard/assign_line_view.xml",
          "wizard/cost_estimate_view.xml",
          "wizard/logistic_requisition_cancel_view.xml",
          "security/logistic_requisition.xml",
          "security/ir.model.access.csv",
          "data/logistic_requisition_data.xml",
          "data/logistic_requisition_sequence.xml",
          "view/logistic_requisition.xml",
          "view/sale_order.xml",
          "view/stock.xml",
          "view/cancel_reason.xml",
          "view/purchase_order.xml",
          "view/report_logistic_requisition.xml",
          "logistic_requisition_report.xml",
          "data/logistic.requisition.cancel.reason.csv",
          ],
 "test": ['test/line_assigned.yml',
          'test/requisition_create_cost_estimate.yml',
          'test/requisition_create_cost_estimate_only.yml',
          'test/requisition_sourcing_with_tender.yml',
          'test/requisition_cancel_reason.yml',
          'test/logistic_requisition_report_test.yml',
          ],
 'css': ['static/src/css/logistic_requisition.css'],
 'installable': True,
 'auto_install': False,
 }
