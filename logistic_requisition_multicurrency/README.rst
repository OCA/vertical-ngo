Logistics Requisition - Multicurrency
=====================================

This module extends **Logistics Requisition** (`logistic_requisition`).
It adds a field on each object Logistics Requisition, Logistics Requisition Line
and Logistics Requisition Source to display amount in company currency.

Displayed amount in company currency are converted from requisition currency to company currency
at rates of requisition date.

Installation
============

Considering that you already use the module **Logistics Requisition**, you
just have to install this extension.

Configuration
=============

You will certainly want to enable in *Settings -> Configuration*:
- *Purchases -> Manage pricelists per supplier*
- *Invoicing -> Allow multi-currency*

Known issues / Roadmap
======================

Credits
=======

Contributors
------------

* Yannick Vaucher <yannick.vaucher@camptocamp.com>

Maintainer
----------

.. image:: http://odoo-community.org/logo.png
 :alt: Odoo Community Association
 :target: http://odoo-community.org

This module is maintained by the OCA.

OCA, or the Odoo Community Association, is a nonprofit organization whose mission is to support the collaborative development of Odoo features and promote its widespread use.

To contribute to this module, please visit http://odoo-community.org.
