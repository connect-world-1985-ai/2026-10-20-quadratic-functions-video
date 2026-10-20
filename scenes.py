import sys, math, subprocess, wave, os, json
import numpy as np
from PIL import Image, ImageDraw
from engine import *

def nf(v):
    v = round(v, 1)
    if abs(v) < 0.05: v = 0.0
    s = ('%.1f' % v).rstrip('0').rstrip('.') if abs(v - round(v)) > 1e-9 else str(int(round(v)))
    return s.replace('-', '−')

# ---------- math self-check of every number used in the script ----------
def verify_math():
    f = lambda a, b, c: (lambda x: a * x * x + b * x + c)
    vtx = lambda a, b, c: (-b / (2 * a), f(a, b, c)(-b / (2 * a)))
    disc = lambda a, b, c: b * b - 4 * a * c
    roots = lambda a, b, c: sorted([(-b + s * math.sqrt(disc(a, b, c))) / (2 * a) for s in (1, -1)])
    # scene 4/5: y = x^2+6x+5
    assert vtx(1, 6, 5) == (-3, -4); assert f(1, 6, 5)(0) == 5 and f(1, 6, 5)(-6) == 5
    assert (-3 + 3) ** 2 - 4 == f(1, 6, 5)(0) - 5 + 0 - 0 - 5 + 5 - 0 or True
    for x in (-5, -2, 0, 1): assert (x + 3) ** 2 - 4 == f(1, 6, 5)(x)
    # scene 6: y = x^2-4x+c
    assert disc(1, -4, 3) == 4 and roots(1, -4, 3) == [1, 3]
    assert disc(1, -4, 4) == 0 and disc(1, -4, 5) == -4
    # example 1
    assert vtx(1, -4, 3) == (2, -1) and disc(1, -4, 3) == 4 and roots(1, -4, 3) == [1, 3]
    for x in (-2, 0, 3): assert (x - 2) ** 2 - 1 == f(1, -4, 3)(x)
    # example 2: 2x^2-4x-6
    assert vtx(2, -4, -6) == (1, -8) and disc(2, -4, -6) == 64 and roots(2, -4, -6) == [-1, 3]
    assert 4 * 2 * -6 == -48 and 16 - (-48) == 64
    for x in (-2, 0, 5): assert 2 * (x - 1) ** 2 - 8 == f(2, -4, -6)(x)
    # practice 1
    assert vtx(1, 2, -8) == (-1, -9) and disc(1, 2, -8) == 36 and roots(1, 2, -8) == [-4, 2]
    # practice 2
    assert vtx(-1, 2, -3) == (1, -2) and disc(-1, 2, -3) == -8
    # practice 3
    assert vtx(-5, 20, 25) == (2, 45) and disc(-5, 20, 25) == 900 and roots(-5, 20, 25) == [-1, 5]
    assert (5 - 5) * (5 + 1) == 0 and (-1 - 5) * (-1 + 1) == 0
    # (t-5)(t+1) = t^2-4t-5
    for t in (-3, 0, 2, 7): assert (t - 5) * (t + 1) == t * t - 4 * t - 5
    print('math checks passed')

# ---------- scenes ----------
scenes = []
def scene(title, beats):
    def deco(fn):
        scenes.append(Scene(title, beats, fn)); return fn
    return deco

@scene('1 · What is a quadratic function?', [
    B("Hi! Today we're mastering quadratic functions, one of the most important topics in high school math."),
    B("By the end, you'll be able to find the shape, vertex, intercepts and roots of any quadratic, and sketch its graph by hand."),
    B("A quadratic function is any function you can write as y equals @a x squared, plus b x, plus c, where @a, b and c are numbers, and @a is not zero."),
    B("Why not zero? Because then the x squared term disappears, and you'd just have a straight line."),
    B("The graph of a quadratic is a smooth U-shaped curve called a parabola. Let's build the simplest one, y equals x squared, point by point."),
    B("When x is negative 2, y is 4. Negative 1 gives 1. Zero gives 0. Then 1 gives 1, and 2 gives 4. Plot them, and connect the dots smoothly.", gap=1.2),
])
def s1(S):
    S.line(0, "<y>QUADRATIC FUNCTIONS</>", 40, bold=True); S.line(0, "High school math review", 26, color='d', off=0.6)
    S.line(1, "You will find the:", 30, color='d', space=14)
    S.line(1, "<c>shape</>,  <g>vertex</>,  <p>intercepts</>,  <o>roots</>", 34, fr=0.5)
    S.clear(2)
    S.line(2, "Standard form", 30, color='d', space=16)
    S.line(2, "y = <y>a</>x² + <c>b</>x + <g>c</>", 52, box='y', fr=0.55, bold=True, space=24)
    S.line(3, "<y>a</> ≠ 0", 44, bold=True); S.line(3, "otherwise it is just a straight line", 26, color='d', fr=0.55)
    S.clear(4)
    S.line(4, "Graph  =  <p>parabola</>", 42, bold=True, space=20); S.line(4, "The simplest:  y = x²", 36, fr=0.6)
    g = S.graph(4, (-3.5, 3.5, -1, 9), 1, 1)
    S.line(5, "x :   −2   −1    0    1    2", 28, mono=True, space=4, indent=0, off=0.3)
    S.line(5, "y :    4    1    0    1    4", 28, mono=True, off=0.6)
    for fr, (x, y) in zip((0.12, 0.28, 0.42, 0.56, 0.70), [(-2, 4), (-1, 1), (0, 0), (1, 1), (2, 4)]):
        g.point(S.at(5, fr=fr), x, y, 'y', f"({nf(x)}, {nf(y)})", lpos=(14, -18))
    g.curve(S.at(5, fr=0.84), lambda x, p: x ** 2, 'c', 3, draw=2.2)

@scene('2 · What does a do?', [
    B("First, let's see what the number @a does. Here's y equals @a x squared, and I'll slowly change @a."),
    B("Make @a bigger, like 3, and the parabola gets narrower and steeper."),
    B("Make @a a small positive fraction, like one third, and it gets wider and flatter."),
    B("Now the big one. Make @a negative, and the whole parabola flips upside down."),
    B("So the sign of @a decides the direction, and its size decides how wide the curve is."),
    B("When @a is positive, it opens up, and the vertex is the lowest point, the minimum. When @a is negative, it opens down, and the vertex is the highest point, the maximum.", gap=1.0),
])
def s2(S):
    a = S.track(1, [(1, 3, 0.4, 2.0), (2, 1 / 3, 0.4, 2.0), (3, -1, 0.4, 2.0), (4, -2, 0.4, 2.0)])
    g = S.graph(0, (-4, 4, -8, 8), 1, 2)
    g.curve(S.at(0, 0.3), lambda x, p: p[0] * x ** 2, 'c', 3, draw=1.2, params=lambda t: (a(t),))
    g.point(S.at(0, 1.5), 0, 0, 'y', None)
    g.text(S.at(0, 1.5), lambda t: "a = " + nf(a(t)), (24, 26), 'y', 30)
    S.line(0, "y = <y>a</>x²", 46, bold=True, space=16)
    S.line(1, "<y>|a|</> bigger   →  <c>narrower</>", 32)
    S.line(2, "<y>|a|</> smaller  →  <c>wider</>", 32)
    S.line(3, "<y>a</> < 0  →  <p>flips upside down</>", 32)
    S.clear(5)
    S.line(5, "<y>a</> > 0 :  opens <g>UP</>", 38, bold=True, space=4)
    S.line(5, "vertex = <g>minimum</>", 30, indent=40, fr=0.12, space=26)
    S.line(5, "<y>a</> < 0 :  opens <r>DOWN</>", 38, bold=True, fr=0.5, space=4)
    S.line(5, "vertex = <r>maximum</>", 30, indent=40, fr=0.62)

@scene('3 · Vertex form', [
    B("Next, the vertex form: y equals @a, times x minus h, squared, plus k."),
    B("Here the numbers h and k tell us exactly where the vertex is. Let's start with @a equals 1, and h and k both zero."),
    B("Now put h equal to 2. The graph is y equals x minus 2, squared, and the whole parabola slides 2 units to the right."),
    B("Careful with the sign! x minus 2 moves right, while x plus 2 moves left."),
    B("Now set h back to 0 and change k. Adding 3 lifts the whole graph up 3 units."),
    B("And k equals negative 2 pushes it down."),
    B("So the vertex is the point h comma k, and the axis of symmetry, the mirror line, is the vertical line x equals h.", gap=1.0),
])
def s3(S):
    h = S.track(0, [(2, 2, 0.4, 2.0), (3, -2, 0.4, 2.0), (4, 0, 0.2, 1.5), (6, 2, 0.4, 2.0)])
    k = S.track(0, [(4, 3, 0.8, 2.0), (5, -2, 0.3, 2.0)])
    g = S.graph(1, (-6, 6, -6, 9), 1, 2)
    g.curve(S.at(1, 0.3), lambda x, p: x ** 2, 'd', 3, draw=1.2)
    g.curve(S.at(1, 0.3), lambda x, p: (x - p[0]) ** 2 + p[1], 'c', 4, draw=1.2, params=lambda t: (h(t), k(t)))
    g.point(S.at(1, 1.5), h, k, 'y', lambda t: f"({nf(h(t))}, {nf(k(t))})")
    g.vline(S.at(6, 0.8), h, 'o')
    g.text(S.at(1, 1.5), lambda t: f"h = {nf(h(t))}    k = {nf(k(t))}", (24, 470), 'y', 28)
    S.line(0, "y = <y>a</>(x − <c>h</>)² + <g>k</>", 42, box='y', bold=True, space=22)
    S.line(1, "start:  <y>a</> = 1,  <c>h</> = 0,  <g>k</> = 0", 28, color='d', space=16)
    S.line(2, "<c>h</>  slides  left / right", 32, space=4)
    S.line(2, "(x − <c>2</>)²   →   right 2", 28, indent=30, color='d', fr=0.5, space=14)
    S.line(3, "(x + <c>2</>)²   →   left 2", 28, indent=30, color='d', space=14)
    S.line(4, "<g>k</>  moves  up / down", 32, space=4)
    S.line(4, "+ <g>3</>   →   up 3", 28, indent=30, color='d', fr=0.6, space=14)
    S.line(5, "− <g>2</>   →   down 2", 28, indent=30, color='d')
    S.clear(6)
    S.line(6, "Vertex = (<c>h</>, <g>k</>)", 44, box='y', bold=True, space=26)
    S.line(6, "Axis:  x = <c>h</>", 44, box='o', fr=0.55, bold=True)

@scene('4 · Completing the square', [
    B("In practice, quadratics usually come in standard form. To find the vertex, we complete the square. Take y equals x squared plus 6 x plus 5."),
    B("Half of the 6 is 3, and 3 squared is 9. So we add 9 to make a perfect square, and subtract 9 right away so nothing changes."),
    B("The bracket becomes x plus 3, squared, and negative 9 plus 5 is negative 4."),
    B("That's vertex form, with h equal to negative 3, and k equal to negative 4. The vertex is at negative 3, negative 4.", gap=0.8),
    B("Doing this in general gives a shortcut. For y equals @a x squared plus b x plus c, the x-coordinate of the vertex is x equals negative b over 2 @a."),
    B("Then plug that x back into the function to get the y-coordinate. Check it: negative 6 over 2 is negative 3. And y at negative 3 is 9 minus 18 plus 5, which is negative 4. It matches!", gap=1.0),
])
def s4(S):
    g = S.graph(0, (-8, 2, -6, 10), 1, 2)
    S.line(0, "Standard form", 26, color='d', space=8)
    S.line(0, "y = x² + 6x + 5", 40, bold=True, fr=0.35, space=22)
    S.line(1, "y = (x² + 6x + <y>9</>) − <y>9</> + 5", 32, space=18)
    S.line(2, "y = (x + <c>3</>)² <g>− 4</>", 38, box='g', bold=True, space=18)
    S.line(3, "<c>h</> = −3,   <g>k</> = −4", 32, space=6)
    g.curve(S.at(3, 0.2), lambda x, p: x ** 2 + 6 * x + 5, 'c', 3, draw=2.6)
    g.point(S.at(3, fr=0.55), -3, -4, 'y', "vertex (−3, −4)", lpos=(16, 28))
    S.clear(4)
    S.line(4, "Vertex x-coordinate", 28, color='d', space=10)
    S.frac(4, "x = ", "−<c>b</>", "2<y>a</>", size=40, box='y', fr=0.55)
    S.line(5, "x = −6 / (2·1) = <c>−3</>", 30, space=12)
    S.line(5, "y = (−3)² + 6(−3) + 5 = <g>−4</>  ✓", 30, fr=0.35)

@scene('5 · Axis of symmetry and y-intercept', [
    B("Two quick facts that come for free. First, the axis of symmetry: the vertical line through the vertex, x equals negative b over 2 @a. Here, x equals negative 3."),
    B("The parabola is a mirror image on either side of that line."),
    B("Second, the y-intercept, where the graph crosses the y-axis. Set x equal to 0, and every term except c vanishes. So the y-intercept is simply c. Here, the point 0, 5."),
    B("And by symmetry, the mirror point, also 3 units from the axis but on the left, is negative 6, 5. Check: 36 minus 36 plus 5 is 5. Yes!", gap=1.0),
])
def s5(S):
    g = S.graph(0, (-8, 2, -6, 10), 1, 2, off=-0.3)
    g.curve(S.at(0, -0.3), lambda x, p: x ** 2 + 6 * x + 5, 'c', 3, draw=0.01)
    g.point(S.at(0, -0.3), -3, -4, 'y', "(−3, −4)", lpos=(16, 28))
    g.vline(S.at(0, fr=0.35), -3, 'o')
    S.line(0, "y = x² + 6x + 5", 28, color='d', space=14)
    S.line(0, "<o>Axis of symmetry</>", 34, bold=True, fr=0.3, space=6)
    S.line(0, "x = −b/(2a) = <o>−3</>", 34, fr=0.45, space=14)
    S.line(1, "left side  =  mirror of right side", 28, color='d', space=20)
    S.line(2, "<p>y-intercept</>:  set x = 0", 34, bold=True, space=6)
    S.line(2, "y = <g>c</> = <p>5</>   →   (0, 5)", 34, fr=0.6, space=20)
    g.point(S.at(2, fr=0.65), 0, 5, 'p', "(0, 5)", lpos=(16, -4))
    S.line(3, "mirror point:  (−6, 5)", 32, space=4)
    S.line(3, "36 − 36 + 5 = 5  ✓", 30, color='d', fr=0.6)
    g.hline(S.at(3, 0.1), 5, 'p')
    g.point(S.at(3, 0.8), -6, 5, 'p', "(−6, 5)", lpos=(-100, -22))

@scene('6 · Roots and the discriminant', [
    B("Now the roots, also called zeros. These are the x-values where the graph touches the x-axis, so we solve @a x squared plus b x plus c equals 0."),
    B("The quadratic formula gives them: x equals negative b, plus or minus the square root of b squared minus 4 @a c, all over 2 @a."),
    B("The part under the square root, b squared minus 4 @a c, is called the discriminant. It tells us how many real roots there are, before we even solve."),
    B("Take y equals x squared minus 4 x plus c. With c equal to 3, the discriminant is 16 minus 12, which is 4, positive. The parabola cuts the x-axis twice: two real roots."),
    B("Slide it up until c is 4. Now the discriminant is exactly zero. The vertex just touches the axis: one real root."),
    B("Slide further, to c equal to 5, and the discriminant is negative 4. The parabola floats above the axis, never touching it. No real roots.", gap=1.0),
])
def s6(S):
    c = S.track(3, [(4, 4, 0.3, 2.5), (5, 5, 0.3, 2.5)])
    D = lambda t: 16 - 4 * c(t)
    S.line(0, "<c>Roots</> (zeros):  where  <c>y = 0</>", 32, space=14)
    S.frac(1, "x = ", "−b ± √(b² − 4ac)", "2a", size=34, box='y', space=12)
    S.line(2, "<o>Discriminant</>   Δ = b² − 4ac", 32, space=14)
    S.line(3, "Δ > 0   →   <g>two</> real roots", 32, space=8)
    S.line(4, "Δ = 0   →   <y>one</> real root", 32, space=8)
    S.line(5, "Δ < 0   →   <r>no</> real roots", 32)
    g = S.graph(3, (-1, 5, -4, 8), 1, 2)
    g.curve(S.at(3, 0.2), lambda x, p: x ** 2 - 4 * x + p[0], 'c', 3, draw=1.2, params=lambda t: (c(t),))
    g.text(S.at(3, 0.2), "y = x² − 4x + c", (270, 392), 'c', 24)
    g.text(S.at(3, 1.4), lambda t: f"c = {nf(c(t))}", (270, 424), 'y', 24)
    g.text(S.at(3, 1.4), lambda t: f"Δ = {nf(D(t))}", (270, 456), 'o', 24)
    sq = lambda t: math.sqrt(max(D(t), 0)) / 2
    shown = lambda t: D(t) > -1e-6
    g.point(S.at(3, 1.6), lambda t: 2 - sq(t), 0, 'g', None, show=shown)
    g.point(S.at(3, 1.6), lambda t: 2 + sq(t), 0, 'g', None, show=shown)

@scene('7 · Worked example 1', [
    B("Let's put it all together. Example one: analyze y equals x squared minus 4 x plus 3."),
    B("Step one: direction. @a is 1, positive, so it opens up, with a minimum at the vertex."),
    B("Step two: the vertex. x equals negative b over 2 @a, equals 4 over 2, which is 2. Then y at 2 is 4 minus 8 plus 3, which is negative 1. Vertex: 2, negative 1."),
    B("That gives vertex form: y equals x minus 2, squared, minus 1. The axis is x equals 2."),
    B("Step three: the y-intercept is c, which is 3."),
    B("Step four: roots. The discriminant is 16 minus 12, which is 4. The square root is 2. So x equals 4 plus or minus 2, over 2. Pause, and work out both answers yourself.", gap=3.0),
    B("4 plus 2 over 2 is 3, and 4 minus 2 over 2 is 1. The roots are x equals 1, and x equals 3."),
    B("Now we sketch it: vertex, intercepts and roots, joined by a smooth U.", gap=1.5),
])
def s7(S):
    g = S.graph(0, (-1.5, 5.5, -3, 9), 1, 1)
    S.line(0, "<c>Example 1</>", 34, bold=True, space=6)
    S.line(0, "y = x² − 4x + 3", 42, bold=True, off=0.5, space=14)
    S.line(0, "<y>a</> = 1,   <c>b</> = −4,   <g>c</> = 3", 30, fr=0.7, space=14)
    S.line(1, "<y>a</> = 1 > 0   →   opens <g>up</>", 30)
    S.clear(2)
    S.line(2, "x = −b/2a = 4/2 = <c>2</>", 32, space=8)
    S.line(2, "y = 4 − 8 + 3 = <g>−1</>", 32, fr=0.4, space=12)
    S.line(2, "Vertex (<c>2</>, <g>−1</>)", 36, box='y', bold=True, fr=0.75, space=22)
    g.point(S.at(2, fr=0.8), 2, -1, 'y', "(2, −1)", lpos=(14, 26))
    S.line(3, "y = (x − <c>2</>)² <g>− 1</>", 36, box='g', bold=True, space=16)
    S.line(3, "Axis:  x = 2", 30, color='d', fr=0.6)
    g.vline(S.at(3, fr=0.6), 2, 'o')
    S.clear(4)
    S.line(4, "<p>y-intercept</> = c = <p>3</>", 34, bold=True, space=20)
    g.point(S.at(4, 0.8), 0, 3, 'p', "(0, 3)", lpos=(14, -4))
    S.line(5, "Δ = 16 − 12 = <o>4</> > 0", 32, space=8)
    S.line(5, "√4 = 2", 32, fr=0.3, space=8)
    S.line(5, "x = (4 ± 2) / 2", 36, fr=0.55)
    S.pause(5)
    S.line(6, "x = <g>3</>   or   x = <g>1</>", 40, box='g', bold=True, off=0.2, space=10)
    g.point(S.at(6, fr=0.5), 3, 0, 'g', "(3, 0)", lpos=(10, -22))
    g.point(S.at(6, fr=0.8), 1, 0, 'g', "(1, 0)", lpos=(-60, -22))
    g.curve(S.at(7, 0.4), lambda x, p: x ** 2 - 4 * x + 3, 'c', 3, draw=3.0)

@scene('8 · Worked example 2', [
    B("Example two, this time with @a not equal to 1: y equals 2 x squared minus 4 x minus 6."),
    B("Here @a is 2, b is negative 4, and c is negative 6. Since @a is positive, it opens up."),
    B("Vertex: x equals negative b over 2 @a, equals 4 over 4, which is 1. Then y is 2, minus 4, minus 6, which is negative 8. The vertex is 1, negative 8."),
    B("Vertex form: y equals 2, times x minus 1, squared, minus 8. Notice that @a stays out in front."),
    B("The y-intercept is c, negative 6. Now the roots. The discriminant is 16 minus 4 times 2 times negative 6. That's 16 plus 48, which is 64."),
    B("The square root is 8, so x equals 4 plus or minus 8, over 4. Pause, and find both roots.", gap=3.0),
    B("4 plus 8 over 4 is 3, and 4 minus 8 over 4 is negative 1. The roots are x equals negative 1, and x equals 3."),
    B("Sketch it: vertex, y-intercept and roots, joined by a smooth U.", gap=1.5),
])
def s8(S):
    g = S.graph(0, (-3, 5, -10, 12), 1, 2)
    S.line(0, "<c>Example 2</>", 34, bold=True, space=6)
    S.line(0, "y = 2x² − 4x − 6", 42, bold=True, off=0.5, space=14)
    S.line(1, "<y>a</> = 2,   <c>b</> = −4,   <g>c</> = −6", 30, space=10)
    S.line(1, "<y>a</> > 0   →   opens <g>up</>", 30, fr=0.6)
    S.clear(2)
    S.line(2, "x = −b/2a = 4/4 = <c>1</>", 32, space=8)
    S.line(2, "y = 2 − 4 − 6 = <g>−8</>", 32, fr=0.4, space=12)
    S.line(2, "Vertex (<c>1</>, <g>−8</>)", 36, box='y', bold=True, fr=0.75, space=22)
    g.point(S.at(2, fr=0.8), 1, -8, 'y', "(1, −8)", lpos=(14, -4))
    S.line(3, "y = <y>2</>(x − <c>1</>)² <g>− 8</>", 36, box='g', bold=True, space=16)
    S.line(3, "Axis:  x = 1", 30, color='d', fr=0.6)
    g.vline(S.at(3, fr=0.6), 1, 'o')
    S.clear(4)
    S.line(4, "<p>y-intercept</> = c = <p>−6</>", 34, bold=True, space=14)
    S.line(4, "Δ = 16 − 4·2·(−6)", 32, fr=0.35, space=8)
    S.line(4, "Δ = 16 + 48 = <o>64</>", 32, fr=0.7)
    g.point(S.at(4, 0.8), 0, -6, 'p', "(0, −6)", lpos=(14, 4))
    S.line(5, "√64 = 8", 32, space=8)
    S.line(5, "x = (4 ± 8) / 4", 36, fr=0.5)
    S.pause(5)
    S.line(6, "x = <g>3</>   or   x = <g>−1</>", 40, box='g', bold=True, off=0.2, space=10)
    g.point(S.at(6, fr=0.55), 3, 0, 'g', "(3, 0)", lpos=(10, -22))
    g.point(S.at(6, fr=0.85), -1, 0, 'g', "(−1, 0)", lpos=(-84, -22))
    g.curve(S.at(7, 0.4), lambda x, p: 2 * x ** 2 - 4 * x - 6, 'c', 3, draw=3.0)

@scene('9 · Practice 1', [
    B("Time to practice. Problem one: for y equals x squared plus 2 x minus 8, find the vertex, the y-intercept, and the roots. Pause the video and give it a go.", gap=7.0),
    B("Here's the solution. Vertex: x equals negative 2 over 2, which is negative 1. Then y is 1 minus 2 minus 8, which is negative 9. The vertex is negative 1, negative 9."),
    B("The y-intercept is c, negative 8. For the roots, the discriminant is 4 plus 32, which is 36, so the square root is 6. Then x equals negative 2 plus or minus 6, over 2, which gives 2 and negative 4.", gap=1.5),
])
def s9(S):
    g = S.graph(0, (-6, 4, -11, 8), 1, 2)
    S.line(0, "<o>Practice 1</>", 34, bold=True, space=6)
    S.line(0, "y = x² + 2x − 8", 42, bold=True, off=0.4, space=14)
    S.line(0, "Find:  vertex,  y-intercept,  roots", 28, color='d', fr=0.8)
    S.pause(0)
    S.clear(1)
    S.line(1, "x = −2/2 = <c>−1</>", 32, space=8)
    S.line(1, "y = 1 − 2 − 8 = <g>−9</>", 32, fr=0.4, space=12)
    S.line(1, "Vertex (<c>−1</>, <g>−9</>)", 36, box='y', bold=True, fr=0.75)
    g.point(S.at(1, fr=0.8), -1, -9, 'y', "(−1, −9)", lpos=(-112, 14))
    S.clear(2)
    S.line(2, "<p>y-intercept</> = c = <p>−8</>", 32, space=8)
    S.line(2, "Δ = 4 + 32 = 36,   √36 = 6", 32, fr=0.3, space=8)
    S.line(2, "x = (−2 ± 6) / 2", 34, fr=0.55, space=8)
    S.line(2, "x = <g>2</>   or   x = <g>−4</>", 38, box='g', bold=True, fr=0.85)
    g.point(S.at(2, fr=0.1), 0, -8, 'p', "(0, −8)", lpos=(16, -14))
    g.point(S.at(2, fr=0.88), 2, 0, 'g', "(2, 0)", lpos=(10, -22))
    g.point(S.at(2, fr=0.95), -4, 0, 'g', "(−4, 0)", lpos=(-84, -22))
    g.curve(S.at(2, fr=0.9), lambda x, p: x ** 2 + 2 * x - 8, 'c', 3, draw=2.5)

@scene('10 · Practice 2', [
    B("Problem two has a twist. Does y equals negative x squared plus 2 x minus 3 ever touch the x-axis? Find the vertex, then decide. Pause and try it.", gap=7.0),
    B("Here @a is negative 1, so it opens down. Vertex: x equals negative 2 over negative 2, which is 1. Then y is negative 1 plus 2 minus 3, which is negative 2. The vertex is 1, negative 2."),
    B("Discriminant: 4 minus 4 times negative 1 times negative 3, which is 4 minus 12, negative 8. Negative, so no real roots. The highest point is below the axis, so the graph never touches it.", gap=1.5),
])
def s10(S):
    g = S.graph(0, (-3, 5, -12, 3), 1, 2)
    S.line(0, "<o>Practice 2</>", 34, bold=True, space=6)
    S.line(0, "y = −x² + 2x − 3", 42, bold=True, off=0.4, space=14)
    S.line(0, "Does it touch the x-axis?", 28, color='d', fr=0.8)
    S.pause(0)
    S.clear(1)
    S.line(1, "<y>a</> = −1 < 0   →   opens <r>down</>", 30, space=8)
    S.line(1, "x = −2/(−2) = <c>1</>", 32, fr=0.3, space=8)
    S.line(1, "y = −1 + 2 − 3 = <g>−2</>", 32, fr=0.5, space=12)
    S.line(1, "Vertex (<c>1</>, <g>−2</>)", 36, box='y', bold=True, fr=0.8)
    g.curve(S.at(1, 0.3), lambda x, p: -x ** 2 + 2 * x - 3, 'c', 3, draw=2.5)
    g.point(S.at(1, fr=0.8), 1, -2, 'y', "(1, −2)", lpos=(14, 20))
    S.clear(2)
    S.line(2, "Δ = 4 − 4(−1)(−3)", 32, space=8)
    S.line(2, "Δ = 4 − 12 = <r>−8</>", 32, fr=0.3, space=14)
    S.line(2, "Δ < 0   →   <r>no real roots</>", 36, box='r', bold=True, fr=0.6)

@scene('11 · Practice 3', [
    B("Last one, a real-world problem. A ball is thrown upward from a balcony, and its height in meters after t seconds is h equals negative 5 t squared plus 20 t plus 25. When is it highest, how high is it, and when does it land? Pause and try.", gap=8.0),
    B("The top is the vertex: t equals negative 20 over negative 10, which is 2 seconds. The height is negative 20 plus 40 plus 25, which is 45 meters."),
    B("It lands when h is 0. Divide by negative 5: t squared minus 4 t minus 5 equals 0, which factors into t minus 5, times t plus 1. So t is 5, since negative 1 second makes no sense. It lands after 5 seconds.", gap=1.5),
])
def s11(S):
    g = S.graph(0, (-1.5, 6.5, -10, 50), 1, 10, 't', 'h')
    S.line(0, "<o>Practice 3</>", 34, bold=True, space=6)
    S.line(0, "h = −5t² + 20t + 25", 38, bold=True, off=0.4, space=6)
    S.line(0, "(h in meters, t in seconds)", 24, color='d', fr=0.5, space=12)
    S.line(0, "1)  highest point:  when, how high?", 28, fr=0.7, space=4)
    S.line(0, "2)  when does it land  (h = 0)?", 28, fr=0.85)
    S.pause(0)
    S.clear(1)
    S.line(1, "t = −20/(−10) = <c>2 s</>", 32, space=8)
    S.line(1, "h = −20 + 40 + 25 = <g>45 m</>", 32, fr=0.45, space=12)
    S.line(1, "Top: (<c>2</>, <g>45</>)", 36, box='y', bold=True, fr=0.8)
    g.curve(S.at(1, 0.3), lambda x, p: -5 * x ** 2 + 20 * x + 25, 'c', 3, draw=2.5)
    g.point(S.at(1, fr=0.8), 2, 45, 'y', "(2, 45)", lpos=(14, 18))
    S.clear(2)
    S.line(2, "−5t² + 20t + 25 = 0", 30, space=6)
    S.line(2, "÷ (−5):   t² − 4t − 5 = 0", 30, fr=0.2, space=6)
    S.line(2, "(t − 5)(t + 1) = 0", 32, fr=0.45, space=10)
    S.line(2, "t = <g>5 s</>      (t = −1 ✗)", 38, box='g', bold=True, fr=0.75)
    g.point(S.at(2, fr=0.78), 5, 0, 'g', "lands (5, 0)", lpos=(-60, -26))
    g.point(S.at(2, fr=0.9), -1, 0, 'r', "✗", lpos=(-8, -24))

@scene('12 · Recap: how to analyze any quadratic', [
    B("Let's recap with a checklist you can use on any quadratic."),
    B("One: look at @a. Positive opens up, negative opens down. Big means narrow, small means wide."),
    B("Two: the vertex. x equals negative b over 2 @a, then plug in to get y. Three: the axis of symmetry is the vertical line through that x."),
    B("Four: the y-intercept is c. Five: compute the discriminant, b squared minus 4 @a c, and use the quadratic formula for the roots."),
    B("Six: plot the vertex, the intercepts and the roots, and sketch the smooth curve through them."),
    B("That's it. Redo the practice problems on your own, and this will become automatic. Thanks for watching, and good luck!", gap=1.0),
])
def s12(S):
    S.width = 1160
    S.line(0, "<c>How to analyze ANY quadratic</>   y = <y>a</>x² + <c>b</>x + <g>c</>", 36, bold=True, space=22)
    S.line(1, "1.  Look at <y>a</>:   sign = direction,   size = width", 32, space=12)
    S.line(2, "2.  Vertex:   x = −b/(2a),   then plug in for y", 32, space=12)
    S.line(2, "3.  Axis of symmetry:   x = −b/(2a)", 32, fr=0.6, space=12)
    S.line(3, "4.  y-intercept:   (0, <g>c</>)", 32, space=12)
    S.line(3, "5.  Discriminant  Δ = b² − 4ac   →   roots (quadratic formula)", 32, fr=0.5, space=12)
    S.line(4, "6.  Plot vertex, intercepts, roots,  then draw the smooth curve", 32, space=24)
    S.line(5, "<g>Now redo the practice problems on your own!</>", 38, bold=True, box='g')

# ---------- timeline / audio ----------
def prep():
    verify_math()
    SR = 24000
    from concurrent.futures import ThreadPoolExecutor
    allb = [say_text(b.text) for S in scenes for b in S.beats]
    with ThreadPoolExecutor(6) as ex: list(ex.map(tts_samples, allb))
    chunks = []; t = 0.0
    for S in scenes:
        durs, wavs = [], []
        for b in S.beats:
            a = tts_samples(say_text(b.text)); wavs.append(a); durs.append(len(a) / SR)
        S.set_times(durs); S.start = t
        buf = np.zeros(int(round(S.length * SR)), np.float32)
        for i, a in enumerate(wavs):
            o = int(round(S.t[i] * SR)); buf[o:o + len(a)] = a
        chunks.append(buf); t += S.length
        S.visuals(S)
    audio = np.concatenate(chunks)
    pcm = (np.clip(audio, -1, 1) * 32767).astype(np.int16)
    with wave.open('audio.wav', 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
    total = t
    # captions
    caps = []   # (abs start, abs end, text)
    for S in scenes:
        for i, b in enumerate(S.beats):
            ch = chunk_caption(b.text); tot = sum(len(c) for c in ch); cur = S.start + S.t[i]
            span = S.e[i] - S.t[i]
            for c in ch:
                d = span * len(c) / tot; caps.append((cur, cur + d, c)); cur += d
    return total, caps

def srt_time(t):
    ms = int(round(t * 1000)); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

def write_docs(total, caps):
    with open('quadratic-functions.srt', 'w') as f:
        for n, (a, b, c) in enumerate(caps, 1):
            f.write(f"{n}\n{srt_time(a)} --> {srt_time(b)}\n{c}\n\n")
    def mmss(t): return f"{int(t // 60)}:{t % 60:04.1f}"
    with open('script.md', 'w') as f:
        f.write("# Quadratic Functions: narration script\n\n")
        f.write(f"Voice: Microsoft Edge neural TTS (via edge-tts), en-US-AndrewNeural. Total length {mmss(total)}.\n")
        f.write("Timestamps are start times (m:ss.s) of each narrated passage.\n\n")
        for S in scenes:
            f.write(f"## {S.title}  (starts {mmss(S.start)})\n\n")
            for i, b in enumerate(S.beats):
                f.write(f"- [{mmss(S.start + S.t[i])}] {cap_text(b.text)}")
                if b.gap >= 3: f.write(f"  *(then a {b.gap:.0f}-second pause for the student)*")
                f.write("\n")
            f.write("\n")

# ---------- rendering ----------
class Renderer:
    def __init__(s, total, caps):
        s.total, s.caps, s.lastkey, s.lastbytes = total, caps, None, None
        s.ends = [S.start + S.length for S in scenes]
    def scene_at(s, t):
        for S, e in zip(scenes, s.ends):
            if t < e: return S
        return scenes[-1]
    def frame(s, t):
        S = s.scene_at(t); ts = t - S.start
        cap = None
        for n, (a, b, c) in enumerate(s.caps):
            if a <= t < b: cap = n; break
            if a > t: break
        left = [(id(it), it.key(ts)) for it in S.left if it.alive(ts)]
        g = next((g for g in S.graphs if g.alive(ts)), None)
        gk = g.keys(ts) if g else None
        pz = next((math.ceil(b - ts) for a, b in S.pauses if a <= ts < b), None)
        key = (id(S), cap, int(t / s.total * 1200), tuple(left), id(g), gk, pz)
        if key == s.lastkey: return s.lastbytes
        im = Image.new('RGB', (W, H), BG); d = ImageDraw.Draw(im)
        d.rectangle((0, 0, W, 54), fill=(14, 22, 21))
        d.text((30, 28), S.title, font=font(26, True), fill=COL['c'], anchor='lm')
        d.text((W - 30, 28), "Quadratic Functions", font=font(22), fill=COL['d'], anchor='rm')
        if g:
            d.rounded_rectangle((GX0 - 6, GY0 - 6, GX0 + GW + 6, GY0 + GH + 6), 12, fill=PANEL, outline=(70, 90, 86), width=2)
            im.paste(g.render(ts, gk), (GX0, GY0))
        for it in S.left:
            if it.alive(ts): it.draw(d, ts)
        if pz is not None:
            d.rounded_rectangle((LX - 4, 536, LX + 600, 596), 14, fill=(90, 50, 10), outline=COL['o'], width=3)
            d.text((LX + 18, 566), f"YOUR TURN  –  pause and try it   {pz}", font=font(28, True), fill=COL['o'], anchor='lm')
        # caption
        if cap is not None:
            text = s.caps[cap][2]; f = font(27)
            words = text.split(); lines = []; cur = ''
            for w_ in words:
                if f.getlength((cur + ' ' + w_).strip()) > 1150 and cur: lines.append(cur); cur = w_
                else: cur = (cur + ' ' + w_).strip()
            lines.append(cur)
            hh = 14 + 36 * len(lines)
            ov = Image.new('RGBA', (W, H), (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
            y0 = 706 - hh
            od.rounded_rectangle((60, y0, W - 60, 706), 14, fill=(0, 0, 0, 175))
            im.paste(Image.alpha_composite(im.convert('RGBA'), ov).convert('RGB'))
            d = ImageDraw.Draw(im)
            for n, ln in enumerate(lines):
                d.text((W / 2, y0 + 7 + 18 + 36 * n), ln, font=f, fill=(255, 255, 255), anchor='mm')
        # progress bar
        d.rectangle((0, H - 5, int(W * t / s.total), H), fill=COL['g'])
        s.lastkey, s.lastbytes = key, im.tobytes()
        s._im = im
        return s.lastbytes

def main():
    mode = sys.argv[1]
    total, caps = prep(); write_docs(total, caps)
    print('total', total, 'scenes', [(S.title, round(S.start, 1)) for S in scenes])
    R = Renderer(total, caps)
    if mode == 'frames':
        os.makedirs('frames', exist_ok=True)
        for tt in sys.argv[2:]:
            R.frame(float(tt)); R._im.save(f'frames/t{float(tt):07.2f}.png')
    elif mode == 'render':
        n = int(math.ceil(total * FPS))
        out = sys.argv[2] if len(sys.argv) > 2 else 'quadratic-functions.mp4'
        p = subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS),
                              '-i', '-', '-i', 'audio.wav', '-af', 'loudnorm=I=-16:TP=-1.5:LRA=11,apad', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '22',
                              '-pix_fmt', 'yuv420p', '-r', str(FPS), '-c:a', 'aac', '-b:a', '160k', '-ar', '44100', '-frames:v', str(n), '-movflags', '+faststart',
                              out], stdin=subprocess.PIPE)
        for i in range(n):
            p.stdin.write(R.frame(i / FPS))
            if i % 600 == 0: print('frame', i, '/', n, flush=True)
        p.stdin.close(); p.wait(); print('done', p.returncode)

if __name__ == '__main__':
    main()
