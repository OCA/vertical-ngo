# -*- coding: utf-8 -*-
##############################################################################
#
#    Author:  Joël Grand-Guillaume
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

{
    "name" : "Logisitc Request",
    "version" : "0.1",
    "author" : "OpenERP SA",
    "category" : "Purchase Management",
    'complexity': "normal",
    "images" : [],
    "website" : "http://www.openerp.com",
    "description": """
This module allows you to manage your Logistic Request.
===========================================================

When a purchase order is created, you now have the opportunity to save the related request.
This new object will regroup and will allow you to easily keep track and order all your purchase orders.
""",
    "depends" : [
        "purchase",
        "mrp" # May be not needed
        ],
    "demo_xml" : ['data/logistic_request_demo.xml'],
    "data" : [
            "security/logistic_request.xml",
            "security/ir.model.access.csv",
            "wizard/logistic_request_partner_view.xml",
            "data/logistic_request_data.xml",
            "data/logistic_request_sequence.xml",
            "view/logistic_request_view.xml",
            "logistic_request_report.xml",
            "logistic_workflow.xml",
    ],
    "auto_install": False,
    "test":[],
    "installable": True,
    "certificate" : "",
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

