import ast
import inspect


def foo():
    print('starting up')
    name = input('enter your name: ')
    age = input('enter your age: ')
    print(f'sorry, {name}, if only you were {age + 1} years old I could let you in')

def anon2(env, age):
    env['age'] = age
    print(f"sorry, {env['name']}, if only you were {int(env['age']) + 1} years old I could let you in")

def anon1(env, name):
    anon2_t = ast.parse(inspect.getsource(anon2))
    env['name'] = name
    return input_cps(env, 'enter your age: ', anon2_t)

def foo_cps(env):
    print('starting up')
    anon1_t = ast.parse(inspect.getsource(anon1))
    return input_cps(env, 'enter your name: ', anon1_t)


# this version prompts and returns a continuation
def input_cps_direct(env, prompt, cont):
    result = input(prompt)
    return lambda: cont(env, result)


# this version prints the prompt and returns a continuation that wants an input parameter
def input_cps_indirect(env, prompt, cont):
    print(prompt)
    return lambda result: cont(env, result)


def input_cps_tree(env, prompt, cont_t):
    print(prompt)
    return prompt, env, ast.unparse(cont_t)


#input_cps = input_cps_direct
input_cps = input_cps_tree

#def cps_continue(env, value, cont_t):


def simple2():
    f()
    g()

def simple2_cps():
    """
Module(
  body=[
    FunctionDef(
      name='simple2_cps',
      args=arguments(
        posonlyargs=[],
        args=[],
        kwonlyargs=[],
        kw_defaults=[],
        defaults=[]),
      body=[
        Expr(
          value=Call(
            func=Name(id='f', ctx=Load()),
            args=[
              Lambda(
                args=arguments(
                  posonlyargs=[],
                  args=[],
                  kwonlyargs=[],
                  kw_defaults=[],
                  defaults=[]),
                body=Call(
                  func=Name(id='g', ctx=Load()),
                  args=[],
                  keywords=[]))],
            keywords=[]))],
      decorator_list=[])],
  type_ignores=[])

    :return:
    """
    f(lambda: g())

def astentatious(func):
    """
    Convert a function to the source of the body of the function, because pervert reasons.

    :param func: the function to decorate
    :return: the body of the function
    """
    fdef = ast.parse(inspect.getsource(func))
    mdef = ast.Module(body=fdef.body[0].body, type_ignores=[])
    return ast.unparse(mdef)


@astentatious
def myfoo(x):
    print(f'Hello, {x}')

# myfoo is now a string with contents "print(f'Hello, {x}')"

def main_orig():
    source = inspect.getsource(foo)
    raw = ast.parse(source)
    print(ast.dump(raw, indent=2))
    print(ast.unparse(raw))
    foo_cps({})

