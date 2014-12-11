Logistics Requisition - Donation
================================

This module adds a type `Donor Stock Dispatch` on Logisitcs Requisition

It allows to create logistics requisition to dispatch stock stored in
your warehouse and owned by other entities.

This kind of requisition will then generate a standard cost estimate.

When confirming a `Donor Stock Dispatch` requisition, source will be
created automatically as a warehouse dispatch sourcing if stock is found.

Otherwise it will create a source of type `Other`.

Contributors
------------

* Yannick Vaucher <yannick.vaucher@camptocamp.com>
