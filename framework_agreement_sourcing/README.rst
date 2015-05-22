Sourcing with Framework Agreements
==================================

If you have a framework agreement negociated for the current product in
your logistic requisition, a sourcing of type "agreement" will be generated.

This sourcing allows the user to choose an agreement that will be used to
create directly a purchase order at the validation of the requisition. This
bypasses the tender flow.

Version 2.0 brings compatibility with version 2.0 of the module
framework_agreement, that introduced the concept of agreement portfolios.

Also, since 2.0 the choice of which agreement to use for a sourcing is up to
the user. The system will only propose an agreement if there is only one for
the portfolio, date, incoterm, and product selected.


Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/OCA/vertical-ngo/issues>`_.
In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us smashing it by providing a detailed and welcomed feedback
`here <https://github.com/OCA/vertical-ngo/issues/new?body=module:%20framework_agreement_sourcing%0Aversion:%208.0%0A%0A**Steps%20to%20reproduce**%0A-%20...%0A%0A**Current%20behavior**%0A%0A**Expected%20behavior**>`_.


Credits
=======

Contributors
------------

* Nicolas Bessi <nicolas.bessi@camptocamp.com>
* Yannick Vaucher <yannick.vaucher@camptocamp.com>
* Leonardo Pistone <leonardo.pistone@camptocamp.com>


Maintainer
----------

.. image:: http://odoo-community.org/logo.png
   :alt: Odoo Community Association
   :target: http://odoo-community.org

This module is maintained by the OCA.

OCA, or the Odoo Community Association, is a nonprofit organization whose mission is to support the collaborative development of Odoo features and promote its widespread use.

To contribute to this module, please visit http://odoo-community.org.
