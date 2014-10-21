# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Nicolas Bessi
#    Copyright 2013, 2014 Camptocamp SA
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
{'name': 'Framework Agreement Negociation in the Tender',
 'version': '1.0',
 'author': 'Camptocamp',
 'maintainer': 'Camptocamp',
 'category': 'NGO',
 'complexity': 'normal',
 'depends': ['purchase_requisition',
             'purchase_requisition_bid_selection',
             'framework_agreement'],
 'description': """
Negociate framework agreement in the Tender
===========================================

This module allows you to negociate a framework agreement in the Tender.

To to so you have to check the box "Negociate Agreement".

The module add a state "Agreement selected" on the tender and on the Purchase
Order.

These will be the final state once you have chosen the agreement that best fits
your needs.

Once the selection is done just use the button "Agreement selected" on the
tender. That will close the flow of tender and the related PO accordingly.

""",
 'website': 'http://www.camptocamp.com',
 'data': ['requisition_workflow.xml',
          'purchase_workflow.xml',
          'view/purchase_requisition_view.xml'],
 'demo': [],
 'test': ['test/agreement_requisition.yml'],
 'installable': True,
 'auto_install': False,
 'license': 'AGPL-3',
 'application': False,
 }
