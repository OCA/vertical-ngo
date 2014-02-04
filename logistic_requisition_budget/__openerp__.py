# -*- coding: utf-8 -*-
##############################################################################
#
#    Author:  Joël Grand-Guillaume, Jacques-Etienne Baudoux, Guewen Baconnier
#    Copyright 2013 Camptocamp SA
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more description.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{"name": "Logistic Requisition Budget",
 "version": "0.1",
 "author": "Camptocamp",
 "license": "AGPL-3",
 "category": "Purchase Management",
 'complexity': "normal",
 "images": [],
 "website": "http://www.camptocamp.com",
 "description": """
This module isolates budget dimension about Logistic Requisitions.
===================================================================

A Logistic requisition express a need that is requested somewhere. It allows to 
manage the sourcing of the needs before making a cost estimate to the requestor.

This invert the logic that is in standard in OpenERP in the way that the sourcing 
of the procuremnt is made before the order confirmation and we built the link incase 
of validation. In standard, th SO confirmation generate the procurement then it
generate the needed procurement.

""",
 "depends": ["logistic_requisition",
             ],
 "demo": [],
 "data": ["view/logistic_requisition.xml",
          "report/logistic_requisition_report.xml",
          ],
 "auto_install": False,
 "test": ['test/requisition_create_cost_estimate.yml',
          ],
 "installable": True,
 }
