import time
import unittest2
from mock import MagicMock, patch
import openerp.tests.common as common


class transport_plan_date(common.TransactionCase):

    def setUp(self):
        """I create a transport plan wizard with date set to %Y-03-01"""
        super(transport_plan_date, self).setUp()
        cr, uid = self.cr, self.uid
        self.wizard_date = time.strftime('%Y-03-01')
        self.logistic_transport_wizard = self.registry('logistic.requisition.source.transport.plan')

    def test_01_eta_date_from_source(self):
        """If I have set an ETA date in tansport plan wizard,
        the wizard one should be used """
        cr, uid = self.cr, self.uid
        req_src_br_1 = MagicMock(name="br1")
        req_src_br_1.requisition_line_id.date_delivery = '2000-01-01'
        with patch.object(self.logistic_transport_wizard, '_get_default_lines') as patched:
            patched.return_value = [req_src_br_1]
            res = self.logistic_transport_wizard._get_default_date_eta_from_lines(cr, uid, {})
        self.assertEqual(res, '2000-01-01', "Date of line was not taken")

    def test_02_eta_date_not_from_line(self):
        """If I have NOT set an ETA date in tansport wizard,
        and I have many lines the eta date of transport plan must not be set"""
        cr, uid = self.cr, self.uid
        req_src_br_1 = MagicMock(name="br1")
        req_src_br_1.requisition_line_id.date_delivery = '2000-01-01'
        req_src_br_2 = MagicMock(name="br2")
        req_src_br_2.requisition_line_id.date_delivery = '2000-01-01'
        with patch.object(self.logistic_transport_wizard, '_get_default_lines') as patched:
            patched.return_value = [req_src_br_1, req_src_br_2]
            res = self.logistic_transport_wizard._get_default_date_eta_from_lines(cr, uid, {})
        self.assertEqual(res, False, "Date of line was taken")

if __name__ == '__main__':
    unittest2.main()
