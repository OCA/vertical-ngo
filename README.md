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
[//]: # (end addons)
