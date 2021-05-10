from cps.caplisp import *


def test_const():
    assert Caplisp.parse_python('23').eval({}) == 23
    assert Caplisp.parse_python('"foo"').eval({}) == "foo"

def test_variable():
    assert Caplisp.parse_python('x').eval({'x': 23}) == 23

def test_binop():
    expr = Caplisp.parse_python('x*y')
    assert expr.eval({'x':5, 'y': 7}) == 35
    assert expr.unparse() == '(* x y)'

def test_list():
    l = Caplisp.parse_python('[1,2]')
    assert l.eval({}) == [1, 2]
    assert l.unparse() == '(1 2)'

def test_func():
    f = Caplisp.parse_python('f()')
    assert f.unparse() == '(f)'
    assert f.eval({'f': lambda: 23}) == 23

    f = Caplisp.parse_python('f(x)')
    assert f.unparse() == '(f x)'
    assert f.eval({'f': lambda x: x*4, 'x': 16}) == 64

def test_nesting():
    f = Caplisp.parse_python('f(x) * g(y) + 3')
    assert f.unparse() == '(+ (* (f x) (g y)) 3)'
    assert f.eval({'f': lambda x: x+3, 'g': lambda x: x*2, 'x': 1, 'y': 4}) == 35
