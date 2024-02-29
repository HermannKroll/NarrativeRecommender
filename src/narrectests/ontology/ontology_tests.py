import unittest

from narrec.ontology.ontology import Ontology


class OntologyTests(unittest.TestCase):

    def setUp(self):
        self.ontology = Ontology()

    def test_prefix_based_distance(self):
        tests = [("C01.069", "C01.221.500", 3),
                 ("C01.069", "C01.221.250.875", 4),
                 ("C01.069", "C01", 1),
                 ("C01.069", "D01", -1)]
        for a, b, goal in tests:
            self.assertEqual(goal, Ontology.prefix_based_distance(a, b))

        tests = [("C01,069", "C01,221,500", 3),
                 ("C01,069", "C01,221,250,875", 4),
                 ("C01,069", "C01", 1),
                 ("C01,069", "D01", -1)]
        for a, b, goal in tests:
            self.assertEqual(goal, Ontology.prefix_based_distance(a, b, denominator=','))

    def test_mesh_ontological_distance(self):
        tests = [("MESH:D015658", "MESH:D000785", 4),
                 ("MESH:D007239", "MESH:D000785", 1),
                 ("MESH:D007239", "MESH:D013514", -1)]

        for a, b, goal in tests:
            self.assertEqual(goal, self.ontology.ontological_mesh_distance(a, b))

    def test_chembl_prefix_based_distance(self):
        tests = [("R.06.AE.06", "R.06.AE.07", 2),
                 ("R.06.AE.06", "R.06.AE", 1),
                 ("R.06.AE.06", "R.06", 2),
                 ("R.06.AE.06", "D01", -1),
                 ("A.01.AA.01", "A.02.AA.01", 6)]
        for a, b, goal in tests:
            self.assertEqual(goal, Ontology.prefix_based_distance(a, b))

    def test_chembl_based_distance(self):
        tests = [("CHEMBL1528", "CHEMBL2106575", 2),
                 ("CHEMBL1528", "CHEMBL1200736", 6)]
        for a, b, goal in tests:
            self.assertEqual(goal, self.ontology.compute_chembl_ontological_distance(a, b))