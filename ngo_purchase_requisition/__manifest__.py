# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

{'name': 'NGO - Purchase Requisition',
 'summary': 'Base Purchase Requisition view for NGO',
 'version': '10.0.1.0.0',
 'author': 'Camptocamp,Odoo Community Association (OCA),\
         Serpent Consulting Services Pvt. Ltd.',
 'license': 'AGPL-3',
 'category': 'Purchase Management',
 'complexity': 'normal',
 'website': 'http://www.camptocamp.com',
 'depends': ['purchase_requisition',
             'purchase_requisition_bid_selection',
             'purchase_requisition_delivery_address',
             'purchase_requisition_auto_rfq',
             'purchase_requisition_transport_document',
             ],
 'data': ['view/purchase_order.xml',
          'view/purchase_requisition.xml',
          ],
 'installable': True,
 'auto_install': False,
}
