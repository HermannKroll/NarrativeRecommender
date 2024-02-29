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
