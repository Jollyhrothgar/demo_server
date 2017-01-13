import mlpux
import json
import numpy as np
"""
A fake module which will be used for unit testing the demo framework.

Here, I'll slowly accumulate a list of possible demo architectures to run through
the demo framework.
"""

@mlpux.demo
def make_2D_data(x_min, x_max, num, ret_type='tuple', func=np.sin):
    """
    Make data set conisisting of x and y values for a 2D plot.

    param1: x_min: minimum of domain
    param2: x_max: maximium of domain
    param3: number of points to generate
    param5: default: callback representing the function that maps x-values to y values.
    param4: return type: 'tuple', 'dict', or 'numpy_tensor' (i.e. x-y values zipped together)
    """
    name = make_2D_data.__name__
    x = np.linspace(start=x_min, stop=x_max, num=num)
    y = func(x)

    if ret_type == 'tuple':
        return x, y
    if ret_type == 'dict':
        return {'x':list(x), 'y':list(y) }
    else:
        raise ValueError("Return of {} must be an iterable representing 2D data set. Options are 'tuple' or 'dict'".format(name))

@mlpux.demo
def square(x:float):
    """
    takes a floating point input, returns the square of that input
    """
    return x*x

@mlpux.demo
def no_args():
    """
    A functiont that returns some kind of string
    """
    return_string = "whoop-de doo!"
    return return_string

@mlpux.demo
def str_args(mystr:str, myint:int):
    """
    A function which puts an int and a string into a string
    """
    return "Hi there {0}, you earned {1} schmeckles".format(mystr, myint)

@mlpux.demo
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
   
@mlpux.demo
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

@mlpux.demo
# annotation -> gets evaluated....
def hard_func(*args, arg1=1, arg2=2, default1="Fanny", default2:float=19.5, **kwargs) -> str_args:
    """
    A complicated function signature with list-type arguments, named arguments,
    default arguments, and keyword arguments. Yikes!!! There's even partial
    annotation.
    """
    ret_vals = {}
    ret_vals['msg_1'] = "There were {} additional keyword arguments **kwargs and {} *args type positional arguments".format(len(kwargs.keys()),len(args))
    try:
        ret_vals['msg_2'] = "the result of arg1 + arg2 is {}".format(arg1+arg2)
    except:
        ret_vals['msg_2'] = "arg1: {}, arg2: {} cannot be combined with the + operator.".format(repr(arg1),repr(arg2))
    ret_vals['msg_3'] = "The default argument of default2 was 19.5, and it is now set to {}".format(repr(default2))
    ret_vals['msg_4'] = "This function accepts additional arguments with *args and **kwargs, but its signature is horrible. Args were: {} and kwargs were: {}".format(repr(args), repr(kwargs))

    return ret_vals
    

@mlpux.demo
def arbitrary_func(*args, **kwargs):
    """ 
    A function that takes an arbitrary list of named and unnamed arguments

    The author should probably document somewhere what to use

    Note that order of args and kwargs matters, therefore, order should be maintained no matter what.
    """
    return_string = "number of args: {0}, number of kwargs: {1}".format(len(args),len(kwargs))
    return return_string

@mlpux.demo
def args_only(*args):
    """
    A function which consists only of positional arguments, with no keywords.

    Call with any number of parameters - returns a list of those parameters back.abs
    """
    ret_val = {i:v for i,v in enumerate(args)}
    if len(ret_val.keys()) == 0:
        ret_val = {'status':'success'}
    return ret_val;

@mlpux.demo
def kwargs_only(**kwargs):
    """
    A function that only takes keyword arguments, and returns them.
    """
    ret_val = {k:v for k,v in kwargs.items()}
    if len(ret_val.keys()) == 0:
        ret_val = {'status':'success'}
    return ret_val


