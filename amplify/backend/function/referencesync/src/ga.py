from copy import deepcopy
from typing import List

import numpy as np


def sort_population(costs, population):
    sorted_indices = np.argsort(costs)
    elite = population[sorted_indices]
    elite_costs = costs[sorted_indices]
    return elite, elite_costs


def selection(costs, population, selection_fraction: float):
    select_k = int(len(population) * selection_fraction)
    population_sorted, costs_sorted = sort_population(costs, population)
    return population_sorted[:select_k], costs_sorted[:select_k]


class GA:
    def __init__(self):
        self.rng = np.random.RandomState(0)

    def opt(self, generations=3, cost_threshold=1, selection_fraction=0.5):
        population = np.array(self.initialize())
        population_size = len(population)
        elite = None

        best_costs = []
        for i in range(generations):
            costs = self.compute_costs(population)
            elite, elite_costs = selection(costs, population, selection_fraction)

            best_cost = elite_costs[0]
            best_costs.append(best_costs)
            if best_cost < cost_threshold:
                break

            elite_mutated = np.array([self.mutate(o) for o in elite])
            population = self.crossover_population(elite_mutated, population_size)

        return elite[0]

    def compute_costs(self, population):
        return np.array([self.cost(o) for o in population])

    def crossover_population(self, elite, population_size):
        new_population = deepcopy(elite).tolist()
        while True:
            i, j = self.rng.randint(0, elite.size, 2)
            new_organism = self.crossover(elite[i], elite[j])
            new_population.append(new_organism)
            if len(new_population) == population_size:
                return np.array(new_population)

    def initialize(self) -> List:
        raise NotImplementedError()

    def mutate(self, organism):
        raise NotImplementedError()

    def crossover(self, o1, o2):
        raise NotImplementedError()

    def cost(self, o):
        raise NotImplementedError()
