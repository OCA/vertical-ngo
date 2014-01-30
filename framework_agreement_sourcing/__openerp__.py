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
{'name': 'Framework agreement integration in sourcing',
 'version': '0.1',
 'author': 'Camptocamp',
 'maintainer': 'Camptocamp',
 'category': 'NGO',
 'complexity': 'normal',
 'depends': ['framework_agreement', 'logistic_requisition'],
 'description': """
Automatically source logistic order from framework agreement
============================================================

If you have a framework agreement negociated for the current product in
your logistic requisition. If the date and state of agreement are OK,
agreement will be used as source for the concerned source lines
of your request.

In this case tender flow is byassed and confirmed PO will be generated
when logistic requisition is confirmed.

By default the sourcing process will look in all agreements for a product
and use them one after the other as long as possible sorted by price.

You can prevent this behavior by forcing only one agreement per product at
the same time in company.

""",
 'website': 'http://www.camptocamp.com',
 'data': [
    'view/requisition_view.xml',
    'logistic_requisition_source_create_po_view.xml',
 ],
 'demo': [],
 'test': [],
 'installable': True,
 'auto_install': False,
 'license': 'AGPL-3',
 'application': False,
 }
