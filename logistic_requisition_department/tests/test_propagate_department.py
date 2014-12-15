from openerp.tests.common import TransactionCase


class TestPropagateDepartment(TransactionCase):
    def setUp(self):
        super(TestPropagateDepartment, self).setUp()

        self.lrs = self.env['logistic.requisition.source'].new({
            'name': '/',
        })
        self.dep_rd = self.env.ref('hr.dep_rd')

    def test_it_propagates_empty_department(self):
        pr_data = self.lrs._prepare_po_requisition([])
        self.assertFalse(pr_data.get('department_id'))

    def test_it_propagates_a_department(self):
        self.lrs.department_id = self.dep_rd
        pr_data = self.lrs._prepare_po_requisition([])
        self.assertEqual(self.dep_rd.id, pr_data.get('department_id'))
