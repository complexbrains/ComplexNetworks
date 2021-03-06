import random
from typing import (
    List,
    Tuple
)

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
from tqdm import tqdm

from project.emails import common


def graph_from_gephi_edge_list(path: str) -> nx.Graph:
    with open(path, 'rb') as file:
        next(file, '')
        graph = nx.read_edgelist(file, nodetype=int)
        return graph


def fail(src_graph: nx.Graph) -> nx.Graph:
    graph = nx.Graph(src_graph)
    n = random.choice(list(graph.nodes()))
    graph.remove_node(n)

    return graph


def attack_degree(src_graph: nx.Graph) -> nx.Graph:
    # to modify the source graph you have to unfreeze it by creating a new graph
    graph = nx.Graph(src_graph)
    degrees = dict(graph.degree())
    max_degree = max(degrees.values())
    max_keys = [k for k, v in degrees.items() if v == max_degree]
    graph.remove_node(max_keys[0])

    return graph


def diameter_and_avg_path_length(graph: nx.Graph) -> Tuple[float, float]:
    max_path_length = 0
    total = 0.0
    for n in graph:
        path_length = nx.single_source_shortest_path_length(graph, n)
        total += sum(path_length.values())
        if max(path_length.values()) > max_path_length:
            max_path_length = max(path_length.values())
    try:
        avg_path_length = total / (graph.order() * (graph.order() - 1))
    except ZeroDivisionError:
        avg_path_length = 0.0
    return max_path_length, avg_path_length


def giant_component_fraction(graph: nx.Graph) -> float:
    components = sorted(nx.connected_component_subgraphs(graph), key=len, reverse=True)
    biggest_ga = components[0]

    return biggest_ga.size() / (len(graph.nodes()) * 1.0)


def robustness_by_attack(src_graph: nx.Graph, nodes_to_remove: int, measure_frequency: int) -> None:
    diameters_history: List[float] = []
    path_len_history: List[float] = []
    ga_fraction_history: List[float] = []

    print('---- Starting Robustness Check ---- \n')

    graph = src_graph
    for iteration in tqdm(range(nodes_to_remove)):
        graph = attack_degree(graph)

        if iteration % measure_frequency == 0:
            diameter, avg_path_len = diameter_and_avg_path_length(graph)

            diameters_history.append(diameter)
            path_len_history.append(avg_path_len)
            ga_fraction_history.append(giant_component_fraction(graph))

    print('---- Done: Robustness Check ---- \n')

    print(diameters_history)
    print(path_len_history)
    print(ga_fraction_history)

    dump_history(common.ROBUSTNESS_ATTACK_HISTORY, diameters_history, path_len_history, ga_fraction_history)


def robustness_by_fail(src_graph: nx.Graph, number_of_runs: int, nodes_to_remove: int, measure_frequency: int) -> None:
    diameters_history: List[List[float]] = []
    path_len_history: List[List[float]] = []
    ga_fraction_history: List[List[float]] = []

    print('---- Starting Robustness Check ---- \n')

    for _ in tqdm(range(number_of_runs)):
        graph = src_graph

        diameters_on_run: List[float] = []
        paths_on_run: List[float] = []
        ga_on_run: List[float] = []

        for iteration in tqdm(range(nodes_to_remove)):
            graph = fail(graph)
            if iteration % measure_frequency == 0:
                # diameter, avg_path_len = diameter_and_avg_path_length(graph)
                # diameters_on_run.append(diameter)
                # paths_on_run.append(avg_path_len)
                ga_on_run.append(giant_component_fraction(graph))

        diameters_history.append(diameters_on_run)
        path_len_history.append(paths_on_run)
        ga_fraction_history.append(ga_on_run)

    print('---- Done: Robustness Check ---- \n')

    print(diameters_history)
    print(path_len_history)
    print(ga_fraction_history)

    dump_history(common.ROBUSTNESS_FAIL_HISTORY, diameters_history,
                 path_len_history, ga_fraction_history, fail_mode=True)


def dump_history(file_path: str, diameters: List, paths: List, ga_fractions: List, fail_mode: bool = False) -> None:
    with open(file_path, 'w') as file:
        if not fail_mode:
            for param in [diameters, paths, ga_fractions]:
                file.write(f'{common.join_values(param)}\n')
        else:
            for run in range(len(diameters)):
                file.write(f'{run}\n')
                # file.write(f'{join_values(diameters[run])}\n')
                # file.write(f'{join_values(paths[run])}\n')
                file.write(f'{common.join_values(ga_fractions[run])}\n')


def normalized_robustness(data: List[float]) -> List[float]:
    return [value / data[0] for value in data]


def plot_robustness() -> None:
    with open(common.ROBUSTNESS_ATTACK_HISTORY) as attack_file:
        attack_history = [float(val) for line in attack_file for val in line.split()]

    attack_history = normalized_robustness(attack_history)

    with open(common.ROBUSTNESS_FAIL_HISTORY) as fail_file:
        fail_history: List[List[float]] = []
        num_of_runs = 5

        for run in range(num_of_runs):
            next(fail_file)
            line = next(fail_file)
            fail_history.append([float(val) for val in line[:-1].split(' ')])

            fail_history[run] = normalized_robustness(fail_history[run])
            print(fail_history[run])

    nodes_removed = np.linspace(0, 100, len(attack_history))

    plt.plot(nodes_removed, attack_history, label='Attack by degree')
    plt.xlabel('Removed nodes, %')
    plt.ylabel('Fraction of nodes')
    plt.title('Dynamics of the fraction of nodes in giant component')
    plt.legend()
    plt.plot(nodes_removed, fail_history[0])
    plt.show()


if __name__ == '__main__':
    g = graph_from_gephi_edge_list(common.REDUCED_GRAPH_PATH)

    robustness_by_attack(g, int(0.9 * len(g.nodes())), 50)
    robustness_by_fail(g, 3, int(0.9 * len(g.nodes())), 50)

    plot_robustness()
