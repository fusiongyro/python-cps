import ast
from cps.simpy import SimPy, Lambda


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


def test_suspend():
    myast = SimPy.parse("suspend()\ndo_something()")

    called = []

    def suspend(cont):
        called.append("suspend")
        return cont

    def do_something(cont):
        called.append("do_something")
        cont(None)

    cont = SimPy.eval(myast, {"suspend": suspend, "do_something": do_something})
    assert called == ["suspend"]

    # now we must try and resume the continuation
    assert isinstance(cont, Lambda)
    cont(None)
    assert called == ["suspend", "do_something"]

    # want to see something crazy? let's clear called
    called = []
    # we can continue a second time
    cont(None)
    # and now we've only done the second half
    assert called == ["do_something"]


# def test_compose():
#     myast = SimPy.parse('f(g())')
#     assert myast == ast.parse('g(lambda x: f(x))')
