# -*- coding: utf-8 -*-
# © 2016 Therp BV <http://therp.nl>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "Hide taxes (invoicing)",
    "version": "8.0.1.0.0",
    "author": "Therp BV,Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "category": "Accounting & Finance",
    "summary": "Hide taxes for most employees",
    "depends": [
        'account',
    ],
    "data": [
        "security/res_groups.xml",
        "data/ir_ui_menu.xml",
        "views/product_template.xml",
        "views/account_invoice.xml",
    ],
}
