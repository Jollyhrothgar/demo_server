# Builtin/Installed
import inspect
import threading
import itertools
import functools
from collections import OrderedDict
import json
import pickle
import time
import uuid
import flask
import socket
import ast
import requests
import os
import sys
from formencode.variabledecode import variable_decode
from formencode.variabledecode import variable_encode

import pandas as pd
import numpy as np
from math import fabs

import random
# Local
import discovery 

# GLOBALS #####################################################################

_DEMO_SERVER_PORT = 5002
_DEMO_SERVER_IP = False
def set_ip(ip):
    """
    Code that should run once there is a connection to the server needs to run
    here.

    TODO a bit later
    """
    global _DEMO_SERVER_IP
    _DEMO_SERVER_IP = ip
discovery.get_ip(service_name="demo server",service_found = set_ip)

_MLPUX_IP_ADDRESS = '0.0.0.0' # always run locally
_UUID = str(uuid.uuid4())

_function_registry = {}
### Structure of _function_registry ###
#_function_registry = {
#    < func_key: lookup key for function, defined in generate_func_identifiers() >:{
#        'callback':func,
#        'info':{
#            'display':None,
#            'parameters':[
#                {
#                        "name":None,
#                        "type":None,
#                        "position":position,
#                        "default_value":None,
#                        "annotation":None,
#                        "param_gui":None
#                },
#                {},
#                ...
#            ] ,
#            'documentation':< python function doc string > ,
#            'func_name':< name of python function >,
#            'signature':< the stringified signature of a function >,
#            'func_uuid':< semi-unique indentifier for functions > 
#            'func_scope':< in order of prefernece: directory of demo or the filename containing the decorated function >
#            'func_key':< semi-unique function string identifier, equal to func_scope + '.' + func_name > 
#        }
#    }
#}
####
app = flask.Flask(__name__)
_kill_server = threading.Event()
_app_thread = None
_kill_server.clear()
_MLPUX_PORT = discovery.select_unused_port()

# 4. TODO 
# output:
# - tabulate library might be good direction to go after basic output is set up

# 5. TODO
# decorated decorators
# - instead of speccing out complex arguemnts to mlpux.demo, perhaps use
#   meta decorators which modify the behavior of mlpux.demo itself.
# It seems that this whole body is unique in scope to each decorator.

def start_server(ip, port):
    global _app_thread
    _app_thread = threading.Thread(
        target=app.run,
        kwargs = {
            'host':ip,
            'port':port,
            'debug':False,
            'threaded':True,
        }
    )
    _app_thread.start()

    # wait for server to come up
    done = False
    while not done:
        try:
            r = requests.get('http://{}:{}/test_up'.format(ip,port))
            #print(r.text, file=sys.stderr)
        except:
            time.sleep(0.2)
        else:
            if int(r.text) == 200:
                done = True

def update_param_gui(func_key, param_name, gui):
    """
        ui_param = {
                "name":None,
                "type":None,
                "position":position,
                "default_value":None,
                "annotation":None,
                "param_gui":None
        }
    """
    global _function_registry
    if func_key not in _function_registry:
        raise ValueError("{} not registered to _function_register")
    for i,param in enumerate(_function_registry[func_key]['info']['parameters']):
        print(i,param,file=sys.stderr)
        if param['name'] == param_name:
            _function_registry[func_key]['info']['parameters'][i]['param_gui'] = dict(gui)
            print("UPDATING",_function_registry[func_key]['info']['parameters'][i]['param_gui'], file=sys.stderr)
            return
    raise ValueError("No parameter updated. Did you enter the parameter's name correctly? Lookup: {}, given:{}".format(func_key, param_name))
    return

def generate_ui_args(func):
    """
    Parse the information extracted from inspecting a function, along with the
    instructions given by the decoration. 

    For now, we simply make a list of args. Annotations to be handled later.

    Here we should infer all the UI types. For now we just handle the basic
    case.

    All callable parameters must have default values.

    First pass, do nothing. This should be called exactly once per function.
    """
    parameters = inspect.signature(func).parameters
    param_data = []
    ui_data = []
    position = 0
    found_positional = True
    for k,v in parameters.items():
        # Check what kind the Parameter is.
        param = {
                "PAR_UUID":str(uuid.uuid4()),   # another uuid
                "POSITIONAL_ONLY":False,        # ??
                # Mutually Exclusive Function Parameter Attributes
                "POSITIONAL_OR_KEYWORD":False,  # Standard python for a function argument.
                "VAR_POSITIONAL":False,         # True if *args-like
                "KEYWORD_ONLY":False,           # True for args following signature like: (*, arg1, arg2...) - only named arguments accepted.
                "VAR_KEYWORD":False,            # True if **kwargs-like
                "DEFAULT":False,                # True if param has default value
                "ANNOTATION":False,             # True if parameter is annotated
                "NAME":"",                      # Parameter Name
            }
        
        ui_param = {
                "name":None,
                "type":None,
                "position":position,
                "default_value":None,
                "annotation":None,
                "param_gui":None
        }
        
        param["POSITIONAL_ONLY"] = \
                v.kind is inspect.Parameter.POSITIONAL_ONLY 
        param["POSITIONAL_OR_KEYWORD"] = \
                v.kind is inspect.Parameter.POSITIONAL_OR_KEYWORD 
        param["VAR_POSITIONAL"] = \
                v.kind is inspect.Parameter.VAR_POSITIONAL
        param["KEYWORD_ONLY"] = \
                v.kind is inspect.Parameter.KEYWORD_ONLY
        param["VAR_KEYWORD"] = \
                v.kind is inspect.Parameter.VAR_KEYWORD
        param["DEFAULT"] = \
                v.default if v.default is not inspect.Parameter.empty else False
        param["ANNOTATION"] = \
                str(repr(v.annotation)) if v.annotation is not inspect.Parameter.empty else False
        param["NAME"] = v.name

        # Skip callable parameters that are default.
        if param["DEFAULT"] and hasattr(v.default,'__call__'):
                continue
        if param["DEFAULT"] is not False:
            ui_param['default_value'] = repr(v.default)
        if param['VAR_KEYWORD']:
            ui_param['type'] = 'keyword'
        if param['VAR_POSITIONAL']:
            ui_param['type'] = 'positional'
            found_positional == True
            if position != 0:
                raise ValueError("""Someone wrote a really ambiguous function
                        signature. You must place positional arguments first in
                        your function signature. Think carefully about
                        symantics and readability of your function. If you make
                        me rewrite this module to accomodate your shitty
                        python, I will end you. --Mike""")
        if param['POSITIONAL_OR_KEYWORD'] or param['KEYWORD_ONLY']:
            ui_param['type'] = 'standard'
        if param["ANNOTATION"] is not False:
            # sanitize for html
            try:
                ui_param['annotation'] = str(repr(v.annotation)).replace('>','')
                ui_param['annotation'] = ui_param['annotation'].replace('<','')
            except: 
                ui_param['annotation'] = "FIX ANNOTATION: mlpux.generate_ui_args"

        ui_param['name'] = param["NAME"]
        param_data.append(dict(param))
        ui_data.append(dict(ui_param))
        position+=1

    # Now, we need to figure out the number of input fields
    # for param in param_data:
        #print(
            # "PARAM: {:>10}, ".format(param["NAME"]),
            # "POSITIONAL_OR_KEYWORD: {:>10}, ".format(param["POSITIONAL_OR_KEYWORD"]),
            # "POSITIONAL_ONLY: {:>10}, ".format(param["POSITIONAL_ONLY"]),
            # "VAR_POSITIONAL: {:>10}, ".format(param["VAR_POSITIONAL"]),
            # "VAR_KEYWORD: {:>10}, ".format(param["VAR_KEYWORD"]), 
            # "KEYWORD_ONLY: {:>10}".format(param["KEYWORD_ONLY"]),
            # "ANNOTATION: {:>10}".format(param["ANNOTATION"]),
            # "SUM: {:>10}".format(sum([int(v) for k,v in param.items() if isinstance(v,bool)])) # check mutual exclusivity
            # )
    return ui_data

def error_if_func_exists(func_key,registry):
    """
    Raise an error if a particular function has been parsed and registered, 
    but it should not yet exist.
    """
    error_msg = """ERROR: You defined a function with a name collision with a
    pre-existing funciton. mlpux is first come-first-serve, therefore your
    function will not be registered. This is rare but possible in cases where
    your function lives in a module inside a directory which shares the same
    module and directory name with another previously defined function. This is
    a consequence of trying to keep things human-readable for the web API. Here
    is an example of this type of collision:
    /some/path/to/module/module.py(contains function) and
    /other/path/to/module/module.py(contains function). Your function key is
    {0} which already exists as a key in {1}. Name your function something
    else, name your module something else, or name the directory your module
    lives in something
    else.""".format(func_key,str(_function_registry.keys()))

    if func_key in registry:
        raise ValueError(error_msg)
    return

def generate_func_identifiers(func):
    """
    Takes a function, generates a mostly-unique identifier from a funciton
    """
    func_name = func.__name__
    members = dict(inspect.getmembers(func))

    # Folder Scope
    try:
        module_folder = os.path.basename(members['__globals__']['__package__'])
    except AttributeError:
        module_folder = None

    # File Scope
    try:
        module_file = os.path.splitext(os.path.basename(os.path.normpath(members['__globals__']['__file__'])))[0]
    except Exception as e:
        print("Couldn't acceess __globals__ or __file__ attribute of function. Exception: {}".format(e), file=sys.stderr)
        print("Using UUIDs for func_key, func_scope")
        func_scope = str(uuid.uuid4())
        time.sleep(0.1)
        func_key = func_scope + "." + func_name
        return func_key, func_scope, func_name
    #print(type(module_folder), file=sys.stderr)
    
    func_scope = ""
    abs_file = inspect.getabsfile(func) 
    path_list = abs_file.split(os.sep)
    
    # Rigel wants func_scope to be the demo directory.
    try:
        func_scope = path_list[-2]
    except:
        if module_folder is None:
            func_scope = module_file
        else:
            func_scope = module_folder + "." + module_file

    if len(func_scope) > 1 and func_scope[0] == '.':
        func_scope = func_scope[1:]
    func_key = func_scope + "." + func_name
    return func_key, func_scope, func_name

def generate_function_entry(func):
    """ 
    extract information from function using inspect module.

    Returns:
    {
        'callback':func,
        'info':{
            'parameters':parameters,
            'documentation':documentation,
            'func_name':func_name,
            'signature':signature,
            'func_uuid':func_key, # was previously a uuid
            'func_scope':func_scope,
            'func_key':func_key
        }
    }

    """
    func_key, func_scope, func_name = generate_func_identifiers(func)
    members = dict(inspect.getmembers(func))
    documentation = members['__doc__']
    signature = str(inspect.signature(func))

    print('UPDATING INFORMATION FOR FUNCTION:', func_key, file=sys.stderr)
    print('FUNCTION SCOPE',func_scope, file=sys.stderr)
    print('FUNCTION KEY:',func_key, file=sys.stderr)

    try:
        parameters = generate_ui_args(func)
    except Exception as e:
        #print("Problem with function: {}, Exception '{}'. Skipping".format(func_key,e), file=sys.stderr)
        return

    parsed = {
                'callback':func,
                'info':{
                    'display':None,
                    'parameters':parameters,
                    'documentation':documentation,
                    'func_name':func_name,
                    'signature':signature,
                    'func_uuid':func_key, # was previously a uuid
                    'func_scope':func_scope,
                    'func_key':func_key
                }
            }
    return func_key, parsed

def wait_for_demo_server_discovery(wait_seconds=60):
    """
    Waits for discovery service to update the value of _DEMO_SERVER_IP.
    """
    global _DEMO_SERVER_IP
    seconds = 0.
    while not _DEMO_SERVER_IP:
        wait_interval = 0.25
        time.sleep(wait_interval)
        seconds += wait_interval
        if seconds > wait_seconds:
            # Use default for local running
            #print("WAITED FOR {} SECONDS AND NO DISCOVERY. USING DEFAULT ADDRESS FOR DEMO SERVER: 0.0.0.0".format(seconds), file=sys.stderr)
            _DEMO_SERVER_IP = '0.0.0.0'
            break
    return

def check_if_demo_server_alive(ip,port=_DEMO_SERVER_PORT):
    """
    Pings the demo server with a get request. ConnectionError causes ValueError
    """
    try:
        # use port for development
        r = requests.get('http://{}:{}/test_up'.format(_DEMO_SERVER_IP,port))
        return
    except ConnectionError as e:
        if _app_thread.isAlive():
            raise ValueError("DEMO SERVER DIED, MLPUX SERVER IS RUNNING IN BACKEND MODE. REEQUESTS MAY BE SENT TO: {}:{}".format(_MLPUX_IP_ADDRESS,_MLPUX_PORT), file=sys.stderr)
        else:
            raise ValueError("ERROR MLPUX SERVER IS NOT RUNNING. DEMO SERVER IS NOT RUNNING.")

def update_demo_server(func_key):
    """
    Update demo server with func_data corresponding to func_key. If mlpux server
    hasn't yet started, the thread is started.
    """
    global _function_registry, _UUID, _app_thread, _DEMO_SERVER_IP, _MLPUX_PORT

    #print('MLPUX LOCAL ADDRESS {}:{}'.format(_MLPUX_IP_ADDRESS,_MLPUX_PORT), file=sys.stderr)

    if _app_thread is None:
        #print("Starting server thread on port ",_MLPUX_PORT, file=sys.stderr)
        start_server(ip = _MLPUX_IP_ADDRESS, port = _MLPUX_PORT) 
    # else:
        #print("IS MLPUX SERVER THREAD RUNNING: ", _app_thread.isAlive(), file=sys.stderr)
    
    wait_for_demo_server_discovery(wait_seconds=60)
    if not _DEMO_SERVER_IP:
        # Demo server was not found with the discovery service.
        #print("DEMO SERVICE WAS NOT DISCOVERED, REQUESTS MUST BE SENT TO:  {}:{}".format(_MLPUX_IP_ADDRESS,_MLPUX_PORT), file=sys.stderr)
        raise ValueError("Server backend is unreachable {}:{}".format(_MLPUX_IP_ADDRESS,_MLPUX_PORT))
    else:
        # In case server went down since last time a function was registered.
        check_if_demo_server_alive(ip=_DEMO_SERVER_IP, port=_DEMO_SERVER_PORT)
        #print("SENDING FUNCTION", file=sys.stderr)

        # Update func_data with network information to call back
        payload = _function_registry[func_key]['info']
        payload['PORT'] = _MLPUX_PORT
        payload['client_uuid'] = _UUID
        data = pickle.dumps(payload,-1)

        r = requests.post(url='http://{}:{}/register_function'.format(_DEMO_SERVER_IP,_DEMO_SERVER_PORT),data=data)
        #print(r.text, file=sys.stderr)

        ret_data = json.loads(r.text)
        #print("SUCCESSFULLY REGISTERED FUNCTION TO SERVER!",ret_data, file=sys.stderr)
    return 

### DECORATORS ################################################################
"""
Building Your Own Decorators

Input Widget Base:
class Input:
    global _function_registry
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

        ### YOUR CODE HERE ###
        1) Define the necessary information the js front end needs t
 
    def __call__(self, *args, **kwargs):
        func = args[0]['func']
        func_key = args[0]['key']
        
        ### YOUR CODE HERE ###
        

        # Pass through for the funciton - this never changes.
        @functools.wraps(func)
        def wrapped(*inner_args, **inner_kwargs):
            return func(*inner_args, **inner_kwargs)
        return {'func':wrapped, 'key':func_key}


Output Widget Base:
# Output Widget
class Output
    global _function_registry
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
 
    def __call__(self, *args, **kwargs):
        func = args[0]['func']
        func_key = args[0]['key']
        
        ### YOUR CODE HERE### 
        
        # Pass through for the funciton - this never changes.
        @functools.wraps(func)
        def wrapped(*inner_args, **inner_kwargs):
            return func(*inner_args, **inner_kwargs)
        return {'func':wrapped, 'key':func_key}
"""


class Interactive:
    """
    Decorate functions with this (must be top-most decorator) in order to retain
    the ability to interactively call them in a module.
    """
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def __call__(self, *args, **kwargs):
        func = args[0]['func']

        @functools.wraps(func)
        def wrapped(*inner_args, **inner_kwargs):
            return func(*inner_args, **inner_kwargs)
        return wrapped

# Input Widget
class Slider:
    """
    Decorate above mlpux.Demo to enable a slider input widget for a parameter
    argument.
    """
    global _function_registry
    def __init__(self, arg, min_val, max_val, ndiv ):
        self.param = arg
        self.param_gui = {'slider':{ 'param':arg, 'min':min_val, 'max':max_val, 'ndiv':ndiv }}
 
    def __call__(self, *args, **kwargs):
        func = args[0]['func']
        func_key = args[0]['key']
        
        if func_key in _function_registry:
            # update parameter gui
            update_param_gui(func_key, self.param, self.param_gui)
            print(self.__class__.__name__, func_key, self.param_gui, file=sys.stderr)
            update_demo_server(func_key)

        else:
            raise ValueError("Function must be decorated with Demo first, then others")
        
        # Pass through for the funciton - this never changes.
        @functools.wraps(func)
        def wrapped(*inner_args, **inner_kwargs):
            return func(*inner_args, **inner_kwargs)
        return {'func':wrapped, 'key':func_key}

# Output Widget
class Plot2D:
    """
    Decorate a function to try to plot its output on a 2D
    style = scatter
    style = line
    style = bar
    """
    global _function_registry
    def __init__(self, title="", style='scatter' ):
        self.display = { 
                'plot2d':{
                    'style':style, 
                    'title':title,
                    }
                }

    def __call__(self, *args, **kwargs):
        func = args[0]['func']
        func_key = args[0]['key']

        if func_key in _function_registry:
            _function_registry[func_key]['info']['display'] = self.display
            update_demo_server(func_key)
            print(self.__class__.__name__, func_key, self.display, file=sys.stderr)
        else:
            raise ValueError("Function must be decorated by mlpux.Demo before decorating with mlpux.Plot2D")
        
        # Pass through for the funciton - this never changes.
        @functools.wraps(func)
        def wrapped(*inner_args, **inner_kwargs):
            return func(*inner_args, **inner_kwargs)
        return {'func':wrapped, 'key':func_key}

# Base Widget
class Demo:
    global _function_registry
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
 
    def __call__(self, func):
        func_key, func_data = generate_function_entry(func)
        if func_key not in _function_registry:
            _function_registry[func_key] = func_data
        print("Demo for callback:", _function_registry[func_key]['callback'], "func_key", func_key, file=sys.stderr)
        update_demo_server(func_key)

        # Passthrough
        @functools.wraps(func)
        def wrapped(*inner_args, **inner_kwargs):
            return func(*inner_args, **inner_kwargs)
        return {"func":wrapped,"key":func_key}

# FLASK ROUTES ################################################################ 
@app.route('/test_up', methods=['GET'])
def test_up():
    return flask.make_response("200".encode(encoding="utf8"))

@app.route('/show_functions',methods=['GET'])
def show_functions():
    global _function_registry
    display_out = { _function_registry.keys() }
    return flask.jsonify(display_out)

@app.route('/execute', methods=['POST'])
def execute_function():
    """
    For now, the function name is used to select the function and the arguments
    are POSTed in the body of the request.

    Note that argument parsing will be handled by server front end, and must be
    posted here as a pickled python object.
    """

    global _function_registry
    
    request_content = flask.request.data
    #print("MLPUX SERVER RECEIVED: {}".format(repr(request_content)), file=sys.stderr)
    arguments = pickle.loads(request_content)
    #print("DECODED: {}".format(repr(arguments)), file=sys.stderr)
    try:
        func_key = arguments['func_key']
        args = arguments['args']
        kwargs = arguments['kwargs']
    except:
        msg = {'error':"Data posted to MLPUX server was not formatted correctly. Expecting {'func_key':func_key, 'args':args, 'kwargs':kwargs}, but got {}".format(repr(arguments))}
        print(msg, file=sys.stderr)
        return flask.jsonify(msg)

    callback = None
    if func_key not in _function_registry:
        msg = {'error' "COULDN'T FIND FUNCTION {} (KEY: {}) in {}".format(func_name, func_key, _function_registry.keys())}
        print(msg, file=sys.stderr)
        return flask.jsonify(msg)
    else:
        callback = _function_registry[func_key]['callback']

    result = "function returned nothing"
    if len(args) > 0 and len(kwargs.keys()) > 0:
        try:
            result = callback(*args,**kwargs) 
        except Exception as e:
            msg = {"error":"Execution endpoint exception: {}. Tried {} with args {}. Request endpoint type: endpoint/func?args=[x,y,z...]&A=a&B=b&... (positional and keyword)".format(e,func_key,"args: "+str(repr(args))+" kwargs: "+str(repr(kwargs)))}
            print(msg,file=sys.stderr)
            return flask.jsonify(msg)
    elif len(args) > 0 and len(kwargs.keys()) == 0:
        try:    
            result = callback(*args) 
        except Exception as e:
            msg = {"error":"Execution endpoint exception: {}. Tried {} with args {}. Request endpoint type: endpoint/func?args=[x,y,z...] (positional only)".format(e, func_key,"args: "+str(repr(args))+" kwargs: "+str(repr(kwargs)))}
            print(msg,file=sys.stderr)
            return flask.jsonify(msg)
    elif len(args) == 0 and len(kwargs.keys()) > 0:
        try:
            result = callback(**kwargs)
        except Exception as e:
            msg = {"error":"Execution endpoint exception: {}. Tried {} with args {}. Request endpoint type: endpoint/func?X=x&Y=y&Z=z... (keyword only) ".format(e, func_key,"args: "+str(repr(args))+" kwargs: "+str(repr(kwargs)))}
            print(msg,file=sys.stderr)
            return flask.jsonify(msg)
    elif len(args) == 0 and len(kwargs.keys()) == 0:
        try:
            result = callback()
        except Exception as e:
            msg = {"error":"Execution endpoint exception: {}. Tried {}. Request endpoint type: endpoint/func (no arguments)".format(e,func_key)}
            print(msg,file=sys.stderr)
            return flask.jsonify(msg)

    out = process_output(result, func_key)
    return flask.jsonify(out)

def plotify(data, func_key):
    """
    Attempts to split data into two arrays which can be plotted.
    """

    out = {
        'display':'plot',
        'x':None,
        'y':None,
        'z':None,
        'msg':'success'
    }
    if not hasattr(data,'__iter__'):
        raise ValueError("Plottable data must be iterable. Exception: {}".format(e))

    # Check data shape for instance like data = x:list, y:list, z:list
    data_shape = np.shape(np.array(data))
    if data_shape[0] in [1,2,3]:
        print(data_shape)
        if len(data_shape) != 1:
            lengths = [len(item) for item in data]
            for length in lengths :
                if length != lengths[0]:
                    raise ValueError("Data x, y, and z values must have same length (lengths: {}), data:{}".format(lengths, repr(data)))
        if len(data_shape) == 1:
            x = np.array(data)   
            if not np.issubdtype(x.dtype, np.number):
                raise ValueError('Data set is not numeric, and cannot be plotted, data: {}'.repr(data))
            y = np.arange(0,x.size)
            out['x'] = x.tolist()
            out['y'] = y.tolist()
            return out
        else:
            x = np.array(data[0])
            if not np.issubdtype(x.dtype, np.number):
                raise ValueError('Data set is not numeric, and cannot be plotted, data: {}'.repr(data))
            y = np.array(data[1])
            if not np.issubdtype(x.dtype, np.number):
                raise ValueError('Data set is not numeric, and cannot be plotted, data: {}'.repr(data))
            out['x'] = x.tolist()
            out['y'] = y.tolist()
            return out
            # TODO special case for z: could be RGB, could be a point, etc.
    return out


def tabify(data, func_key):
    """
    Attempts to display data in a nicely formatted pandas dataframe
    """ 
    out = {
        'display':'table',
        'msg':'success',
        'table_soup':None
    }
    try:
        out['table_soup'] = pd.DataFrame(data).to_html()
        return out
    except Exception as e:
        raise ValueError("data can't be displayed as table. Data: {}, exception: {}".format(repr(data), e))
    try:
        out['table_soup'] = pd.DataFrame({0:item for item in data }).to_html()
        return out
    except Exception as e:
        raise ValueError("data can't be displayed as table. Data: {}, exception: {}".format(repr(data), e))

    try:
        out['table_soup'] = pd.DataFrame({ i:{k:data[k]} for i,k in enumerate(data.keys())}).to_html()
        return out
    except Exception as e:
        raise ValueError("data can't be displayed as table. Data: {}, exception: {}".format(repr(data), e))

    return out

def mapify(data, func_key):
    """
    Returns a list of GPS coordinates and central area

    Calculates center as average, as points are expected to be closely clustered.
    """
    output = {
        'msg':'success',
        'center':None,
        'points':[],
        'display':'map',
    }

    lat_sum = 0.
    lon_sum = 0.
    num = 0.

    for pair in data:
        try:
            if not isinstance(pair, str) and len(pair) > 2:
                raise ValueError("Mapping can't understand format of data. Exception: {}".format(repr(pair)))
            output['points'].append({'lat':pair[0], 'lng':pair[1]})
            lat_sum += pair[0]
            lon_sum += pair[1]
        except Exception as e:
            try:
                lat_lng = pair.split(',')
                lat_lng[0] = float(lat_lng[0])
                lat_lng[1] = float(lat_lng[1])
                output['points'].append({'lat':lat_lng[0], 'lng':lat_lng[1]}) 
                lat_sum += lat_lng[0]
                lon_sum += lat_lng[1]
            except Exception as f:
                raise ValueError("Data encountered isn't subscriptable into lat-lng pair: {}. Exception {}, and {}".format(repr(pair), e, f))
            
        num += 1.
    
    output['center'] = {'lat':(lat_sum/num), 'lng':(lon_sum/num)}
    print("Successfuly parsed map-like data", file=sys.stderr)
    return output

def process_output(data, func_key):
    """
    data guaranteed to be successfully resultant from a funciton execution.
    Here, we transform the data to something that can be shown on the front-end.
    """

    out = {'msg':'success', 'display':'plain', 'result':data}

    print("Testing for map-like-data", file=sys.stderr)
    try:
        out = mapify(data, func_key)
        return out
    except Exception as e:
        print("Data was not mappable {}, Exception: {}".format(data,e),file=sys.stderr)

    print("Testing for plot-like data", file=sys.stderr)
    try:
        out = plotify(data, func_key)
        return out
    except Exception as e:
        print("Data was not plottable {}, Exception: {}".format(data,e, file=sys.stderr))

    print("checking if data can be drawn on a table", file=sys.stderr)
    try:
        out = tabify(data, func_key)
        return out 
    except Exception as e:
        print("Data was not able to be displated in a Pandas DataFrame, data {}, Exception {}".format(data, e, file=sys.stderr))
    
    return out
