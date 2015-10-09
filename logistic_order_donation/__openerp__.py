# -*- coding: utf-8 -*-
#
#
#    Copyright 2014 Camptocamp SA
#    Author: Yannick Vaucher
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

{"name": "Logistics Order - Donation",
 "summary": "Sales Order as In-Kind Donations",
 "version": "8.0.0.2.0",
 "author": "Camptocamp,Odoo Community Association (OCA)",
 "license": "AGPL-3",
 "category": "Purchase Management",
 'complexity': "normal",
 "images": [],
 "website": "http://www.camptocamp.com",
 "depends": ["logistic_order",
             "web_context_tunnel",
             ],
 "demo": ['demo/donation.xml',
          ],
 "data": ['view/sale_order.xml',
          'data/stock.xml',
          ],
 "test": [],
 'installable': True,
 "auto_install": False,
 }
