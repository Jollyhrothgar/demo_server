import mlpux
import json
import numpy as np
import random
"""
A fake module which will be used for unit testing the demo framework.

Here, I'll slowly accumulate a list of possible demo architectures to run through
the demo framework.
"""

@mlpux.Interactive()
@mlpux.Plot2D(title="A Plot Title")
@mlpux.Slider(arg='x_min', min_val=0, max_val=50, ndiv=30)
@mlpux.Slider(arg='x_max', min_val=100, max_val=250, ndiv=30)
@mlpux.Demo()
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
        return list(x),list(y)
    if ret_type == 'dict':
        return {'x':list(x), 'y':list(y) }
    else:
        raise ValueError("Return of {} must be an iterable representing 2D data set. Options are 'tuple' or 'dict'".format(name))


# TODO: generate a table
def create_a_table(rows, **kwargs):
    """
    Creates a table with headers determined by the keyword arguments.
    """
    pass

@mlpux.Interactive()
@mlpux.Demo()
def square(x:float):
    """
    takes a floating point input, returns the square of that input
    """
    return x*x

@mlpux.Interactive()
@mlpux.Demo()
def no_args():
    """
    A functiont that returns some kind of string
    """
    return_string = "whoop-de doo!"
    return return_string

@mlpux.Interactive()
@mlpux.Demo()
def str_args(mystr:str, myint:int):
    """
    A function which puts an int and a string into a string
    """
    return "Hi there {0}, you earned {1} schmeckles".format(mystr, myint)

@mlpux.Interactive()
@mlpux.Demo()
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
   
@mlpux.Interactive()
@mlpux.Demo()
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

@mlpux.Interactive()
@mlpux.Demo()
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
    

@mlpux.Interactive()
@mlpux.Demo()
def arbitrary_func(*args, **kwargs):
    """ 
    A function that takes an arbitrary list of named and unnamed arguments

    The author should probably document somewhere what to use

    Note that order of args and kwargs matters, therefore, order should be maintained no matter what.
    """
    return_string = "number of args: {0}, number of kwargs: {1}".format(len(args),len(kwargs))
    return return_string

@mlpux.Interactive()
@mlpux.Demo()
def args_only(*args):
    """
    A function which consists only of positional arguments, with no keywords.

    Call with any number of parameters - returns a list of those parameters back.abs
    """
    ret_val = {i:v for i,v in enumerate(args)}
    if len(ret_val.keys()) == 0:
        ret_val = {'status':'success'}
    return ret_val;

@mlpux.Interactive()
@mlpux.Demo()
def kwargs_only(**kwargs):
    """
    A function that only takes keyword arguments, and returns them.
    """
    ret_val = {k:v for k,v in kwargs.items()}
    if len(ret_val.keys()) == 0:
        ret_val = {'status':'success'}
    return ret_val


@mlpux.Interactive()
@mlpux.Demo()
def generate_gps_list(num=2,lat_var=90./10000., lon_var=180./10000.):
    """
    Generate gaussian distribution of GPS coordinates around a central
    point. If no central point is supplied, 
    
    param center: tuple (lat,long)
    param lat_var: variance of points generated in lattitude
    param long_va: varience of points generated in longitude
    """
    sign = np.array([-1,1])
    
    center = (random.uniform(-90.,90.), random.uniform(-180.,180.))
    list_of_list_pairs = []
    list_of_tuples = []
    lat_list = []
    lon_list = []
    for i in range(num):
        lat = np.random.normal(loc=center[0], scale=lat_var**(0.5))
        lon = np.random.normal(loc=center[1], scale=lon_var**(0.5))
        list_of_list_pairs.append([lat,lon])
        list_of_tuples.append((lat,lon))
        lat_list.append(lat)
        lon_list.append(lon)
    return list_of_tuples
