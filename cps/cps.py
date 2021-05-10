"""
Some random notes.

To handle a block like:
  f()
  g()

We can transform it into this:

  (lambda _: g())(f())

Another approach is:

  f_cps(lambda: g_cps(lambda: None))

Where f and g have been mechanically transformed to call the continuation instead of returning.

An assignment is handled the same way:

  x = f()
  g()

becomes

  f_cps(lambda x: g_cps(lambda: None))

and something more interesting like:

  g(f())

becomes:

  f_cps(lambda x: g_cps(x, lambda: None))

Conditions are handled by insinuating a new continuation-friendly if function:

  if cond:
    f()
  else:
    g()
  h()

becomes:

  if_cps(cond, lambda cont: f_cps(cont), lambda cont: g_cps(cont), lambda: h())

The implementation of this becomes:

  def if_cps(cond, thencase, elsecase, after):
    if cond:
      return thencase(after)
    else:
      return elsecase(after)


For-loops can be unrolled:

  for item in [1,2,3,4]:
    f(item)
  h()

becomes:

  for_cps(lambda item, cont: f_cps(item, cont), [1,2,3,4], lambda: h())

which is defined in such a way to produce something like this:

  (lambda item, cont: f_cps(item, lambda item, cont: f_cps(item, lambda item, cont: ....)(1)(2)(3)(4)

Return values are handled like so:

  return f()

becomes

  f(lambda r: r)

in contrast to

  f()

which becomes

  f(lambda: None)

For my application, either the module returns a continuation to be saved, or it returns some value we don't care about.

"""

import ast
from typing import Any, NamedTuple, Optional, Union

import asteval as asteval


class CapabilityExecutionState(NamedTuple):
    environment: dict
    continuation: str
    message_pattern: str

    @staticmethod
    def load(self, state: str) -> "CapabilityExecutionState":
        """
        Load this capability execution state from the persisted string.

        :param state:  the freeze-dried state of this execution
        :return: a
        """
        pass

    def resume(self, message) -> Union[Any, "CapabilityExecutionState"]:
        """
        Do whatever work can be done on this execution in response to this message
        before we return to a waiting state.

        :return: a new CapabilityExecutionState for the next step
        """
        # Step 1: parse the continuation back to an AST
        tree = ast.parse(self.continuation)

        # Step 2: evaluate to the next step
        self.partial_evaluate(tree, message, self.environment)

    def partial_evaluate(self, tree: ast.Module, msg: Any, environment: dict[str,Any]):
        # As a rule of thumb, whenever start, we wind up with a Module node. Inside that Module,
        # we can safely assume there is a body with a single element, which is a lambda expression.
        # We need to pass the 'msg' to that lambda expression to evaluate the next step, so we must
        # now wrap it in a Call.
        call_lambda = ast.Expr(ast.Call(func=tree.body[0].value, args=[ast.Constant(value=msg)], keywords=[]))

        # now we can proceed with evaluation
        return asteval.Interpreter(symtable=self.expand_environment(environment)).run(call_lambda)

    def expand_environment(self, env: dict[str, Any]) -> dict[str, Any]:
        # Augment the environment we received by adding in the functions we understand
        # TODO: implement this
        return env

    def persist(self) -> str:
        """
        Persist this capability execution state to a string that can be saved somewhere else, such as a database.

        :return: the capability execution state
        """
        # TODO: make sure to remove the functions we understand from the environment

        pass


class CapabilityDefinition:
    def __init__(self, code):
        self.code = code

    def execute(self) -> Union[Any, CapabilityExecutionState]:
        """
        Execute the initial work of this capability definition and return a new CapabilityExecutionState.
        :return: the execution, as it is after completing its first steps
        """

        # Step 1: parse the code
        tree = ast.parse(self.code)

        # Step 2: CPS transform the code
        cps_transformed = CpsTransform().visit(tree)

        # Step 3: unparse the CPS-transformed code
        cps_code = ast.unparse(cps_transformed)

        # Step 4: using a blank initial environment, we now have an initial
        # capability execution state
        initial_state = CapabilityExecutionState({}, cps_code, None)

        # Step 5: evaluate the initial state and return the result
        return initial_state.resume(None)

    @staticmethod
    def compile_capability(capability_definition: str) -> "CapabilityDefinition":
        """
        Compile a capability definition from text, in a Python-like language.

        :param capability_definition: source code for this capability definition
        :return: a compiled CapabilityDefinition
        """
        pass


class CpsTransform(ast.NodeTransformer):
    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        # so the trick here is, if the body has more than one item in it, we have to manufacture some CPS magic
        if len(node.body) == 1:
            return node
        elif len(node.body) == 2:
            # let's handle the two-item case
            return ast.FunctionDef(name=node.name,
                                   args=node.args,
                                   body=self.cps_transform(node.body),
                                   decorator_list=node.decorator_list,
                                   lineno=node.lineno)
        else:
            print(ast.dump(node, indent=2))
            raise NotImplementedError(f"don't know how to process functions with body of length {len(node.body)}")

    def cps_transform(self, exprs: list[ast.Expr]) -> list[ast.Expr]:
        e1, e2 = exprs
        # e1 is a function call, so I'm going to turn e2 into a lambda and pass it as an argument to e1
        new_e2 = ast.Lambda(args=ast.arguments(posonlyargs=[], args=[], defaults=[], kwonlyargs=[]), body=self.visit(e2))
        call = ast.Call(func=e1.value.func, args=e1.value.args + [new_e2], keywords=e1.value.keywords)
        new_e1 = ast.Expr(value=self.visit(call))
        return [new_e1]

    def visit_Call(self, node: ast.Call) -> ast.Call:
        assert type(node.func) == type(ast.Name())
        return ast.Call(func=ast.Name(id=node.func.id + '_cps', ctx=ast.Load()),
                        args=node.args,
                        keywords=node.keywords)



class MyEvaluator(ast.NodeVisitor):
    def visit_Constant(self, node: ast.Constant) -> Any:
        return node.value

def dump(node):
    print(ast.dump(node, indent=2))


def main():
    #simple2_ast = ast.parse(inspect.getsource(simple2))
    #simple2_ast_cps = CpsTransform().visit(simple2_ast)
    #print(ast.dump(simple2_ast_cps, indent=2))
    #print(ast.unparse(simple2_ast_cps))

    evalu = MyEvaluator()
    my_ast = ast.parse('23')
    print(f'result: {evalu.visit(my_ast).body[0]}')

if __name__ == '__main__':
    main()