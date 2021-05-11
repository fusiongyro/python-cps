import ast
from typing import Any


class SimPy:
    @staticmethod
    def parse(code: str) -> ast.AST:
        # first we parse the AST
        # then we transform it to CPS style
        normal = ast.parse(code)
        return CpsTransformer().visit(normal)

    @staticmethod
    def eval(code: ast.AST, env: dict[str, Any]) -> Any:
        return SimpleEvaluator(env).visit(code)


class CpsTransformer(ast.NodeTransformer):
    def visit_Module(self, node: ast.Module) -> Any:
        # every chain terminates in a call to "complete()", which our interpreter catches
        body = node.body + [
            ast.Expr(value=ast.Call(func=ast.Name(id="complete", ctx=ast.Load()), args=[], keywords=[]))
        ]
        return ast.Module(body=self.cps_convert(body), type_ignores=node.type_ignores)

    def cps_convert(self, body: list[ast.Expr]):
        if len(body) == 1:
            return body
        else:
            # take the last two items from the body and convert them
            new_last = self.cps_convert_two(body[-2], body[-1])
            return self.cps_convert(body[:-2] + [new_last])

    def cps_convert_two(self, penultimate: ast.Expr, ultimate: ast.Expr) -> ast.Expr:
        # whatever comes next is definitely a lambda expression
        inner = ast.Lambda(args=self.blank_arguments(), body=ultimate.value)

        # if the thing before that is a function call, pass inner as a continuation to it
        if isinstance(penultimate.value, ast.Call):
            return ast.Expr(
                value=ast.Call(
                    func=penultimate.value.func,
                    args=penultimate.value.args + [inner],
                    keywords=penultimate.value.keywords,
                )
            )
        else:
            raise NotImplementedError

    def blank_arguments(self):
        return ast.arguments(
            posonlyargs=[], args=[ast.arg(arg="_")], vararg=None, kwonlyargs=[], kw_defaults=[], kwarg=None, defaults=[]
        )


class SimPyLambda(ast.Lambda):
    def __call__(self, arg):
        # FIXME: dude, where's my environment?
        SimpleEvaluator({self.args.args[0].arg: arg}).visit(self.body)


class SimpleEvaluator(ast.NodeVisitor):
    def __init__(self, env: dict[str, Any]):
        self.env = env

    def visit_Module(self, node: ast.Module) -> Any:
        # we should never have more than one expression in the body
        assert len(node.body) == 1
        return self.visit(node.body[0])

    def visit_Expr(self, node: ast.Expr) -> Any:
        # at the moment we only support Calls
        assert isinstance(node.value, ast.Call)
        return self.visit(node.value)

    def visit_Call(self, node: ast.Call) -> Any:
        return self.env[node.func.id](*node.args)
