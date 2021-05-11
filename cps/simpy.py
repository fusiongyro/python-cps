import ast
from typing import Any


class SimPy:
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

        elif isinstance(node, ast.Call):
            # handle the lambda expression by preparing an invocation to eval
            # with the right environment
            def lambda_miracle(lambda_ast: ast.Lambda, varname: str):
                return lambda value: cls.eval(lambda_ast, env | {varname: value})

            args = node.args
            if isinstance(args[-1], ast.Lambda):
                args[-1] = lambda_miracle(args[-1], args[-1].args.args[0].arg)
            return env[node.func.id](*args)

        else:
            raise NotImplementedError(type(node))


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
