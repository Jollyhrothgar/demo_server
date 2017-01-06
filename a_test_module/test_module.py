import mlpux
import json
"""
A fake module which will be used for unit testing the demo framework.

Here, I'll slowly accumulate a list of possible demo architectures to run through
the demo framework.
"""

@mlpux.demo(x = { 'var':'x', 'type':'slider', 'min_range':-25, 'max_range':25 } )
def square(x:float):
    """
    takes a floating point input, returns the square of that input
    """
    return x*x

@mlpux.demo()
def no_args():
    """
    A functiont that returns some kind of string
    """
    return_string = "whoop-de doo!"
    return return_string

@mlpux.demo()
def str_args(mystr:str, myint:int):
    """
    A function which puts an int and a string into a string
    """
    return "Hi there {0}, you earned {1} schmeckles".format(mystr, myint)

@mlpux.demo()
def args_notype(arg1, arg2, arg3):
    """
    A function which takes three arguments, but type is not specified.

    args 1 and 2 should be integers, which are added, arg3 is a string 
    """

    return_string = "{0} + {1} = {2}, says Mr. {3}".format(arg1, arg2, arg1+arg2, arg3)

    complicated_object = { 
        "result":return_string,
        "arg1":arg1,
        "arg2":arg2,
        "arg3":arg3,
        "arg_list":[arg1, arg2, arg3],
        }
    return complicated_object 
   
@mlpux.demo()
def args_notype_clone(arg1, arg2, arg3):
    """
    A function which takes three arguments, but type is not specified.

    args 1 and 2 should be integers, which are added, arg3 is a string 

    A clone of args_notype but returns json string.
    """

    return_string = "{0} + {1} = {2}, says Mr. {3}".format(arg1, arg2, arg1+arg2, arg3)

    complicated_object = { 
        "result":return_string,
        "arg1":arg1,
        "arg2":arg2,
        "arg3":arg3,
        "arg_list":[arg1, arg2, arg3],
        }
    return json.dumps(complicated_object)

@mlpux.demo()
# annotation -> gets evaluated....
def hard_func(arg1, arg2, default1="Fanny", default2:float=19.5, *args, **kwargs) -> str_args:
    """
    A complicated function signature with list-type arguments, named arguments,
    default arguments, and keyword arguments. Yikes!!! There's even partial
    annotation.
    """
    return str_args("happy","gilmore")

@mlpux.demo()
def arbitrary_func(*args, **kwargs):
    """ 
    A function that takes an arbitrary list of named and unnamed arguments

    The author should probably document somewhere what to use

    Note that order of args and kwargs matters, therefore, order should be maintained no matter what.
    """
    return_string = "number of args: {0}, number of kwargs: {1}".format(len(args),len(kwargs))
    return return_string

@mlpux.demo()
def args_only(*args):
    """
    A function which consists only of positional arguments, with no keywords.

    Call with any number of parameters - returns a list of those parameters back.abs
    """
    return args;

@mlpux.demo()
def kwargs_only(**kwargs):
    """
    A function that only takes keyword arguments, and returns them.
    """
    return kwargs


