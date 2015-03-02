# -*- coding: utf-8 -*-
# Author: Leonardo Pistone
# Copyright 2014 Camptocamp SA (http://www.camptocamp.com)

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public Lice
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

{
    'name': 'Logistic Requisitions with Department Categorization',
    'version': '1.1',
    "category": "Purchase Management",
    'author': "Camptocamp,Odoo Community Association (OCA)",
    "license": "AGPL-3",
    'website': 'http://camptocamp.com',
    'depends': ['logistic_requisition', 'hr',
                'purchase_requisition_department'],
    'data': ['view/logistic_requisition.xml',
             'view/logistic_requisition_line.xml',
             'view/logistic_requisition_source.xml'],
    'installable': True,
}
