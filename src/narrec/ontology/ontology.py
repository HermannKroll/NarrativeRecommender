from narrant.entity.meshontology import MeSHOntology


class Ontology:

    def __init__(self):
        self.mesh_ontology = MeSHOntology.instance()

    @staticmethod
    def prefix_based_distance(a: str, b: str, denominator: str = '.') -> int:
        """
        Calculates the distance between two prefix-based ontology representations
        a = C01.069
        b = C01.221.500
        :param a: prefix-based ontology encoding a
        :param b: prefix-based ontology encoding b
        :param denominator: character to separate the ontological levels
        :return: Distance should be 3 (1 step upwards and two steps downwards)
        """
        parts_a = a.split(denominator)
        parts_b = b.split(denominator)

        # they do not agree on their first prefix
        if parts_a[0] != parts_b[0]:
            return -1

        # count the number of overlapping elements
        overlapping = 0
        if len(parts_a) <= len(parts_b):
            parts_shorter = parts_a
            parts_longer = parts_b
        else:
            parts_shorter = parts_b
            parts_longer = parts_a
        # test from shorter to longer
        for idx, pa in enumerate(parts_shorter):
            if pa == parts_longer[idx]:
                overlapping += 1
            else:
                break

        # we know how many parts to overlap
        # now count how many steps are necessary to come from a and b to that overlapping prefix
        distance = (len(parts_a) - overlapping) + (len(parts_b) - overlapping)
        return distance

    def ontological_mesh_distance(self, a, b) -> int:
        if not a.startswith('MESH:D'):
            return -1
        if not b.startswith('MESH:D'):
            return -1

        try:
            # find the tree numbers for a and b
            a_tree_nos = self.mesh_ontology.get_tree_numbers_for_descriptor(a[5:])
            b_tree_nos = self.mesh_ontology.get_tree_numbers_for_descriptor(b[5:])

            # compute the distances between all tree number pairs
            distances = []
            for a_tn in a_tree_nos:
                for b_tn in b_tree_nos:
                    dis = Ontology.prefix_based_distance(a_tn, b_tn)
                    if dis > 0:
                        distances.append(dis)
            if len(distances) > 0:
                # return the minimum ontological distance between a and b
                return min(distances)
            else:
                # we did not find any distance -> -1
                return -1

        except KeyError:
            # some descriptor does not have a tree number
            return -1

    def compute_ontological_distance(self, a: str, b: str) -> int:
        # if they are equal - 1.0
        if a == b:
            return 1.0
        # if both mesh descriptors
        if a.startswith('MESH:D') and b.startswith('MESH:D'):
            return self.ontological_mesh_similarity(a, b)
        # if both are chembl ids
        if a.startswith('CHEMBL') and b.startswith('CHEMBL'):
            return 0.0

        # TODO
        return 1


def main():
    pairs = [("C01.069", "C01.221.500"),
             ("C01.069", "C01.221.250.875")]
    for a, b in pairs:
        print(f'Distance between {a} and {b} is {Ontology.prefix_based_distance(a, b)}')


if __name__ == "__main__":
    main()
