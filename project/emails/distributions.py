from collections import Counter

import matplotlib.pyplot as plt
import networkx as nx

from project.emails.data.utils import log_binning

FILE_PATH = 'data/emails.txt'
FIGURES_PATH = 'figures/'


def graph_instance():
    g = nx.Graph()
    g.add_edges_from(edges_from_file(FILE_PATH))
    return g


def edges_from_file(path):
    edges = []
    with open(path, 'r') as file:
        for line in file.readlines()[1:]:
            node_from, node_to = map(int, line.split("\t"))
            edges.append([node_from, node_to])
    return edges


def degrees_distribution(graph):
    degs = sorted(graph.degree([node for node in graph.nodes()]).values(), reverse=True)

    deg_x, deg_y = log_binning(dict(Counter(degs)), 50)

    plt.figure()
    plt.scatter(deg_x, deg_y, c='r', marker='s', s=25, label='')
    plt.xscale('log')
    plt.yscale('log')
    plt.title('Degrees Distribution')
    plt.xlabel('k')
    plt.ylabel('Count')
    plt.savefig(FIGURES_PATH + 'degrees_distribution.png')


def average_degree(graph):
    degs = list(graph.degree([node for node in graph.nodes()]).values())
    return sum(degs) / len(graph.nodes())


g = graph_instance()
print(average_degree(g))