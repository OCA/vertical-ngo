# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

{
    'name': 'NGO - Purchase Order',
    'summary': 'Base Purchase Order view for NGO',
    'version': '10.0.1.0.0',
    'author': 'Camptocamp,Odoo Community Association (OCA), \
         Serpent Consulting Services Pvt. Ltd.',
    'category': 'Purchase Management',
    'complexity': 'normal',
    'website': 'http://www.camptocamp.com',
    'license': 'LGPL-3',
    'depends': [
        'framework_agreement',
        'framework_agreement_requisition',
        'purchase_origin_address',
        'purchase_delivery_address',
        'purchase_requisition',
        'purchase_requisition_bid_selection',
        'purchase_rfq_bid_workflow',
        'purchase_transport_document',
    ],
    'data': [
        'views/purchase_order.xml',
    ],
    'installable': True,
    'auto_install': False,
}
