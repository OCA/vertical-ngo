# -*- coding: utf-8 -*-
#
#
#    Author: Yannick Vaucher
#    Copyright 2014 Camptocamp SA
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

{"name": "Logistics Consignee",
 "summary": "Consignee on Sales, Purchases, Purchase requisition for Pickings",
 "version": "0.1",
 "author": "Camptocamp,Odoo Community Association (OCA)",
 "license": "AGPL-3",
 "category": "Logistics",
 'complexity': "normal",
 "images": [],
 "website": "http://www.camptocamp.com",
 "depends": ["base",
             "sale_stock",
             "purchase",
             "purchase_requisition",
             ],
 "demo": [],
 "data": ['view/res_partner.xml',
          'view/purchase_order.xml',
          'view/purchase_requisition.xml',
          'view/sale_order.xml',
          'view/stock_picking.xml',
          'view/report_saleorder.xml',
          ],
 "test": ['test/test_report.yml'],
 'installable': True,
 "auto_install": False,
 }
