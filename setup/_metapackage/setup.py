import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo8-addons-oca-vertical-ngo",
    description="Meta package for oca-vertical-ngo Odoo addons",
    version=version,
    install_requires=[
        'odoo8-addon-framework_agreement_requisition',
        'odoo8-addon-framework_agreement_sourcing',
        'odoo8-addon-framework_agreement_sourcing_stock_route_transit',
        'odoo8-addon-logistic_budget',
        'odoo8-addon-logistic_consignee',
        'odoo8-addon-logistic_order',
        'odoo8-addon-logistic_order_donation',
        'odoo8-addon-logistic_order_donation_budget',
        'odoo8-addon-logistic_order_donation_shipment_test',
        'odoo8-addon-logistic_order_donation_transit',
        'odoo8-addon-logistic_order_multicurrency',
        'odoo8-addon-logistic_order_requisition_donation',
        'odoo8-addon-logistic_requisition',
        'odoo8-addon-logistic_requisition_department',
        'odoo8-addon-logistic_requisition_donation',
        'odoo8-addon-logistic_requisition_multicurrency',
        'odoo8-addon-ngo_purchase',
        'odoo8-addon-ngo_purchase_requisition',
        'odoo8-addon-ngo_shipment_plan',
        'odoo8-addon-vertical_ngo',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
    ]
)
