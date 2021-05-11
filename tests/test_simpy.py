import ast
from cps.simpy import SimPy


def test_simple():
    myast = SimPy.parse("f()\ng()")
    assert ast.dump(myast, indent=2) == ast.dump(ast.parse("f(lambda _: g(lambda _: complete()))"), indent=2)

    f_called = False

    def f(cont):
        f_called = True
        cont(None)

    g_called = False

    def g(cont):
        g_called = True
        cont(None)

    SimPy.eval(myast, {"f": f, "g": g})
    assert f_called == True
    assert g_called == True


# LATER
# def test_compose():
#     myast = SimPy.parse('f(g())')
#     assert myast == ast.parse('g(lambda x: f(x))')
