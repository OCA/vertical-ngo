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


Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/OCA/vertical-ngo/issues>`_.
In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us smashing it by providing a detailed and welcomed feedback
`here <https://github.com/OCA/vertical-ngo/issues/new?body=module:%20logistic_requisition_multicurrency%0Aversion:%208.0%0A%0A**Steps%20to%20reproduce**%0A-%20...%0A%0A**Current%20behavior**%0A%0A**Expected%20behavior**>`_.


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
