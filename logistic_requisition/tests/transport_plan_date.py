import time
import unittest2
from mock import MagicMock
import openerp.tests.common as common


class transport_plan_date(common.TransactionCase):

    def setUp(self):
        """I create a transport plan wizard with date set to %Y-03-01"""
        super(transport_plan_date, self).setUp()
        cr, uid = self.cr, self.uid
        self.wizard_date = time.strftime('%Y-03-01')
        self.logistic_transport_wizard = self.registry('logistic.requisition.source.transport.plan')
        self.wizard_br = MagicMock()
        self.wizard_br.date_etd = self.wizard_date
        self.wizard_br.from_address_id = self.browse_ref('base.res_partner_5')
        self.wizard_br.to_address_id = self.browse_ref('base.res_partner_6')
        self.wizard_br.transport_estimated_cost = 12000
        self.wizard_br.transport_mode_id = self.browse_ref('transport_plan.transport_mode1')
        self.wizard_br.note = "Mocked form"

    def test_01_eta_date_from_form(self):
        """If I have set an ETA date in tansport plan wizard,
        the wizard one should be used """
        cr, uid = self.cr, self.uid
        req_src_br_1 = MagicMock(name="br1")
        req_src_br_1.eta_date = '2000-01-01'
        self.wizard_br.date_eta = self.wizard_date
        res = self.logistic_transport_wizard._prepare_transport_plan(cr, uid, self.wizard_br,
                                                                     [req_src_br_1])
        self.assertEqual(res['date_eta'], self.wizard_date, "Date of wizard was not taken")

    def test_02_eta_date_from_line(self):
        """If I have NOT set an ETA date in tansport plan wizard,
        and I have only one requistion line, the date of the line must be used """
        cr, uid = self.cr, self.uid
        self.wizard_br.date_eta = False
        req_src_br_1 = MagicMock()
        req_src_br_1.date_eta = '2000-01-01'
        self.wizard_br.date_eta = False
        res = self.logistic_transport_wizard._prepare_transport_plan(cr, uid, self.wizard_br,
                                                                     [req_src_br_1])
        self.assertEqual(res['date_eta'], '2000-01-01', "Date of line was not taken")

    def test_03_eta_date_not_from_line(self):
        """If I have NOT set an ETA date in tansport wizard,
        and I have many lines the eta date of transport plan must not be set"""
        cr, uid = self.cr, self.uid
        self.wizard_br.date_eta = False
        req_src_br_1 = MagicMock(name="br1")
        req_src_br_1.date_eta = '2000-01-01'
        req_src_br_2 = MagicMock(name="br2")
        req_src_br_2.date_eta = '2000-01-01'
        self.wizard_br.date_eta = False
        res = self.logistic_transport_wizard._prepare_transport_plan(cr, uid, self.wizard_br,
                                                                     [req_src_br_1, req_src_br_2])
        self.assertEqual(res['date_eta'], False, "Date was set but It should not")

if __name__ == '__main__':
    unittest2.main()
