from ga import GA
import numpy as np


class TestGA(GA):

    def initialize(self):
        return [self.rng.randn() for _ in range(100)]

    def cost(self, o):
        return np.abs(o)

    def mutate(self, organism):
        return organism + self.rng.randn() * 0.01

    def crossover(self, o1, o2):
        return min(o1, o2)


def main():
    ga = TestGA()
    print(ga.opt(generations=100))


if __name__ == '__main__':
    main()
