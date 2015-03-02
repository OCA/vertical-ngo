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
 'author': "Camptocamp,Odoo Community Association (OCA)",
 'maintainer': 'Camptocamp',
 'category': 'NGO',
 'complexity': 'normal',
 'depends': ['purchase_requisition',
             'purchase_requisition_bid_selection',
             'ngo_purchase_requisition',
             'framework_agreement'],
 'website': 'http://www.camptocamp.com',
 'data': ['requisition_workflow.xml',
          'purchase_workflow.xml',
          'view/purchase_requisition.xml',
          'view/purchase_order.xml',
          'wizard/confirm_generate_agreement.xml'
          ],
 'demo': [],
 'test': ['test/agreement_requisition.yml'],
 'installable': True,
 'auto_install': False,
 'license': 'AGPL-3',
 'application': False,
 }
