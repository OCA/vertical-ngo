This module allows you to manage your Logistic Requisitions.
============================================================

A Logistic requisition express a need that is requested somewhere.
It allows to manage the sourcing of the needs before making a cost estimate to
the requestor.

This invert the logic that is in standard in Odoo in the way that the sourcing
of the procuremnt is made before the order confirmation and we built the link
incase of validation. In standard, th SO confirmation generate the procurement
then it generate the needed procurement.

The sourcing can be of various type:

 * Warehouse dispatch: You will deliver the requested goods from one of your
 stock location
 * Procurement: You will go for tender to chose the best supplier for the
 required goods
 * Framework agreement: You will use the existing Framework agreement
 * Other: Nothing of those choices. In that case, the line can be selected
and included in either a PO or a tender

The simple process is the following:

 * LR are recorded to represent the need of the customer/requestor
 * LR are confirmed and sourced by different way (dispatch, tender, ..)
 * If sourced from tender, you need to go all along the tendering process
   (CBA).
 Once you chose one bid, the system will automatically put back the prices
 information on the sourcing line of the LR.
  * You can create a cost estimate from sourced LR lines for your
 resquestor/customer
 * If the requestor accepts the cost estimate, his validation will
   automatically:
   * Create the link between the chosen winning bid and the line sourced this
     way. A new draft PO will be generatedand managed as drop shipping.
   * Lines sourced as a dispatch will create a delivery order.
   * Lines sourced a LTA will create a PO of type LTA


Contributors
------------

* Joël Grand-Guillaume <joel.grandguillaume@camptocamp.com>
* Jacques-Etienne Baudoux <je@bcim.be>
* Guewen Baconnier <guewen.baconnier@camptocamp.com>
* Nicolas Bessi <nicolas.bessi@camptocamp.com>
* Yannick Vaucher <yannick.vaucher@camptocamp.com>
