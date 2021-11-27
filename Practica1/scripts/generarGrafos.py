import string

# Librerias adicionales a instalar
import regex as re
from graphviz import Digraph
from cairosvg import svg2png

# Fichero de entrada, listado de expresiones UNL:
# [S:<número de oración>]
# {org}
# <oración original>
# {/org}
# {unl}
# <contenido>
# {/unl}
# [/S]
#
# [S:<número siguiente oración>]
# ...
input_file = 'grafos.txt'

# Directorio de salida
output_dir = '../Memoria/images'


def make_graph(edges, name):
    edges = clean_empty_edges(edges)
    nodes = extract_edges_nodes(edges)
    dot = Digraph(name=name)
    for node in nodes:
        dot.node(label=node, name=nodes[node])
    for e in edges:
        e_label = extract_edge_label(e)
        e_nodes = extract_edge_nodes(e)
        dot.edge(nodes[e_nodes[0]], nodes[e_nodes[1]], label=e_label)
    dot.render(directory=output_dir, format='svg')
    svg2png(url=f'{output_dir}{name}.gv.svg',
            write_to=f'{output_dir}{name}.gv.png',
            dpi=200)


def clean_empty_edges(edges):
    return list(filter(lambda e: bool(e), edges))


def extract_edge_nodes(edge):
    return re.findall(r'\(.*?\)', ''.join(edge.split()))[0][1:-1].split(',')


def extract_edges_nodes(edges):
    nodes = dict()
    ids = list(string.ascii_lowercase) + list(string.ascii_uppercase)
    id_idx = 0
    for e in edges:
        for n in extract_edge_nodes(e):
            nodes[n] = ids[id_idx]
            id_idx += 1
    return nodes


def extract_edge_label(edge):
    edge = ''.join(edge.split())
    return edge[:edge.index('(')]


with open(input_file, 'r') as f:
    text = ''.join(f.readlines())
    graphs = re.findall(r'\{unl\}(.*?)\{/unl\}', text, re.DOTALL)
    for i, g in enumerate(graphs):
        make_graph(g.splitlines(), f'unl_{i+1}')
