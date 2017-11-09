import nxsvg
import networkx as nx
from sys import stdout

G = nx.DiGraph()
G.add_cycle(range(4))
G.add_node(0, stroke='red', fill='pink', position=(0, 0))
G.add_node(1, rx=0, ry=0, position=(1, -1))
G.add_node(2, rx=0, ry=0, position=(2, -1))
G.add_node(3, rx=0, ry=0, position=(3, 0), fill='#00ffff', label="3")
G.add_edge(0, 1, stroke='red', stroke_dasharray='5 5')
G.add_edge(3, 3, label='a')

rend = nxsvg.SVGRenderer()
stdout.write(rend.draw(G, size=('1000px', '400px')))
