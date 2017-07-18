# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

{
    'name': 'NGO - Purchase Requisition',
    'summary': 'Base Purchase Requisition view for NGO',
    'version': '10.0.1.0.0',
    'category': 'Purchase Management',
    'author': 'Camptocamp,Odoo Community Association (OCA),\
            Serpent Consulting Services Pvt. Ltd.',
    'complexity': 'normal',
    'website': 'http://www.camptocamp.com',
    'license': 'LGPL-3',
    'depends': [
        'purchase_requisition',
        'purchase_requisition_bid_selection',
        'purchase_requisition_delivery_address',
        'purchase_requisition_auto_rfq',
        'purchase_requisition_transport_document',
    ],
    'data': [
        'views/purchase_order.xml',
        'views/purchase_requisition.xml',
    ],
    'installable': True,
    'auto_install': False,
}
