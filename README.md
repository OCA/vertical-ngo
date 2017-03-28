[![Build Status](https://travis-ci.org/OCA/vertical-ngo.svg?branch=10.0)](https://travis-ci.org/OCA/vertical-ngo)
[![Coverage Status](https://coveralls.io/repos/OCA/vertical-ngo/badge.svg?branch=10.0)](https://coveralls.io/r/OCA/vertical-ngo?branch=10.0)


This project aim to develop and publish all modules related to the need of
humanitarian NGOs. It would cover the overall needs in terms of logistics,
order management, accounting, transportation and distribution.

Main changes are made in the procurement standard flow of Odoo. Usually, you
have sales that drive procurement, that drive purchase. With those modules, you
record logistic requisition to capture the needs, you source them from one way
or another (purchase, stock, donnation,..) and give back to the requestor the
price, time and product information. If he agree with, then you confirm the
requisition by creating an offer. The offer will drive all the necessary flows
to deliver the goods where they are needed. It also improves the purchase
requisition flow to fit more with the NGO's problematic.

In the future, it'll cover other NGO's specific needs such as the distribution,
transportation, finance (donations, donors report,.. ), volonteer management,..

You'll find here :
----------------------

- NGO Addons: That contain the module specific to the NGO world (currently
  management of logistic reuquisition, kind of need registring and sourcing
  tools)


Other related community project where we put some useful module for NGO as well
-------------------------------------------------------------------------------

 * https://github.com/OCA/stock-logistics-transport : module
   `stock_route_transit`, `stock_shipment_management`, `transport_information`

 * https://github.com/OCA/stock-logistics-warehouse : module `stock_reserve`
   and `stock_reserve_sale`, `stock_location_ownership`

 * https://github.com/OCA/stock-logistics-workflow : module
   `stock_split_picking`

 * https://github.com/OCA/sale-workflow : module `sale_validity`,
   `sale_quotation_sourcing`, `sale_sourced_by_line`, `sale_exception_nostock`,
   `sale_cancel_reason`, `partner_prepayment`

[//]: # (addons)

Unported addons
---------------
addon | version | summary
--- | --- | ---
[framework_agreement_requisition](framework_agreement_requisition/) | 8.0.1.0.0 (unported) | Framework Agreement Negociation in the Tender
[framework_agreement_sourcing](framework_agreement_sourcing/) | 8.0.2.0.0 (unported) | Sourcing with Framework Agreements
[framework_agreement_sourcing_stock_route_transit](framework_agreement_sourcing_stock_route_transit/) | 8.0.0.1.0 (unported) | Sourcing for Framework Agreement with Transit routes
[logistic_budget](logistic_budget/) | 8.0.2.3.1 (unported) | Logistics Budget
[logistic_consignee](logistic_consignee/) | 8.0.0.1.0 (unported) | Deprecated: use purchase_requisition_transport_multi_address, purchase_transport_multi_address, sale_transport_multi_address, stock_transport_multi_address
[logistic_order](logistic_order/) | 8.0.0.3.1 (unported) | Sales Order as Logistics Order
[logistic_order_donation](logistic_order_donation/) | 8.0.0.2.0 (unported) | Sales Order as In-Kind Donations
[logistic_order_donation_budget](logistic_order_donation_budget/) | 8.0.0.1.0 (unported) | Budget management for In-Kind Donations
[logistic_order_donation_shipment_test](logistic_order_donation_shipment_test/) | 8.0.0.1.0 (unported) | Test coexistence of Shipment management and Logistic Order Donations
[logistic_order_donation_transit](logistic_order_donation_transit/) | 8.0.0.1.0 (unported) | Transit management for Logistic Order Donations
[logistic_order_multicurrency](logistic_order_multicurrency/) | 8.0.0.1.0 (unported) | Multicurrency management
[logistic_order_requisition_donation](logistic_order_requisition_donation/) | 8.0.0.1.0 (unported) | Adapt views and fields
[logistic_requisition](logistic_requisition/) | 8.0.1.4.1 (unported) | Logistics Requisition
[logistic_requisition_department](logistic_requisition_department/) | 8.0.1.2.0 (unported) | Logistic Requisitions with Department Categorization
[logistic_requisition_donation](logistic_requisition_donation/) | 8.0.0.1.0 (unported) | Manage Donor Warehouse Dispatch with Logistics Requisition
[logistic_requisition_multicurrency](logistic_requisition_multicurrency/) | 8.0.0.1.1 (unported) | Multicurrency management for logistics requistion
[ngo_purchase](ngo_purchase/) | 8.0.1.2.0 (unported) | Base Purchase Order view for NGO
[ngo_purchase_requisition](ngo_purchase_requisition/) | 8.0.2.0.0 (unported) | Base Purchase Requisition view for NGO
[ngo_shipment_plan](ngo_shipment_plan/) | 8.0.0.1.0 (unported) | Adaptations of Shipment Management for NGO
[vertical_ngo](vertical_ngo/) | 8.0.0.1.0 (unported) | Odoo NGO Verticalization

[//]: # (end addons)
