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

{"name": "Logistics Order",
 "summary": "Sales Order as Logistics Order",
 "version": "0.3",
 "author": "Camptocamp,Odoo Community Association (OCA)",
 "license": "AGPL-3",
 "category": "Purchase Management",
 'complexity': "normal",
 "images": [],
 "website": "http://www.camptocamp.com",
 "description": """
Logistics Order
===============

This module customizes the Sales Orders to disguise them in Logistics Orders

A draft Sale order is now a Cost Estimate
An opened Sale order is now a Logistics Order

* Adds Consignee, Incoterm Address and Delivery time on the Logistics Order
* Adds a main menu entry `Order Management`


Contributors
------------

* Guewen Baconnier <guewen.baconnier@camptocamp.com>
* Nicolas Bessi <nicolas.bessi@camptocamp.com>
* Yannick Vaucher <yannick.vaucher@camptocamp.com>
* Alexandre Fayolle <alexandre.fayolle@camptocamp.com>

""",
 "depends": ["sale_stock",
             "sale_validity",
             "delivery",
             "sale_quotation_sourcing",
             'logistic_consignee',
             ],
 "demo": [],
 "data": ['view/sale_order_view.xml',
          'view/report_logisticorder.xml',
          'workflow/sale_order.xml',
          'data/logistic_order_sequence.xml',
          ],
 "test": ['test/test_report.yml',
          ],
 'installable': True,
 "auto_install": False,
 }
