import ast
from cps.simpy import SimPy


def test_simple():
    myast = SimPy.parse("f()\ng()")
    assert ast.dump(myast, indent=2) == ast.dump(ast.parse("f(lambda _: g(lambda _: complete()))"), indent=2)

    called = []

    def f(cont):
        called.append("f")
        cont(None)

    def g(cont):
        called.append("g")
        cont(None)

    SimPy.eval(myast, {"f": f, "g": g})
    assert called == ["f", "g"]


# LATER
# def test_compose():
#     myast = SimPy.parse('f(g())')
#     assert myast == ast.parse('g(lambda x: f(x))')
