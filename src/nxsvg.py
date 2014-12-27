__all__ = ['SVGRenderer']
from svgwrite.path import Path
from svgwrite.shapes import Rect, Line, Polygon
from svgwrite.text import Text, TextPath, TSpan
from svgwrite.container import Marker, Group
from svgwrite import Drawing
import math

def DefaultNodeFormatter(node, data):
    return 'Node[%d]\n%s' % (node, str(data)), {}
def DefaultEdgeFormatter(u, v, data):
    return 'Edge[%d, %d]:%s' % (u, v, str(data)), {}
def midpoint(p1, p2):
    return (p1[0] + p2[0]) * 0.5, (p1[1] + p2[1]) * 0.5

def RichText(s, dy, **kwargs):
    """ parse and create a center aligned multiline Text object:
          dy linespacing.

        coordinates are in viewbox

        vertical baseline is the baseline of the last line
    """
    lines = s.split('\n')
    x, y = kwargs.pop('insert', (0, 0))
    y = y - dy * (len(lines) - 1)
    txt = Text('', insert=(x, y), **kwargs)
    for i, line in enumerate(lines):
        if len(line) > 0:
            if i == 0:
                font_weight='bold'
            else:
                font_weight='normal'
            ts = TSpan(line, x=[x], y=[y + dy * i], 
                    font_weight=font_weight, 
                    **kwargs)
            txt.add(ts)
    return txt


class SVGRenderer(object):
    def __init__(self, 
            GlobalScale=1000., 
            Padding = 10., 
            LineWidth = '1px', 
            FontSize = 20.,
            LineSpacing = 1.5):

        self.GlobalScale = GlobalScale
        self.Padding = Padding
        self.LineWidth = LineWidth
        self.FontSize = FontSize
        self.LineSpacing = LineSpacing

    def get_size(self, labeltxt):
        """ return size of label text in unitary cooridnate """
        lines = labeltxt.split('\n')
        tw = max([len(line) for line in lines])
        th = len(lines)
        fac = self.FontSize / self.GlobalScale
        width = tw * fac
        height = th * fac * self.LineSpacing
        return width, height

    def get_anchor(self, pos, otherpos):
        """ returns the anchor point of the edge
            in size of the node box
        """
        anchors = [
                (1.0, 0.5),
                (0.5, 0.0),
                (0., 0.5),
                (0.5, 1.0)]
        diff = (otherpos[0] - pos[0], otherpos[1] - pos[1])
        # the svg coordinate has wrong handness
        ang = math.atan2(-diff[1], diff[0])
        ang = int(ang / math.pi * 180)
        ang += 45
        if ang < 0:
            ang += 360
        if ang >= 360:
            ang -= 360
        phase = ang // 90
        #print pos, otherpos, ang, phase, anchors[phase]
        return anchors[phase]
    def scale(self, v):
        """ scale from unitary coordinate to SVG viewbox """
        return v[0] * self.GlobalScale, v[1] * self.GlobalScale
    def clip(self, v, s):
        """ clip the position of a node box in unitary coordinate """
        p = self.Padding / self.GlobalScale
        def f(a, b):
            if a + b > 1.0 - p:
                return 1.0 - p- b
            if a < p:
                return p
            return a
        return tuple([f(a, b) for a, b in zip(v, s)])

    def draw(self, g, pos, 
            size=('1200px', '1200px'), 
            nodeformatter=DefaultNodeFormatter, 
            edgeformatter=DefaultEdgeFormatter):
        """ formatter returns a string and a dict of the attributes(undefined yet)"""
        dwg = Drawing(size=size) #, profile='basic', version=1.2)
        dwg.viewbox(minx=0, miny=0, width=self.GlobalScale, height=self.GlobalScale)
        dwg.fit()
        if g.is_directed():
            # now add the marker
            marker = Marker(orient='auto', markerUnits="strokeWidth", size=(20, 20), refX=1.0, refY=0.5)
            marker.viewbox(minx=0, miny=0, width=1, height=1)
            marker.add(Polygon(points=[(0, 0.2), (1, 0.5), (0, 0.8)], fill='black', stroke='none'))
            dwg.defs.add(marker)

        pos = pos.copy()
        x = []
        y = []
        size = {}

        for node, data in g.nodes_iter(data=True):
            p = pos[node]
            label, prop = nodeformatter(node, data)
            size[node] = self.get_size(label)
            x.append(p[0])
            y.append(p[1])

        xmin = min(x)
        xmax = max(x)
        ymin = min(y)
        ymax = max(y)

        # normalize input pos to 0 ~ 1
        for node in g.nodes_iter():
            p = pos[node]
            p = ((p[0] - xmin) / (xmax - xmin),
                 (p[1] - ymin) / (ymax - ymin) )

            wh = size[node]
            p = self.clip(p, wh)
            pos[node] = p

        # draw the nodes
        for node, data in g.nodes_iter(data=True):
            label, prop = nodeformatter(node, data)
            p = pos[node]
            wh = size[node]
            wh, p = self.scale(wh), self.scale(p)
            grp = Group()
            ele = Rect(insert=p, size=wh, 
                    stroke_width=self.LineWidth,
                    stroke='black',
                    fill='none',
                    rx=self.FontSize,
                    ry=self.FontSize,
                    )
            grp.add(ele)
            txtp = p[0] + wh[0] * 0.5, p[1] + wh[1]

            txt = RichText(label, 
                    dy=self.LineSpacing * self.FontSize,
                    insert=txtp, 
                    font_family='monospace', 
                    font_size=self.FontSize, 
                    text_anchor="middle")

            # raise away from the edge by half a line
            txt.translate(tx=0, ty=-self.FontSize * 0.5)
            grp.add(txt)
            dwg.add(grp)

        # draw the edges
        drawn = {}
        for u, v, data in g.edges_iter(data=True):
            label, prop = edgeformatter(u, v, data)
            p1 = pos[u]
            p2 = pos[v]
            a = self.get_anchor(p1, p2)
            p1 = p1[0] + size[u][0] * a[0], p1[1] + size[u][1] * a[1]
            a = self.get_anchor(p2, p1)
            p2 = p2[0] + size[v][0] * a[0], p2[1] + size[v][1] * a[1]
            p1 = p1[0], p1[1]
            p2 = p2[0], p2[1]
            p1 = self.scale(p1)
            p2 = self.scale(p2)

            # parallel edges
            nedges = g.number_of_edges(u, v)
            if g.is_directed():
                nedges += g.number_of_edges(v, u)
            if u <= v:
                key = (u, v)
            else:
                key = (v, u)
            i = drawn.pop((u, v), 0)
            drawn[(u, v)] = i + 1
            i =  2 * i - (nedges - 1)
            ang = math.atan2((p2[1] - p1[1]), p2[0] - p1[0]) 

            l = ((p2[1] - p1[1]) ** 2 + (p2[0] - p1[0]) ** 2) ** 0.5
            dx = -(p2[1] - p1[1]) / l 
            dy = (p2[0] - p1[0]) / l 

            # control point in the middle
            txtp = (p1[0] + p2[0]) * 0.5 + 2 * self.FontSize * i * dx, \
                    (p1[1] + p2[1]) * 0.5 + 2 * self.FontSize * i * dy 
            controlp = tuple([
                    (txtp[i] - (p1[i] + p2[i]) * 0.25) * 2
                    for i in range(2)])
                    
            grp = Group()
            if g.is_directed():
                edge = Path(d=[
                        ('M', p1[0], p1[1]), 
                        ('Q', midpoint(p1, controlp), txtp),
                        ('Q', midpoint(controlp, p2), p2),
                        ],
                        marker_mid=marker.get_funciri(), 
                        #marker_end=marker.get_funciri(), 
                        stroke_width=self.LineWidth, 
                        fill='none',
                        stroke='black')
            else:
                edge = Path(d=[('M', p1[0], p1[1]), (txtp[0], txtp[1]), (p2[0], p2[1])], 
                        stroke_width=self.LineWidth, 
                        stroke='black')
            grp.add(edge)
            txt = RichText(label, 
                    dy=self.LineSpacing * self.FontSize,
                    font_size=self.FontSize, 
                    font_family='monospace', 
                    text_anchor="middle",
                    insert=txtp, 
                    )
            # I am confused by there is no negtive sign before y diff
            txt.rotate( 180. / math.pi * ang + 180,
                    center=txtp)
            # raise away from the edge by half a line
            txt.translate(tx=0, ty=-self.FontSize * 0.5)
            grp.add(txt)
            dwg.add(grp)
        return dwg.tostring()

def test():
    import networkx as nx
    g = nx.MultiDiGraph()

    g.add_star(range(4))
    g.add_star(range(4))
    g.add_cycle(range(4))
    #pos = nx.spring_layout(g)
    pos = nx.shell_layout(g)
    red = SVGRenderer() 
    print red.draw(g, pos)

if __name__ == "__main__":
    test()
