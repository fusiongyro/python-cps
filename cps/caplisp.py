"""
A new approach.

We translate Python into an internal language with CPS. The internal language is much smaller than full Python.


"""
import abc
import collections.abc
import operator
import typing
from typing import Any
import ast

class Caplisp:
    @staticmethod
    def parse_python(str) -> "CaplispNode":
        my_ast = ast.parse(str)
        return PythonToCaplisp().visit(my_ast)

    @staticmethod
    def parse_caplisp(str) -> "CaplispNode":
        raise NotImplementedError


class CaplispInterpreter:
    def __init__(self, program, environment=None):
        self.environment = environment if environment else {}
        self.program = program

    def run(self):
        self.eval(self.program, self.environment)

    def eval(self, term, environment):
        term.eval(environment)


class CaplispNode(abc.ABC):
    @abc.abstractmethod
    def eval(self, environment: dict[str, Any]) -> Any:
        pass

    @abc.abstractmethod
    def unparse(self) -> str:
        pass


class CaplispConstant(CaplispNode):
    def __init__(self, value):
        self.value = value

    def eval(self, environment: dict[str, Any]) -> Any:
        return self.value

    def unparse(self):
        return str(self.value)


class CaplispVariable(CaplispNode):
    def __init__(self, id):
        self.id = id

    def eval(self, environment: dict[str, Any]) -> Any:
        return environment[self.id]

    def unparse(self):
        return self.id


class CaplispFuncall(CaplispNode):
    def __init__(self, func: Any, *args: CaplispNode):
        self.func = func
        self.args = args

    def unparse(self) -> str:
        return CaplispList([self.func] + list(self.args)).unparse()

    def eval(self, environment: dict[str, Any]) -> Any:
        return self.func.eval(environment)(*[a.eval(environment) for a in self.args])


class CaplispFunctionReference(CaplispNode):
    def __init__(self, realfunc: typing.Callable, name: str):
        self.realfunc = realfunc
        self.name = name

    def unparse(self):
        return self.name

    def eval(self, environment: dict[str, Any]) -> Any:
        return self.realfunc


class CaplispList(CaplispNode):
    def __init__(self, elements: list[CaplispNode]):
        self.elements = elements

    def eval(self, environment: dict[str, Any]) -> Any:
        return [item.eval(environment) for item in self.elements]

    def unparse(self) -> str:
        return '(' + ' '.join(item.unparse() for item in self.elements) + ')'


class PythonToCaplisp(ast.NodeVisitor):
    def visit_Constant(self, node: ast.Constant) -> Any:
        return CaplispConstant(node.value)

    def visit_Module(self, node: ast.Module) -> Any:
        return self.visit(node.body[0])

    def visit_Expr(self, node: ast.Expr) -> Any:
        return self.visit(node.value)

    def visit_Name(self, node: ast.Name) -> Any:
        return CaplispVariable(node.id)

    def visit_BinOp(self, node: ast.BinOp) -> Any:
        opmap = {ast.Add: operator.add,
                 ast.Sub: operator.sub,
                 ast.Mult: operator.mul,
                 ast.MatMult: operator.matmul,
                 ast.Div: operator.truediv,
                 ast.Mod: operator.mod,
                 ast.Pow: operator.pow,
                 ast.LShift: operator.lshift,
                 ast.RShift: operator.rshift,
                 ast.BitOr: operator.or_,
                 ast.BitXor: operator.xor,
                 ast.BitAnd: operator.and_,
                 ast.FloorDiv: operator.floordiv}
        opnames = {ast.Add: '+',
                 ast.Sub: '-',
                 ast.Mult: '*',
                 ast.MatMult: '@',
                 ast.Div: '/',
                 ast.Mod: '%',
                 ast.Pow: '**',
                 ast.LShift: '<<',
                 ast.RShift: '>>',
                 ast.BitOr: '|',
                 ast.BitXor: '^',
                 ast.BitAnd: '&',
                 ast.FloorDiv: '//'}
        func = CaplispFunctionReference(opmap[type(node.op)], opnames[type(node.op)])
        return CaplispFuncall(func, self.visit(node.left), self.visit(node.right))

    def visit_List(self, node: ast.List) -> Any:
        return CaplispList([self.visit(x) for x in node.elts])

    def visit_Call(self, node: ast.Call) -> Any:
        return CaplispList([self.visit(node.func)] + [self.visit(arg) for arg in node.args])

    def generic_visit(self, node: ast.AST) -> Any:
        raise NotImplementedError