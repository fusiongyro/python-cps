import ast
from typing import Any


class SimPy:
    BUILTINS = {"complete": lambda: None}

    @staticmethod
    def parse(code: str) -> ast.AST:
        # first we parse the AST
        # then we transform it to CPS style
        normal = ast.parse(code)
        return CpsTransformer().visit(normal)

    @classmethod
    def eval(cls, node: ast.AST, env: dict[str, Any]) -> Any:
        # the right way to do this is with a recursive function
        # that unfortunately necessitates some rather gross type inspection
        if isinstance(node, ast.Module):
            assert len(node.body) == 1
            return cls.eval(node.body[0], env)

        elif isinstance(node, ast.Expr):
            assert isinstance(node.value, ast.Call)
            return cls.eval(node.value, env)

        elif isinstance(node, ast.Name):
            return (env | cls.BUILTINS)[node.id]

        elif isinstance(node, ast.Lambda):
            # so the problem here is that we need to both be able to actually call this, and be able to turn it
            # back into an ast node
            return Lambda(node.args, node.body, env)

        elif isinstance(node, ast.Call):
            # handle the lambda expression by preparing an invocation to eval
            # with the right environment
            return cls.eval(node.func, env)(*[cls.eval(arg, env) for arg in node.args])

        else:
            raise NotImplementedError(type(node))


class Lambda(ast.Lambda):
    def __init__(self, args, body, environment: dict[str, Any]):
        super().__init__(args, body)
        self.environment = environment

    def __call__(self, *args, **kwargs):
        # step 1: need to match up my args and their names
        new_environment = {arg.arg: value for arg, value in zip(self.args.args, args)}
        SimPy.eval(self.body, new_environment | self.environment)


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
