#!/usr/bin/env python3
"""
Small two-layer grid router used by gen_pcb.py (no external autorouter).

Model
- The board is rasterised on a GRID mm lattice; layer 0 = F.Cu, 1 = B.Cu.
- For every layer and every width class there is an int32 "owner" map:
      0  free,  k > 0  only net code k may use the cell,  -1  nobody may.
  An obstacle of net k marks every cell whose centre lies within
  clearance + class half-width + SLACK of its copper. A track whose centre line
  only visits free/own cells therefore keeps the clearance (SLACK covers the
  half-diagonal between lattice points).
- A* runs over (layer, cell, heading) with turn penalties, per-layer costs and
  a via move. A connection starts on the copper of one cluster of the net and
  ends on any copper already connected to the growing tree (Prim order).
- GND is not routed as a net: every GND pad gets a short stub to a via (fanout)
  and the planes are poured by gen_pcb.py; stitching vias are added at the end.

Everything here is deterministic: the same board in gives the same tracks out.
"""
import heapq
import math

import numpy as np
import pcbnew

SQ2 = math.sqrt(2.0)
DIRS = [(1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1)]
STEP = [1.0, SQ2, 1.0, SQ2, 1.0, SQ2, 1.0, SQ2]
LAYERS = (pcbnew.F_Cu, pcbnew.B_Cu)
NOHEAD = 8


def to_mm(v):
    return v / 1e6


class Router:
    def __init__(self, board, ox, oy, w, h, grid=0.1, clearance=0.2, edge_clearance=0.3,
                 classes=None, slack=None):
        self.board = board
        self.ox, self.oy = ox, oy
        self.g = grid
        self.nx = int(round(w / grid)) + 1
        self.ny = int(round(h / grid)) + 1
        self.N = self.nx * self.ny
        self.clr = clearance
        self.edge_clr = edge_clearance
        self.slack = grid * 0.75 if slack is None else slack
        # class name -> half width of the copper that will occupy a cell centre
        self.classes = classes or {"w25": 0.125, "w30": 0.15, "w40": 0.20, "w50": 0.25, "via": 0.30}
        self.owner = {c: np.zeros((2, self.ny, self.nx), np.int32) for c in self.classes}
        self.via_block = np.zeros((self.ny, self.nx), bool)        # no via for any net
        self.via_block_sig = np.zeros((self.ny, self.nx), bool)    # no via except GND
        self.hole_block = np.zeros((self.ny, self.nx), bool)       # too close to a drilled hole
        self.hole_to_hole = 0.5
        self.via_drill = 0.3
        self.xs = np.arange(self.nx) * grid
        self.ys = np.arange(self.ny) * grid
        self.netcode = {}
        for name, ni in board.GetNetsByName().items():
            self.netcode[str(name)] = ni.GetNetCode()
        self.log = []
        self.unrouted = []

    # ------------------------------------------------------------ geometry helpers
    def _win(self, x0, y0, x1, y1):
        g = self.g
        i0 = max(int(math.floor(x0 / g)), 0)
        i1 = min(int(math.ceil(x1 / g)) + 1, self.nx)
        j0 = max(int(math.floor(y0 / g)), 0)
        j1 = min(int(math.ceil(y1 / g)) + 1, self.ny)
        if i0 >= i1 or j0 >= j1:
            return None
        X, Y = np.meshgrid(self.xs[i0:i1], self.ys[j0:j1])
        return (slice(j0, j1), slice(i0, i1)), X, Y

    @staticmethod
    def _seg_dist(X, Y, ax, ay, bx, by):
        vx, vy = bx - ax, by - ay
        L2 = vx * vx + vy * vy
        if L2 < 1e-12:
            return np.hypot(X - ax, Y - ay)
        t = np.clip(((X - ax) * vx + (Y - ay) * vy) / L2, 0.0, 1.0)
        return np.hypot(X - (ax + t * vx), Y - (ay + t * vy))

    def _poly_inside(self, X, Y, pts, inset=0.0):
        """Lattice points inside a closed polygon, at least `inset` from its boundary."""
        n = len(pts)
        inside = np.zeros(X.shape, bool)
        d = np.full(X.shape, np.inf)
        for i in range(n):
            ax, ay = pts[i]
            bx, by = pts[(i + 1) % n]
            cond = ((ay > Y) != (by > Y))
            with np.errstate(divide="ignore", invalid="ignore"):
                xc = (bx - ax) * (Y - ay) / (by - ay + 1e-30) + ax
            inside ^= cond & (X < xc)
            d = np.minimum(d, self._seg_dist(X, Y, ax, ay, bx, by))
        return inside & (d >= inset)

    def _poly_dist(self, X, Y, pts):
        """Distance to a closed polygon, 0 inside."""
        n = len(pts)
        inside = np.zeros(X.shape, bool)
        d = np.full(X.shape, np.inf)
        for i in range(n):
            ax, ay = pts[i]
            bx, by = pts[(i + 1) % n]
            if (ay > Y).any() or (by > Y).any():
                cond = ((ay > Y) != (by > Y))
                with np.errstate(divide="ignore", invalid="ignore"):
                    xc = (bx - ax) * (Y - ay) / (by - ay + 1e-30) + ax
                inside ^= cond & (X < xc)
            d = np.minimum(d, self._seg_dist(X, Y, ax, ay, bx, by))
        d[inside] = 0.0
        return d

    def _mark(self, layer, net, win, d, extra=0.0):
        """Mark an obstacle (distance field d of its copper) in every class map."""
        sl, _, _ = win
        for c, hw in self.classes.items():
            R = self.clr + hw + self.slack + extra
            m = d <= R
            if not m.any():
                continue
            sub = self.owner[c][layer][sl]
            if net > 0:
                clash = m & (sub != 0) & (sub != net)
                sub[m & (sub == 0)] = net
                sub[clash] = -1
            else:
                sub[m] = -1

    def _block(self, layer, win, d, track_extra_ok=False):
        """Rule-area style keepout: copper of any net must stay out of the area."""
        sl, _, _ = win
        for c, hw in self.classes.items():
            if c == "via":
                continue
            m = d <= hw + self.slack
            self.owner[c][layer][sl][m] = -1

    # ------------------------------------------------------------ obstacles
    def shape_points(self, poly_set):
        out = []
        for i in range(poly_set.OutlineCount()):
            ol = poly_set.Outline(i)
            pts = [(to_mm(ol.CPoint(j).x) - self.ox, to_mm(ol.CPoint(j).y) - self.oy) for j in range(ol.PointCount())]
            out.append(pts)
        return out

    def add_pad(self, pad):
        net = pad.GetNetCode()
        for li, L in enumerate(LAYERS):
            if not pad.IsOnLayer(L):
                continue
            ps = pad.GetEffectivePolygon(L, pcbnew.ERROR_INSIDE)
            for pts in self.shape_points(ps):
                xs = [p[0] for p in pts]
                ys = [p[1] for p in pts]
                m = max(self.classes.values()) + self.clr + self.slack + 0.1
                win = self._win(min(xs) - m, min(ys) - m, max(xs) + m, max(ys) + m)
                if win is None:
                    continue
                d = self._poly_dist(win[1], win[2], pts)
                self._mark(li, net, win, d)

    def pad_cells(self, pad):
        """(layer, flat index) of lattice points inside the pad copper (polygon approximated from
        the inside and 0.02 mm inset, so a track ending there is certainly on the pad)."""
        cells = []
        for li, L in enumerate(LAYERS):
            if not pad.IsOnLayer(L):
                continue
            ps = pad.GetEffectivePolygon(L, pcbnew.ERROR_OUTSIDE)
            for pts in self.shape_points(ps):
                xs = [p[0] for p in pts]
                ys = [p[1] for p in pts]
                win = self._win(min(xs), min(ys), max(xs), max(ys))
                if win is None:
                    continue
                ins = self._poly_inside(win[1], win[2], pts, inset=0.02)
                sl = win[0]
                jj, ii = np.nonzero(ins)
                for j, i in zip(jj + sl[0].start, ii + sl[1].start):
                    cells.append((li, int(j) * self.nx + int(i)))
            if not cells:
                p = pad.GetPosition()
                i = int(round((to_mm(p.x) - self.ox) / self.g))
                j = int(round((to_mm(p.y) - self.oy) / self.g))
                cells.append((li, j * self.nx + i))
        return cells

    def add_segment(self, layer, net, a, b, width):
        ax, ay = a
        bx, by = b
        m = width / 2 + max(self.classes.values()) + self.clr + self.slack + 0.1
        win = self._win(min(ax, bx) - m, min(ay, by) - m, max(ax, bx) + m, max(ay, by) + m)
        if win is None:
            return
        d = self._seg_dist(win[1], win[2], ax, ay, bx, by) - width / 2
        self._mark(layer, net, win, np.maximum(d, 0.0))

    def add_via(self, net, p, dia, drill=None):
        for li in (0, 1):
            self.add_segment(li, net, p, p, dia)
        self.add_hole(p, self.via_drill if drill is None else drill)

    def add_hole(self, p, drill):
        """No new via centre closer than hole-to-hole + both radii (any net, same net included)."""
        r = self.hole_to_hole + drill / 2 + self.via_drill / 2
        win = self._win(p[0] - r, p[1] - r, p[0] + r, p[1] + r)
        if win is None:
            return
        d = np.hypot(win[1] - p[0], win[2] - p[1])
        self.hole_block[win[0]][d < r + 1e-6] = True

    def segment_cells(self, layer, a, b):
        ax, ay = a
        bx, by = b
        r = self.g * 0.75
        win = self._win(min(ax, bx) - r, min(ay, by) - r, max(ax, bx) + r, max(ay, by) + r)
        if win is None:
            return []
        d = self._seg_dist(win[1], win[2], ax, ay, bx, by)
        sl = win[0]
        jj, ii = np.nonzero(d <= r)
        return [(layer, int(j + sl[0].start) * self.nx + int(i + sl[1].start)) for j, i in zip(jj, ii)]

    def add_outline(self):
        ps = pcbnew.SHAPE_POLY_SET()
        self.board.GetBoardPolygonOutlines(ps)
        outlines = self.shape_points(ps)
        X, Y = np.meshgrid(self.xs, self.ys)
        inside = np.zeros(X.shape, bool)
        dmin = np.full(X.shape, np.inf)
        for pts in outlines:
            n = len(pts)
            ins = np.zeros(X.shape, bool)
            for i in range(n):
                ax, ay = pts[i]
                bx, by = pts[(i + 1) % n]
                cond = ((ay > Y) != (by > Y))
                with np.errstate(divide="ignore", invalid="ignore"):
                    xc = (bx - ax) * (Y - ay) / (by - ay + 1e-30) + ax
                ins ^= cond & (X < xc)
                dmin = np.minimum(dmin, self._seg_dist(X, Y, ax, ay, bx, by))
            inside |= ins
        self.inside = inside
        for c, hw in self.classes.items():
            bad = (~inside) | (dmin <= self.edge_clr + hw + self.slack)
            self.owner[c][:, bad] = -1
        # never step off the lattice
        for c in self.classes:
            o = self.owner[c]
            o[:, 0, :] = -1
            o[:, -1, :] = -1
            o[:, :, 0] = -1
            o[:, :, -1] = -1

    def keepout_polygon(self, pts, layers=(0, 1), tracks=True, vias=True, vias_except_gnd=False):
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        m = max(self.classes.values()) + self.slack + 0.1
        win = self._win(min(xs) - m, min(ys) - m, max(xs) + m, max(ys) + m)
        if win is None:
            return
        d = self._poly_dist(win[1], win[2], pts)
        sl = win[0]
        if tracks:
            for li in layers:
                self._block(li, win, d)
        if vias:
            vm = d <= self.classes["via"] + self.slack
            if vias_except_gnd:
                self.via_block_sig[sl][vm] = True
            else:
                self.via_block[sl][vm] = True

    def add_rule_area(self, zone):
        """KiCad rule area (board or footprint level)."""
        layers = [li for li, L in enumerate(LAYERS) if zone.IsOnLayer(L)]
        for pts in self.shape_points(zone.Outline()):
            self.keepout_polygon(pts, layers, tracks=zone.GetDoNotAllowTracks(), vias=zone.GetDoNotAllowVias())

    def build(self):
        self.add_outline()
        for z in self.board.Zones():
            if z.GetIsRuleArea():
                self.add_rule_area(z)
        for fp in self.board.GetFootprints():
            for z in fp.Zones():
                if z.GetIsRuleArea():
                    self.add_rule_area(z)
            for pad in fp.Pads():
                self.add_pad(pad)
                if pad.HasHole():
                    q = pad.GetPosition()
                    self.add_hole((to_mm(q.x) - self.ox, to_mm(q.y) - self.oy), to_mm(pad.GetDrillSize().x))
        for t in self.board.GetTracks():
            if t.GetClass() == "PCB_VIA":
                p = t.GetPosition()
                self.add_via(t.GetNetCode(), (to_mm(p.x) - self.ox, to_mm(p.y) - self.oy), to_mm(t.GetWidth(pcbnew.F_Cu)),
                             to_mm(t.GetDrillValue()))
            else:
                li = 0 if t.GetLayer() == pcbnew.F_Cu else 1
                a, b = t.GetStart(), t.GetEnd()
                self.add_segment(li, t.GetNetCode(), (to_mm(a.x) - self.ox, to_mm(a.y) - self.oy),
                                 (to_mm(b.x) - self.ox, to_mm(b.y) - self.oy), to_mm(t.GetWidth()))

    # ------------------------------------------------------------ connectivity
    def clusters(self, netname):
        """Pads of a net grouped by existing copper (KiCad connectivity)."""
        code = self.netcode[netname]
        self.board.BuildConnectivity()
        conn = self.board.GetConnectivity()
        pads = [p for fp in self.board.GetFootprints() for p in fp.Pads() if p.GetNetCode() == code]
        tracks = [t for t in self.board.GetTracks() if t.GetNetCode() == code]
        idx = {}
        parent = list(range(len(pads) + len(tracks)))

        def find(a):
            while parent[a] != a:
                parent[a] = parent[parent[a]]
                a = parent[a]
            return a

        def union(a, b):
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[ra] = rb

        items = pads + tracks
        for i, it in enumerate(items):
            idx[it.m_Uuid.AsString()] = i
        # KiCad answers direct neighbours only; union-find gives the clusters
        for i, it in enumerate(items):
            for other in list(conn.GetConnectedTracks(it)) + list(conn.GetConnectedPads(it)):
                j = idx.get(other.m_Uuid.AsString())
                if j is not None:
                    union(i, j)
        groups = {}
        for i, it in enumerate(items):
            groups.setdefault(find(i), {"pads": [], "tracks": []})
            groups[find(i)]["pads" if i < len(pads) else "tracks"].append(it)
        return [g for g in groups.values() if g["pads"]]

    def cluster_cells(self, cl):
        cells = []
        for p in cl["pads"]:
            cells += self.pad_cells(p)
        for t in cl["tracks"]:
            if t.GetClass() == "PCB_VIA":
                p = t.GetPosition()
                q = (to_mm(p.x) - self.ox, to_mm(p.y) - self.oy)
                cells += self.segment_cells(0, q, q) + self.segment_cells(1, q, q)
            else:
                li = 0 if t.GetLayer() == pcbnew.F_Cu else 1
                a, b = t.GetStart(), t.GetEnd()
                cells += self.segment_cells(li, (to_mm(a.x) - self.ox, to_mm(a.y) - self.oy),
                                            (to_mm(b.x) - self.ox, to_mm(b.y) - self.oy))
        return cells

    # ------------------------------------------------------------ search
    def astar(self, passable, target, viaok, sources, goal, layer_cost, via_cost, turn_cost, max_exp,
              heuristic=True, hweight=1.0):
        nx = self.nx
        N = self.N
        off = [dx + dy * nx for dx, dy in DIRS]
        turn = [0.0, turn_cost[0], turn_cost[1], 1e9, 1e9]
        gx, gy = goal
        hmin = min(layer_cost) * hweight
        g = {}
        parent = {}
        heap = []
        for li, c in sources:
            s = (li * N + c) * 9 + NOHEAD
            if g.get(s, 1e18) > 0:
                g[s] = 0.0
                parent[s] = -1
                x, y = c % nx, c // nx
                if heuristic:
                    dx, dy = abs(x - gx), abs(y - gy)
                    hh = (max(dx, dy) + (SQ2 - 1) * min(dx, dy)) * hmin
                else:
                    hh = 0.0
                heapq.heappush(heap, (hh, 0.0, s))
        exp = 0
        P = passable
        T = target
        while heap:
            f, gc, s = heapq.heappop(heap)
            if gc > g.get(s, 1e18):
                continue
            hd = s % 9
            lc = s // 9
            li = lc // N
            c = lc - li * N
            if T[li][c]:
                return self._unwind(parent, s)
            exp += 1
            if exp > max_exp:
                return None
            pl = P[li]
            lcst = layer_cost[li]
            for d in range(8):
                if hd != NOHEAD:
                    diff = (d - hd) & 7
                    tc = turn[diff if diff <= 4 else 8 - diff]
                    if tc >= 1e8:
                        continue
                else:
                    tc = 0.0
                c2 = c + off[d]
                if not pl[c2]:
                    continue
                ng = gc + STEP[d] * lcst + tc
                s2 = ((li * N + c2) * 9) + d
                if ng < g.get(s2, 1e18):
                    g[s2] = ng
                    parent[s2] = s
                    if heuristic:
                        x, y = c2 % nx, c2 // nx
                        dx, dy = abs(x - gx), abs(y - gy)
                        hh = (max(dx, dy) + (SQ2 - 1) * min(dx, dy)) * hmin
                    else:
                        hh = 0.0
                    heapq.heappush(heap, (ng + hh, ng, s2))
            if viaok is not None and viaok[c]:
                li2 = 1 - li
                if P[li2][c]:
                    ng = gc + via_cost
                    s2 = ((li2 * N + c) * 9) + NOHEAD
                    if ng < g.get(s2, 1e18):
                        g[s2] = ng
                        parent[s2] = s
                        heapq.heappush(heap, (f - gc + ng, ng, s2))
        return None

    def _unwind(self, parent, s):
        out = []
        while s != -1:
            lc = s // 9
            out.append((lc // self.N, lc % self.N))
            s = parent[s]
        out.reverse()
        return out

    def path_to_runs(self, path):
        """[(layer, [(x,y) mm ...]), ...] with collinear points removed; vias between runs."""
        runs = []
        cur = None
        for li, c in path:
            x, y = (c % self.nx) * self.g, (c // self.nx) * self.g
            if cur is None or cur[0] != li:
                cur = (li, [])
                runs.append(cur)
            pts = cur[1]
            if pts and abs(pts[-1][0] - x) < 1e-9 and abs(pts[-1][1] - y) < 1e-9:
                continue
            pts.append((x, y))
        out = []
        for li, pts in runs:
            simp = []
            for p in pts:
                if len(simp) >= 2:
                    (x0, y0), (x1, y1) = simp[-2], simp[-1]
                    if abs((x1 - x0) * (p[1] - y1) - (y1 - y0) * (p[0] - x1)) < 1e-9:
                        simp[-1] = p
                        continue
                simp.append(p)
            out.append((li, simp))
        return out

    # ------------------------------------------------------------ board output
    def emit(self, netname, runs, width, via_dia=0.6, via_drill=0.3):
        code = self.netcode[netname]
        ni = self.board.FindNet(netname)
        new_cells = []
        prev_end = None
        for k, (li, pts) in enumerate(runs):
            if k > 0:
                p = pts[0]
                v = pcbnew.PCB_VIA(self.board)
                v.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(self.ox + p[0]), pcbnew.FromMM(self.oy + p[1])))
                v.SetWidth(pcbnew.FromMM(via_dia))
                v.SetDrill(pcbnew.FromMM(via_drill))
                v.SetNet(ni)
                self.board.Add(v)
                self.add_via(code, p, via_dia)
                new_cells += self.segment_cells(0, p, p) + self.segment_cells(1, p, p)
            for a, b in zip(pts[:-1], pts[1:]):
                t = pcbnew.PCB_TRACK(self.board)
                t.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(self.ox + a[0]), pcbnew.FromMM(self.oy + a[1])))
                t.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(self.ox + b[0]), pcbnew.FromMM(self.oy + b[1])))
                t.SetWidth(pcbnew.FromMM(width))
                t.SetLayer(LAYERS[li])
                t.SetNet(ni)
                self.board.Add(t)
                self.add_segment(li, code, a, b, width)
                new_cells += self.segment_cells(li, a, b)
            if len(pts) == 1:
                new_cells += self.segment_cells(li, pts[0], pts[0])
            prev_end = pts[-1]
        del prev_end
        return new_cells

    # ------------------------------------------------------------ nets
    def _class_for(self, width):
        best = None
        for c, hw in self.classes.items():
            if c == "via":
                continue
            if hw + 1e-9 >= width / 2 and (best is None or hw < self.classes[best]):
                best = c
        if best is None:
            raise ValueError("no class for width %.2f" % width)
        return best

    def _masks(self, code, cls, own_cells, allow_vias, gnd=False):
        P = []
        for li in (0, 1):
            o = self.owner[cls][li]
            m = (o == 0) | (o == code)
            P.append(m)
        if own_cells:
            for li, c in own_cells:
                P[li].flat[c] = True
        Pb = [m.tobytes() for m in P]
        V = None
        if allow_vias:
            ov = self.owner["via"]
            vm = ((ov[0] == 0) | (ov[0] == code)) & ((ov[1] == 0) | (ov[1] == code)) & ~self.via_block & \
                ~self.hole_block
            if not gnd:
                vm &= ~self.via_block_sig
            V = vm.tobytes()
        return Pb, V

    def route_net(self, netname, width=0.25, layer_cost=(1.0, 2.5), via_cost=12.0, allow_vias=True,
                  turn_cost=(0.4, 1.2), max_exp=600000, pads_filter=None):
        code = self.netcode[netname]
        cls = self._class_for(width)
        cl = self.clusters(netname)
        if pads_filter:
            cl = [c for c in cl if any(pads_filter(p) for p in c["pads"])]
        if len(cl) <= 1:
            return True
        cells = [self.cluster_cells(c) for c in cl]
        # start from the cluster with most pads
        start = max(range(len(cl)), key=lambda i: (len(cl[i]["pads"]), -i))
        tree = set(cells[start])
        tree_pads = list(cl[start]["pads"])
        todo = [i for i in range(len(cl)) if i != start]
        ok = True
        while todo:
            best = None
            for i in todo:
                for p in cl[i]["pads"]:
                    pp = p.GetPosition()
                    for q in tree_pads:
                        qq = q.GetPosition()
                        d = math.hypot(pp.x - qq.x, pp.y - qq.y)
                        if best is None or d < best[0]:
                            best = (d, i, q)
            _, i, q = best
            todo.remove(i)
            src = cells[i]
            tgt = np.zeros(2 * self.N, bool)
            for li, c in tree:
                tgt[li * self.N + c] = True
            T = [tgt[:self.N].tobytes(), tgt[self.N:].tobytes()]
            P, V = self._masks(code, cls, list(tree) + src, allow_vias)
            qq = q.GetPosition()
            goal = (int(round((to_mm(qq.x) - self.ox) / self.g)), int(round((to_mm(qq.y) - self.oy) / self.g)))
            path = None
            tries = ((layer_cost, via_cost, max_exp, 1.0), ((1.0, 1.3), via_cost * 0.5, max_exp * 4, 1.3))
            for lcst, vcst, budget, hw in tries:
                path = self.astar(P, T, V, src, goal, lcst, vcst, turn_cost, budget, hweight=hw)
                if path:
                    break
            label = "%s: %s -> %s" % (netname, "/".join(pad_name(p) for p in cl[i]["pads"][:2]), pad_name(q))
            if not path:
                self.unrouted.append(label)
                self.log.append("FAILED " + label)
                ok = False
                continue
            runs = self.path_to_runs(path)
            new = self.emit(netname, runs, width)
            nvias = len(runs) - 1
            length = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for _, pts in runs for a, b in zip(pts[:-1], pts[1:]))
            self.log.append("ok %-40s len %6.1f mm  vias %d" % (label, length, nvias))
            tree.update(src)
            tree.update(new)
            tree_pads += cl[i]["pads"]
        return ok

    # ------------------------------------------------------------ ground
    def gnd_fanout(self, pads, width=0.3, via_dia=0.6, max_exp=200000, min_gap=0.25):
        """Short stub from each pad to the nearest legal via site."""
        code = self.netcode["GND"]
        cls = self._class_for(width)
        # via sites must not overlap any GND pad (no via-in-pad)
        near_pad = np.zeros((self.ny, self.nx), bool)
        for fp in self.board.GetFootprints():
            for p in fp.Pads():
                if p.GetNetCode() != code or not p.IsOnLayer(pcbnew.F_Cu):
                    continue
                ps = p.GetEffectivePolygon(pcbnew.F_Cu, pcbnew.ERROR_INSIDE)
                for pts in self.shape_points(ps):
                    xs = [a[0] for a in pts]
                    ys = [a[1] for a in pts]
                    r = via_dia / 2 + min_gap
                    win = self._win(min(xs) - r - 0.2, min(ys) - r - 0.2, max(xs) + r + 0.2, max(ys) + r + 0.2)
                    d = self._poly_dist(win[1], win[2], pts)
                    near_pad[win[0]][d <= r] = True
        done = 0
        for pad in pads:
            src = self.pad_cells(pad)
            src = [(li, c) for li, c in src if li == 0]
            P, V = self._masks(code, cls, src, True, gnd=True)
            Vn = np.frombuffer(V, dtype=bool).copy() & ~near_pad.ravel()
            # target: a via site; the search stays on F.Cu
            T = [Vn.tobytes(), bytes(self.N)]
            path = self.astar([P[0], bytes(self.N)], T, None, src, (0, 0), (1.0, 1e9), 0.0, (0.3, 0.8),
                              max_exp, heuristic=False)
            if not path:
                self.log.append("GND fanout FAILED for " + pad_name(pad))
                self.unrouted.append("GND fanout " + pad_name(pad))
                continue
            runs = self.path_to_runs(path)
            li, pts = runs[0]
            end = pts[-1]
            self.emit("GND", runs, width)
            v = pcbnew.PCB_VIA(self.board)
            v.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(self.ox + end[0]), pcbnew.FromMM(self.oy + end[1])))
            v.SetWidth(pcbnew.FromMM(via_dia))
            v.SetDrill(pcbnew.FromMM(0.3))
            v.SetNet(self.board.FindNet("GND"))
            self.board.Add(v)
            self.add_via(code, end, via_dia)
            # no other via site directly next to this one
            done += 1
        self.log.append("GND fanout: %d vias" % done)

    def place_via(self, netname, p, via_dia=0.6, via_drill=0.3):
        v = pcbnew.PCB_VIA(self.board)
        v.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(self.ox + p[0]), pcbnew.FromMM(self.oy + p[1])))
        v.SetWidth(pcbnew.FromMM(via_dia))
        v.SetDrill(pcbnew.FromMM(via_drill))
        v.SetNet(self.board.FindNet(netname))
        self.board.Add(v)
        self.add_via(self.netcode[netname], p, via_dia)
        return v

    def via_site_ok(self, code, p, gnd=True):
        i = int(round(p[0] / self.g))
        j = int(round(p[1] / self.g))
        if not (0 <= i < self.nx and 0 <= j < self.ny):
            return False
        ov = self.owner["via"]
        for li in (0, 1):
            if ov[li, j, i] not in (0, code):
                return False
        if self.via_block[j, i] or self.hole_block[j, i] or (not gnd and self.via_block_sig[j, i]):
            return False
        return True

    def stitch(self, sites, extra_gap=0.0):
        """GND stitching vias at the given candidate sites (mm), where legal."""
        code = self.netcode["GND"]
        placed = []
        for p in sites:
            q = (round(p[0] / self.g) * self.g, round(p[1] / self.g) * self.g)
            if self.via_site_ok(code, q):
                placed.append(self.place_via("GND", q))
        return placed


def pad_name(p):
    return "%s.%s" % (p.GetParentFootprint().GetReference(), p.GetNumber())
