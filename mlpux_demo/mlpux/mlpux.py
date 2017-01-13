# Builtin/Installed
import inspect
import threading
import itertools
from functools import wraps
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

# Local
import discovery 

# GLOBALS #####################################################################


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

_functions = {}

app = flask.Flask(__name__)
_kill_server = threading.Event()
_app_thread = None
_kill_server.clear()

# _MLPUX_PORT = 35556
_MLPUX_PORT = discovery.select_unused_port()

# Rigel's meeting To-Dos
# 2. TODO:
# no decorator arguemnts , i.e.:
# @mlpux.demo
#
# not 
#
# @mlpux.demo()

# 3. TODO
# Check out global scoping
# 
# if we are given generic code, all functions are decorated 
# - use some trickery with globals scope
# - use case: someone submits a file, no decoration, can we walk thru the scope and then decorate things automatically

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
            print(r.text, file=sys.stderr)
        except:
            time.sleep(0.2)
        else:
            if int(r.text) == 200:
                done = True

@app.route('/test_up', methods=['GET'])
def test_up():
    return flask.make_response("200".encode(encoding="utf8"))

@app.route('/show_functions',methods=['GET'])
def show_functions():
    global _functions
    display_out = { name:str(function['attributes']['function']['parameters']) for name,function in _functions.items() }
    return flask.jsonify(display_out)


def generate_ui_args(parameters):
    """
    Parse the information extracted from inspecting a function, along with the instructions
    given by the decoration. 

    For now, we simply make a list of args. Annotations to be handled later.

    Here we should infer all the UI types. For now we just handle the basic
    case.

    All callable parameters must have default values.
    """
    # parameters is a dict of 'name':Parameter objects
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
                "input_type":'input',
                "default_value":None,
                "user_input":None,
                "annotation":None
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
                print("Skipping callable default parameter", file=sys.stderr)
                continue
        if param["DEFAULT"] is not False:
            ui_param['default_value'] = repr(v.default)
        if param['VAR_KEYWORD']:
            ui_param['type'] = 'keyword'
        if param['VAR_POSITIONAL']:
            ui_param['type'] = 'positional'
            found_positional == True
            if position != 0:
                raise ValueError("Someone wrote a really ambiguous function signature. You must place positional arguments first in your function signature. Think carefully about symantics and readability of your function. If you make me rewrite this module to accomodate your shitty python, I will end you. --Mike")
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
    for param in param_data:
        print(
            "PARAM: {:>10}, ".format(param["NAME"]),
            "POSITIONAL_OR_KEYWORD: {:>10}, ".format(param["POSITIONAL_OR_KEYWORD"]),
            "POSITIONAL_ONLY: {:>10}, ".format(param["POSITIONAL_ONLY"]),
            "VAR_POSITIONAL: {:>10}, ".format(param["VAR_POSITIONAL"]),
            "VAR_KEYWORD: {:>10}, ".format(param["VAR_KEYWORD"]), 
            "KEYWORD_ONLY: {:>10}".format(param["KEYWORD_ONLY"]),
            "ANNOTATION: {:>10}".format(param["ANNOTATION"]),
            "SUM: {:>10}".format(sum([int(v) for k,v in param.items() if isinstance(v,bool)])) # check mutual exclusivity
            )
    return ui_data

def create_function_server(func):
    """
    Use inspect to get the properties of the function
    """

    global _functions, _UUID, _MLPUX_PORT, _app_thread, _MLPUX_IP_ADDRESS, _DEMO_SERVER_IP

    func_name = func.__name__
    
    print('PROCESSING FUNCTION:', func_name, file=sys.stderr)
    print('LOCAL ADDRESS {}:{}'.format(_MLPUX_IP_ADDRESS,_MLPUX_PORT), file=sys.stderr)
    
    # if you want names and values as a dictionary:
    args_spec = inspect.getfullargspec(func)
    members = dict(inspect.getmembers(func))
    annotations = members['__annotations__']

    # Folder Scope
    try:
        module_folder = os.path.basename(members['__globals__']['__package__'])
    except AttributeError:
        module_folder = None

    # File Scope
    module_file = os.path.splitext(os.path.basename(os.path.normpath(members['__globals__']['__file__'])))[0]
    print(type(module_folder), file=sys.stderr)

    func_scope = ""
    if module_folder is None:
        func_scope = module_file
    else:
        func_scope = module_folder + "." + module_file
    func_key = func_scope + "." + func_name
    print('FUNCTION SCOPE',func_scope, file=sys.stderr)
    print('FUNCTION KEY:',func_key, file=sys.stderr)
    documentation = members['__doc__']
    parameters = inspect.signature(func).parameters
    try:
        parameters = generate_ui_args(parameters)
    except Exception as e:
        print("Problem with function: {}, Exception '{}'. Skipping".format(func_key,e), file=sys.stderr)
        return

    if func_key in _functions:
        raise ValueError("ERROR: You defined a function with a name collision with a pre-existing funciton. mlpux is first come-first-serve, therefore your function will not be registered. This is rare but possible in cases where your function lives in a module inside a directory which shares the same module and directory name with another previously defined function. This is a consequence of trying to keep things human-readable for the web API. Here is an example of this type of collision: /some/path/to/module/module.py(contains 'func') and /other/path/to/module/module.py(contains'func'). Your function key is {} which already exists as a key in {}. Name your function something else, name your module something else, or name the directory your module lives in something else.".format(func_key,str(_functions.keys())))
    _functions[func_key] = { 'func':func }
    # bind ui elements (if not existing) to function arguments (TODO)
    _func_data = {
        'client_uuid':_UUID,
        'PORT':_MLPUX_PORT,
        # IP - supplied by server
        'function':{ # each time this is sent, only one key is 'unknown', we can obtain this server-side.
            'parameters':parameters,
            'documentation':documentation,
            'func_name':func_name,
            'signature':str(inspect.signature(func)),
            'func_uuid':func_key,
            'func_scope':func_scope,
            'func_key':func_key
        }
    }
    
    # Start Server Thread
    if _app_thread is None:
        print("Starting server thread on port ",_MLPUX_PORT, file=sys.stderr)
        print("Service for file: {}".format(module_file), file=sys.stderr)
        start_server(ip = _MLPUX_IP_ADDRESS, port = _MLPUX_PORT) 
    print("IS MLPUX SERVER THREAD RUNNING: ", _app_thread.isAlive(), file=sys.stderr)

    print("SIGNATURE:",_func_data['function']['signature'], file=sys.stderr)
    print("TEST UP: ",_DEMO_SERVER_IP, file=sys.stderr)

    _functions[func_key]['attributes'] = dict(_func_data)

    data = pickle.dumps(_func_data,-1)

    # Wait five seconds to find server.
    seconds = 0
    while not _DEMO_SERVER_IP:
        wait_interval = 0.25
        time.sleep(wait_interval)
        seconds += wait_interval
        if seconds > 5:
            # Use default for local running
            print("WAITED FOR {} SECONDS AND NO DISCOVERY. USING DEFAULT ADDRESS FOR DEMO SERVER: 0.0.0.0".format(seconds), file=sys.stderr)
            _DEMO_SERVER_IP = '0.0.0.0'
            break

    if not _DEMO_SERVER_IP:
        # Demo server was not found with the discovery service.
        print("DEMO SERVICE WAS NOT DISCOVERED, REQUESTS MUST BE SENT TO:  {}:{}".format(_MLPUX_IP_ADDRESS,_MLPUX_PORT), file=sys.stderr)
    else:
        # double check that server is still up, but don't bother if its not discoverable.
        try:
            # use port for development
            r = requests.get('http://{}:{}/test_up'.format(_DEMO_SERVER_IP,5002))
        except ConnectionError as e:
            if _app_thread.isAlive():
                print("DEMO SERVER DIED, MLPUX SERVER IS RUNNING IN BACKEND MODE. REEQUESTS MAY BE SENT TO: {}:{}".format(_MLPUX_IP_ADDRESS,_MLPUX_PORT), file=sys.stderr)
                return
            else:
                raise ValueError("ERROR MLPUX SERVER IS NOT RUNNING. DEMO SERVER IS NOT RUNNING.")

        # If we're here, the connection is okay
        print("SENDING FUNCTION", file=sys.stderr)
        # use port for non-privelaged development.
        r = requests.post(url='http://{}:{}/register_function'.format(_DEMO_SERVER_IP,5002),data=data)
        print(r.text, file=sys.stderr)

        ret_data = json.loads(r.text)
        print("SUCCESSFULLY REGISTERED FUNCTION TO SERVER!",ret_data, file=sys.stderr)
    return 

# wrappers 
# Goal is to pass wrapper arguments cascading down to the core demo function.
# Usage would be akin to:
#
# @mlpux.ui_slider(arg_label=var3, min=10, max=20, step=0.5)
# @mlpux.demo
# def func(var1, var2, var3):
#   ...
# Desired effect: arguement value is set by manipulation of a slider element.

# def demo(*ui_args, **ui_kwargs): # maybe do not support arguments to decorator
def plot2D(func, **kwargs):
    """
    kwargs to be passed to matplotlib plot command
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper

def plot3D(func, **kwargs):
    """
    kwargs to be passed to matplotlib plot command
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper

def demo(func, **ui_kwargs):
    """
    inspects a function, func and spins off a server which can be used to 
    remotely call the function via a web interface or REST API.

    API generated for function is called through base server at _DEMO_SERVER_IP.

    ui_kwargs will  be generated and passed in by functions which decorate 
    the demo decorator.
    """
    print('*'*80, file=sys.stderr)
    # print ('ui_args:'  , ui_args)
    # print ('ui_kwargs:', ui_kwargs)

    create_function_server(func) # pass as key-word arguments
    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper

@app.route('/execute', methods=['POST','GET'])
def execute_function():
    """
    For now, the function name is used to select the function and the arguments are
    POSTed in the body of the request.

    Note that argument parsing will be handled by server front end, and must be
    posted here as a pickled python object.
    """

    global _functions

    
    request_content = flask.request.data
    print("MLPUX SERVER RECEIVED: {}".format(repr(request_content)), file=sys.stderr)
    arguments = pickle.loads(request_content)
    print("DECODED: {}".format(repr(arguments)), file=sys.stderr)
    try:
        func_key = arguments['func_key']
        args = arguments['args']
        kwargs = arguments['kwargs']
    except:
        msg = {'error':"Data posted to MLPUX server was not formatted correctly. Expecting {'func_key':func_key, 'args':args, 'kwargs':kwargs}, but got {}".format(repr(arguments))}
        print(msg, file=sys.stderr)
        return flask.jsonify(msg)

    callback = None
    if func_key not in _functions:
        msg = {'error' "COULDN'T FIND FUNCTION {} (KEY: {}) in {}".format(func_name, func_key, _functions.keys())}
        print(msg, file=sys.stderr)
        return flask.jsonify(msg)
    else:
        callback = _functions[func_key]['func']

    result = "function returned nothing"
    if len(args) > 0 and len(kwargs.keys()) > 0:
        try:
            result = callback(*args,**kwargs) 
        except Exception as e:
            msg = {"error":"Execution endpoint exception: {}. Tried {} with args {}. Request endpoint type: endpoint/func?args=[x,y,z...]&A=a&B=b&... (positional and keyword)".format(e,func_key,func_args)}
            print(msg,file=sys.stderr)
            return flask.jsonify(msg)
    elif len(args) > 0 and len(kwargs.keys()) == 0:
        try:    
            result = callback(*args) 
        except Exception as e:
            msg = {"error":"Execution endpoint exception: {}. Tried {} with args {}. Request endpoint type: endpoint/func?args=[x,y,z...] (positional only)".format(e, func_key,func_args)}
            print(msg,file=sys.stderr)
            return flask.jsonify(msg)
    elif len(args) == 0 and len(kwargs.keys()) > 0:
        try:
            result = callback(**kwargs)
        except Exception as e:
            msg = {"error":"Execution endpoint exception: {}. Tried {} with args {}. Request endpoint type: endpoint/func?X=x&Y=y&Z=z... (keyword only) ".format(e, func_key,func_args)}
            print(msg,file=sys.stderr)
            return flask.jsonify(msg)
    elif len(args) == 0 and len(kwargs.keys()) == 0:
        try:
            result = callback()
        except Exception as e:
            msg = {"error":"Execution endpoint exception: {}. Tried {}. Request endpoint type: endpoint/func (no arguments)".format(e,func_key)}
            print(msg,file=sys.stderr)
            return flask.jsonify(msg)

    # TODO: do some inference on what to do with result here.

    return flask.jsonify({"msg":"success","result":result})
