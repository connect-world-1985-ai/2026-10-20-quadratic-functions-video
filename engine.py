import re, math, os, hashlib, subprocess, asyncio, json
import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1280, 720, 30
BG = (23, 35, 33)
PANEL = (16, 26, 25)
CHALK = (236, 236, 228)
COL = {'w': CHALK, 'y': (255, 213, 79), 'c': (100, 210, 255), 'g': (129, 230, 140),
       'p': (255, 128, 171), 'o': (255, 159, 67), 'd': (140, 158, 152), 'r': (255, 99, 99)}
FD = '/usr/share/fonts/truetype/dejavu/'
_fc = {}
def font(sz, bold=False, mono=False):
    k = (sz, bold, mono)
    if k not in _fc:
        n = 'DejaVuSansMono' if mono else 'DejaVuSans'
        if bold: n += '-Bold'
        _fc[k] = ImageFont.truetype(FD + n + '.ttf', sz)
    return _fc[k]

def clamp(u, a=0.0, b=1.0): return max(a, min(b, u))
def smooth(u): u = clamp(u); return u * u * (3 - 2 * u)
def mix(c1, c2, a): return tuple(int(c1[i] * (1 - a) + c2[i] * a) for i in range(3))
def val(v, t): return v(t) if callable(v) else v

def parse(s, default='w'):
    segs = []; cur = default; pos = 0
    for m in re.finditer(r'<(\w)>|</>', s):
        if m.start() > pos: segs.append((s[pos:m.start()], cur))
        cur = m.group(1) if m.group(1) else default
        pos = m.end()
    if pos < len(s): segs.append((s[pos:], cur))
    return segs

def seg_w(segs, f): return sum(f.getlength(t) for t, _ in segs)
def draw_segs(d, x, y, segs, f, anchor='t', alpha=1.0, base=None):
    # always draw on a common baseline so punctuation-only segments (e.g. ", ") sit correctly
    sz = f.size
    if anchor == 't': by = y + 0.93 * sz
    elif anchor == 'b': by = y - 0.24 * sz
    else: by = y + 0.35 * sz   # 'm'
    for t, c in segs:
        d.text((x, by), t, font=f, fill=mix(BG, COL[c], alpha), anchor='ls')
        x += f.getlength(t)

# ---------------- left panel items ----------------
LX = 50; LTOP = 84; LBOT = 600
class LItem:
    def __init__(s, kind, t0, y, size, **kw):
        s.kind, s.t0, s.y, s.size, s.t1 = kind, t0, y, size, None
        s.__dict__.update(kw)
    def alive(s, t): return t >= s.t0 and (s.t1 is None or t < s.t1)
    def key(s, t):
        if s.kind == 'pause': return None
        return int(clamp((t - s.t0) / 0.35) * 4)
    def draw(s, d, t):
        a = 0.15 + 0.85 * (clamp((t - s.t0) / 0.35))
        f = font(s.size, s.__dict__.get('bold', False), s.__dict__.get('mono', False))
        x = LX + s.indent
        if s.kind == 'line':
            segs = s.segs
            if s.box:
                w = seg_w(segs, f)
                d.rounded_rectangle((x - 12, s.y - 6, x + w + 12, s.y + int(s.size * 1.3) + 2), 10,
                                    outline=mix(BG, COL[s.box], a), width=3)
            draw_segs(d, x, s.y, segs, f, 't', a)
        elif s.kind == 'frac':
            lh = int(s.size * 1.3)
            bar_y = s.y + lh + 3
            pw = seg_w(s.pre, f)
            nw, dw = seg_w(s.num, f), seg_w(s.den, f)
            bw = max(nw, dw) + 20
            if s.box:
                d.rounded_rectangle((x - 12, s.y - 6, x + pw + bw + 24, s.y + 2 * lh + 10), 10,
                                    outline=mix(BG, COL[s.box], a), width=3)
            draw_segs(d, x, bar_y, s.pre, f, 'm', a)
            bx = x + pw + 6
            d.line((bx, bar_y, bx + bw, bar_y), fill=mix(BG, CHALK, a), width=3)
            draw_segs(d, bx + (bw - nw) / 2, bar_y - 6, s.num, f, 'b', a)
            draw_segs(d, bx + (bw - dw) / 2, bar_y + 6, s.den, f, 't', a)

# ---------------- graph ----------------
GX0, GY0, GW, GH = 670, 80, 570, 500
class Ctx:
    def __init__(s, win):
        s.xmin, s.xmax, s.ymin, s.ymax = win
    def sx(s, x, k=2): return (x - s.xmin) / (s.xmax - s.xmin) * GW * k
    def sy(s, y, k=2): return GH * k - (y - s.ymin) / (s.ymax - s.ymin) * GH * k

class El:
    def __init__(s, t0, show=None): s.t0, s.show = t0, show
    def vis(s, t): return t >= s.t0 and (s.show is None or s.show(t))
    def lvl(s, t, dur=0.35, n=5): return int(clamp((t - s.t0) / dur) * n)

class Curve(El):
    def __init__(s, t0, fn, color, width, draw, params, show):
        super().__init__(t0, show); s.fn, s.color, s.width, s.drawdur, s.params = fn, color, width, draw, params
    def key(s, t):
        if not s.vis(t): return None
        p = tuple(round(v, 3) for v in s.params(t)) if s.params else ()
        u = clamp((t - s.t0) / s.drawdur) if s.drawdur > 0 else 1
        return ('c', int(smooth(u) * 150), p)
    def draw2(s, d, c, t, k):
        q, p = k[1] / 150, k[2]
        if q <= 0: return
        xs = np.linspace(c.xmin, c.xmin + (c.xmax - c.xmin) * q, 500)
        ys = s.fn(xs, p); R = c.ymax - c.ymin
        ys = np.clip(ys, c.ymin - 20 * R, c.ymax + 20 * R)
        pts = [(float(c.sx(x)), float(c.sy(y))) for x, y in zip(xs, ys)]
        d.line(pts, fill=COL[s.color], width=s.width * 2, joint='curve')

class Point(El):
    def __init__(s, t0, x, y, color, label, lpos, show):
        super().__init__(t0, show); s.x, s.y, s.color, s.label, s.lpos = x, y, color, label, lpos
    def key(s, t):
        if not s.vis(t): return None
        lab = s.label(t) if callable(s.label) else s.label
        return ('p', s.lvl(t, 0.3), round(val(s.x, t), 3), round(val(s.y, t), 3), lab)
    def draw2(s, d, c, t, k):
        px, py = c.sx(k[2]), c.sy(k[3]); r = 6 + 9 * k[1] / 5 if k[1] < 5 else 15
        r = 15 * min(1, k[1] / 4)
        d.ellipse((px - r, py - r, px + r, py + r), fill=COL[s.color], outline=BG, width=3)
    def draw1(s, d, c, t, k):
        if k[4]:
            px, py = c.sx(k[2], 1) + s.lpos[0], c.sy(k[3], 1) + s.lpos[1]
            f = font(21, True)
            tw = f.getlength(k[4])
            px = clamp(px, 4, GW - tw - 8); py = clamp(py, 14, GH - 14)
            d.rounded_rectangle((px - 4, py - 14, px + tw + 4, py + 14), 6, fill=PANEL)
            d.text((px, py), k[4], font=f, fill=COL[s.color], anchor='lm')

class Line(El):
    def __init__(s, t0, x, y, color, vert, dashed, show):
        super().__init__(t0, show); s.x, s.y, s.color, s.vert, s.dashed = x, y, color, vert, dashed
    def key(s, t):
        if not s.vis(t): return None
        return ('l', int(smooth((t - s.t0) / 0.7) * 20), round(val(s.x if s.vert else s.y, t), 3))
    def draw2(s, d, c, t, k):
        q = k[1] / 20
        if q <= 0: return
        if s.vert:
            x = c.sx(k[2]); a, b = GH * 2, GH * 2 * (1 - q); pts = (a, b)
            seg = lambda y0, y1: (x, y0, x, y1)
        else:
            y = c.sy(k[2]); a, b = 0, GW * 2 * q
            seg = lambda x0, x1: (x0, y, x1, y)
        lo, hi = min(a, b), max(a, b); step = 28; pos = lo
        while pos < hi:
            d.line(seg(pos, min(pos + 16, hi)), fill=COL[s.color], width=4); pos += step

class GText(El):
    def __init__(s, t0, fn, pos, color, size, show):
        super().__init__(t0, show); s.fn, s.pos, s.color, s.size = fn, pos, color, size
    def key(s, t):
        if not s.vis(t): return None
        return ('t', s.fn(t) if callable(s.fn) else s.fn)
    def draw1(s, d, c, t, k):
        f = font(s.size, True)
        d.text(s.pos, k[1], font=f, fill=COL[s.color], anchor='lm')

class Graph:
    def __init__(s, t0, win, xstep, ystep, xl, yl):
        s.t0, s.t1, s.win, s.xstep, s.ystep, s.xl, s.yl = t0, None, win, xstep, ystep, xl, yl
        s.els = []; s.ctx = Ctx(win); s._base = None
    def alive(s, t): return t >= s.t0 and (s.t1 is None or t < s.t1)
    def curve(s, t0, fn, color='c', width=3, draw=1.5, params=None, show=None):
        e = Curve(t0, fn, color, width, draw, params, show); s.els.append(e); return e
    def point(s, t0, x, y, color='y', label=None, lpos=(14, -22), show=None):
        e = Point(t0, x, y, color, label, lpos, show); s.els.append(e); return e
    def vline(s, t0, x, color='o', show=None):
        e = Line(t0, x, None, color, True, True, show); s.els.append(e); return e
    def hline(s, t0, y, color='o', show=None):
        e = Line(t0, None, y, color, False, True, show); s.els.append(e); return e
    def text(s, t0, fn, pos, color='y', size=24, show=None):
        e = GText(t0, fn, pos, color, size, show); s.els.append(e); return e
    def base(s):
        if s._base is None:
            c = s.ctx; im = Image.new('RGB', (GW * 2, GH * 2), PANEL); d = ImageDraw.Draw(im)
            gc, ac = (34, 52, 50), (150, 168, 162)
            x = math.ceil(c.xmin / s.xstep) * s.xstep
            while x <= c.xmax + 1e-9:
                d.line((c.sx(x), 0, c.sx(x), GH * 2), fill=gc, width=2); x += s.xstep
            y = math.ceil(c.ymin / s.ystep) * s.ystep
            while y <= c.ymax + 1e-9:
                d.line((0, c.sy(y), GW * 2, c.sy(y)), fill=gc, width=2); y += s.ystep
            ax = c.sx(clamp(0, c.xmin, c.xmax)); ay = c.sy(clamp(0, c.ymin, c.ymax))
            d.line((0, ay, GW * 2, ay), fill=ac, width=4); d.line((ax, 0, ax, GH * 2), fill=ac, width=4)
            f = font(30); fmt = lambda v: str(int(v)).replace('-', '−')
            x = math.ceil(c.xmin / s.xstep) * s.xstep
            while x <= c.xmax + 1e-9:
                if abs(x) > 1e-9 and 30 < c.sx(x) < GW * 2 - 30: d.text((c.sx(x), ay + 8), fmt(x), font=f, fill=ac, anchor='mt')
                x += s.xstep
            y = math.ceil(c.ymin / s.ystep) * s.ystep
            while y <= c.ymax + 1e-9:
                if abs(y) > 1e-9 and 30 < c.sy(y) < GH * 2 - 30: d.text((ax - 10, c.sy(y)), fmt(y), font=f, fill=ac, anchor='rm')
                y += s.ystep
            fb = font(30, True)
            d.text((GW * 2 - 12, ay - 10), s.xl, font=fb, fill=COL['w'], anchor='rb')
            d.text((ax + 12, 8), s.yl, font=fb, fill=COL['w'], anchor='lt')
            s._base = im
        return s._base
    def keys(s, t): return tuple(e.key(t) for e in s.els)
    def render(s, t, keys):
        im = s.base().copy(); d = ImageDraw.Draw(im); c = s.ctx
        for e, k in zip(s.els, keys):
            if k is not None and hasattr(e, 'draw2'): e.draw2(d, c, t, k)
        im = im.reduce(2); d = ImageDraw.Draw(im)
        for e, k in zip(s.els, keys):
            if k is not None and hasattr(e, 'draw1'): e.draw1(d, c, t, k)
        return im

# ---------------- scene helper ----------------
class Beat:
    def __init__(s, text, gap=0.35): s.text, s.gap = text, gap
def B(text, gap=0.35): return Beat(text, gap)

class Scene:
    def __init__(s, title, beats, visuals):
        s.title, s.beats, s.visuals = title, beats, visuals
        s.left, s.graphs, s.pauses = [], [], []
        s.cy = LTOP; s.width = 590
    # timing
    def set_times(s, durs):
        t = 0.4; s.t, s.e = [], []
        for b, d in zip(s.beats, durs):
            s.t.append(t); s.e.append(t + d); t += d + b.gap
        s.length = t + 0.5
    def at(s, i, off=0.0, fr=None):
        return s.t[i] + (fr * (s.e[i] - s.t[i]) if fr is not None else off)
    # left
    def _fit(s, segs, size, indent, bold=False, mono=False):
        while size > 18 and seg_w(segs, font(size, bold, mono)) > s.width - indent: size -= 2
        return size
    def line(s, i, text, size=32, indent=0, color='w', box=None, off=0.0, fr=None, space=10, bold=False, mono=False):
        segs = parse(text, color); size = s._fit(segs, size, indent, bold, mono)
        it = LItem('line', s.at(i, off, fr), s.cy, size, segs=segs, indent=indent, box=box, bold=bold, mono=mono)
        s.cy += int(size * 1.3) + space
        assert s.cy <= LBOT + 20, ('left overflow', s.title, text, s.cy)
        s.left.append(it); return it
    def frac(s, i, pre, num, den, size=32, box=None, off=0.0, fr=None, space=14, color='w'):
        it = LItem('frac', s.at(i, off, fr), s.cy, size, pre=parse(pre, color), num=parse(num, color), den=parse(den, color),
                   indent=0, box=box)
        s.cy += int(size * 1.3) * 2 + 20 + space
        assert s.cy <= LBOT + 20, ('left overflow', s.title, pre, s.cy)
        s.left.append(it); return it
    def space(s, px): s.cy += px
    def clear(s, i, off=0.0, fr=None):
        t = s.at(i, off, fr)
        for it in s.left:
            if it.t1 is None: it.t1 = t
        s.cy = LTOP
    def pause(s, i, secs=None):
        t0 = s.e[i]; t1 = t0 + s.beats[i].gap; s.pauses.append((t0, t1))
    # graph
    def graph(s, i, win, xstep=1, ystep=1, xl='x', yl='y', off=0.0, fr=None):
        t = s.at(i, off, fr)
        if s.graphs and s.graphs[-1].t1 is None: s.graphs[-1].t1 = t
        g = Graph(t, win, xstep, ystep, xl, yl); s.graphs.append(g); return g
    def end_graph(s, i, off=0.0):
        if s.graphs and s.graphs[-1].t1 is None: s.graphs[-1].t1 = s.at(i, off)
    def track(s, init, kfs):
        # kfs: (beat, value, delay, ramp)
        segs = []; prev = init
        for (b, v, delay, ramp) in kfs:
            segs.append((s.t[b] + delay, ramp, prev, v)); prev = v
        def f(t):
            cur = init
            for (t0, ramp, a, b) in segs:
                if t >= t0: cur = a + (b - a) * smooth((t - t0) / ramp)
            return cur
        return f

# ---------------- captions ----------------
def say_text(t): return t.replace('@a', 'ay')
def cap_text(t): return t.replace('@a', 'a')
def chunk_caption(text, maxc=96):
    text = cap_text(text)
    sents = re.split(r'(?<=[.!?:])\s+', text.strip())
    parts = []
    for sn in sents:
        while len(sn) > maxc:
            cut = max(sn.rfind(', ', 0, maxc), sn.rfind(' ', 0, maxc)) if ', ' in sn[:maxc] else sn.rfind(' ', 0, maxc)
            if sn.rfind(', ', 0, maxc) > 25: cut = sn.rfind(', ', 0, maxc) + 1
            parts.append(sn[:cut].strip()); sn = sn[cut:].strip()
        parts.append(sn)
    out = []
    for p in parts:
        if out and (len(out[-1]) + 1 + len(p) <= maxc or (len(out[-1]) < 20 and len(out[-1]) + 1 + len(p) <= 125)): out[-1] += ' ' + p
        else: out.append(p)
    return out

# ---------------- TTS ----------------
VOICE = 'en-US-AndrewNeural'
RATE = '+5%'
async def _tts(text, path, voice, rate):
    import edge_tts
    await edge_tts.Communicate(text, voice, rate=rate).save(path)
def tts_samples(text, cache='cache'):
    os.makedirs(cache, exist_ok=True)
    h = hashlib.md5((VOICE + RATE + text).encode()).hexdigest()
    p = f'{cache}/{h}.mp3'
    if not os.path.exists(p):
        for attempt in range(5):
            try:
                asyncio.run(_tts(text, p, VOICE, RATE)); break
            except Exception as ex:
                print('tts retry', attempt, ex); 
                import time; time.sleep(2)
        assert os.path.exists(p) and os.path.getsize(p) > 1000, 'tts failed'
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', p, '-f', 's16le', '-ac', '1', '-ar', '24000', '-'],
                         capture_output=True, check=True).stdout
    a = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768
    idx = np.where(np.abs(a) > 0.01)[0]
    if len(idx): a = a[max(0, idx[0] - 1200): idx[-1] + 2400]
    return a
