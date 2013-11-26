# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Nicolas Bessi
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
{'name': 'Simple Framework Agreement',
 'version': '0.1',
 'author': 'Camptocamp',
 'maintainer': 'Camptocamp',
 'category': 'Purchase Management',
 'complexity': 'normal',
 'depends': ['stock', 'procurement', 'purchase'],
 'description': """
Long Term Agreement (or Framework Agreement) on price.
======================================================

Agreements are defined by a product, a date range , a supplier, a price, a lead time
and agreed quantity.

Agreements are set on a product view or using a menu in the product configuration.

There can be only one agreement for the same supplier and product at the same time, even
if we may have different prices depending on lead time/qty.

There is an option on company to restrict one agreement per product at same time.

If an agreement is running its price will be automatically used in PO.
A warning will be raised in case of exhaustion of override of agreement price.

**Technical aspect**

The module provide an observalbe mixin to enable generic on_change management on various model
related to agreements.

The framework agreement is by default related to purchase order but the addon
provides a library to integrate it with any other model easily
""",
 'website': 'http://www.camptocamp.com',
 'data': ['data.xml',
          'security/multicompany.xml',
          'view/product_view.xml',
          'view/framework_agreement_view.xml',
          'view/purchase_view.xml',
          'view/company_view.xml'],
 'demo': [],
 'test': [],
 'installable': True,
 'auto_install': False,
 'license': 'AGPL-3',
 'application': False,
 }
