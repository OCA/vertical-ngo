# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright 2013 Camptocamp SA
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

{"name": "Logistic Order",
 "version": "0.1",
 "author": "Camptocamp",
 "license": "AGPL-3",
 "category": "Purchase Management",
 'complexity': "normal",
 "images": [],
 "website": "http://www.camptocamp.com",
 "description": """
This module customizes the Sales Orders to disguise them in Logistic Orders
===========================================================================

""",
 "depends": ["sale_stock",
             "sale_validity",
             "delivery",
             "stock_location_ownership",
             ],
 "demo": [],
 "data": ['view/sale_order_view.xml',
          'view/report_logisticorder.xml',
          'data/logistic_order_sequence.xml',
          ],
 "test": ['test/test_report.yml',
          ],
 'installable': True,
 "auto_install": False,
 }
