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
{'name': 'Framework Agreement Negociation',
 'version': '0.1',
 'author': "Camptocamp,Odoo Community Association (OCA)",
 'maintainer': 'Camptocamp',
 'category': 'NGO',
 'complexity': 'normal',
 'depends': ['purchase_requisition',
             'purchase_requisition_extended',
             'framework_agreement'],
 'description': """
Negociate framework agreement using tender process
==================================================

This will allows you to use "The calls for Bids" model
 to negociate agreement.

To to so you have too check the box "Negociate Agreement".

The module add a state "Agreement selected" on tender and PO.


These will be the final state once you have choosen
the agreement that fit your needs the best.

Once the selection is done juste use the button "Agreement selected" on tender
That will close flow of tender and related PO accordingly.

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
