[![Build Status](https://travis-ci.org/OCA/vertical-ngo.svg?branch=8.0)](https://travis-ci.org/OCA/vertical-ngo)
[![Coverage Status](https://coveralls.io/repos/OCA/vertical-ngo/badge.png?branch=8.0)](https://coveralls.io/r/OCA/vertical-ngo?branch=8.0)

/!\ Under migration currently this is a copy paste of the Launchpad project !


This project aim to develop and publish all modules related to the need of humanitarian NGOs. It would cover the overall needs in terms of logistics, order management, accounting, transportation and distribution.

PLEASE PAY ATTENTION, THIS PROJECT IS UNDER GITHUB MIGRATION PROCESS, FOLLOW CHANGES HERE: https://docs.google.com/spreadsheets/d/1CfGY7rc60jnpAWvMfNf0pI7fBDAlumwI2jx6f_RJ4_4/edit#gid=0

Main changes are made in the procurement standard flow of OpenERP. Usually, you have sales that drive procurement, that drive purchase. With those modules, you record logistic requisition to capture the needs, you source them from one way or another (purchase, stock, donnation,..) and give back to the requestor the price, time and product information. If he agree with, then you confirm the requisition by creating an offer. The offer will drive all the necessary flow to deliver the good where they are needed. It also improve the purchase requisition flow to fit more with the NGO's problematic.

In the future, it'll cover other NGO's specific needs such as the distribution, transportation, finance (dontations, donors report,.. ), volonteer management,..

You'll find here :
----------------------

- Addons backport branches: That contain a specific addons branch of OpenERP with backport in 7.0 of the future improvements that will land in version 8.0 concerning the purchase and the purchase_requisition module

- NGO Addons: That contain the module specific to the NGO world (currently management of logistic reuquisition, kind of need registring and sourcing tools)

- Purchase workflow: That contain module to improve the purchase and purchase_requisition module, to make it work in a complexe structure. Those module need the addons-abckport branch, reason why they land here instead of the community module.

Other related community project where we put some useful module for NGO as well:
--------------------------------------------------------------------------------------------------------------------

 * https://github.com/OCA/stock-logistics-warehouse : module stock_reserve and stock_reserve_sale, stock_location_ownership

 * https://github.com/OCA/stock-logistics-workflow : module stock_split_picking

 * https://github.com/OCA/sale-workflow : module sale_validity, sale_sourced_by_line, sale_exception_nostock_by_line, sale_exception_nostock, sale_dropshipping, sale_cancel_reason, partner_prepayment
