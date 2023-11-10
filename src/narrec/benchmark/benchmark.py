from abc import abstractmethod


class Benchmark:

    def __init__(self):
        self.doc2recommended = {}
        self.doc2not_recommended = {}

    @abstractmethod
    def load_benchmark_data(self):
        raise NotImplementedError
