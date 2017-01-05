import inspect
import threading
import itertools
from functools import wraps
from collections import OrderedDict
import json
import pickle
import http.client
import time
import uuid
import flask
import socket
import ast
import requests

from formencode.variabledecode import variable_decode
from formencode.variabledecode import variable_encode

import discovery 

# GLOBALS #####################################################################

_DEMO_SERVER_ADDRESS = False
def set_ip(ip):
    """
    Code that should run once there is a connection to the server needs to run
    here.

    TODO a bit later
    """
    global _DEMO_SERVER_ADDRESS
    _DEMO_SERVER_ADDRESS = ip

discovery.get_ip(service_name="demo server backend",service_found = set_ip)

_MLPUX_IP_ADDRESS = '0.0.0.0'
_UUID = str(uuid.uuid4())

_functions = {}

app = flask.Flask(__name__)
_kill_server = threading.Event()
_app_thread = None
_kill_server.clear()

_MLPUX_PORT = 52758
#_MLPUX_PORT = discovery.select_unused_port()

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

def start_server(ip, port, discovery_name=None):
    global _app_thread
    if discovery_name is None:
        discovery_name = str(port)
    discovery.discoverable(service_name="mlpux_module_{}".format(discovery_name))
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
            print(r.text)
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


@app.route('/execute/<string:func_name>', methods=['GET'])
def execute_function(func_name):
    """
    For now, the function name is used to select the function and the arguments are
    POSTed in the body of the request.
    """
    global _functions

    print("GOT REQUEST: ",flask.request.args)
    print("DECODED:",variable_decode(flask.request.args))
    print("TRYING TO EXECUTE:",func_name)

    callback = None
    if func_name not in _functions:
        msg = "COULDN'T FIND FUNCTION {} in {}".format(func_name,_functions.keys())
        print(msg)
        return flask.jsonify({'error':msg})
    else:
        callback = _functions[func_name]['func']

    # Dictionary of args
    func_args = variable_decode(flask.request.args) 
    # Convention: 
    # kwargs as usual for GET, but *args as:
    # /base/path?args=[thing1, thing2...]
    # Holy python order: (*args, *kwargs, an_arg, another_arg)
    args = []
    kwargs = {}
    try:
        for k,v in func_args.items():
            if k == 'args':
                try:
                    args += ast.literal_eval(v)
                except:
                    msg = {"error":"could not evaluate {} as an *args array.".format(v)}
                    return flask.jsonify(msg)
            else:
                kwargs[k] = ast.literal_eval(v)
    except:
        msg = {"error":"could not parse arguments!"}
        msg.update(func_args)
        flask.jsonify(msg)

    result = "function returned nothing"
    try:
        if len(args) > 0 and len(kwargs.keys()) > 0:
            result = callback(*args,**kwargs) 
        elif len(args) > 0 and len(kwargs.keys()) == 0:
            result = callback(*args) 
        elif len(args) == 0 and len(kwargs.keys()) > 0:
            print(kwargs)
            result = callback(**kwargs)
        elif len(args) == 0 and len(kwargs.keys()) == 0:
            result = callback()
    except:
        msg = {"error":"Problem executing function {} with arguments func args: {}".format(func_name,func_args)}
        return flask.jsonify(msg)
    return flask.jsonify({"msg":"success","result":result})

def generate_ui_args(parameters, **ui_kwargs):
    """
    Parse the information extracted from inspecting a function, along with the instructions
    given by the decoration. ui_kwargs are ignored for now.

    For now, we simply make a list of args. Annotations to be handled later.

    Here we should infer all the UI types. For now we just handle the basic
    case.
    """
    # parameters is a dict of 'name':Parameter objects
    param_data = []
    for k,v in parameters.items():
        # Check what kind the Parameter is.
        param_data.append({
                "PAR_UUID":uuid.uuid4(),
                "POSITIONAL_ONLY":0,        # Tricky
                "POSITIONAL_OR_KEYWORD":0,  # Standard python binding
                "VAR_POSITIONAL":0,         # True if *args-like
                "KEYWORD_ONLY":0,           # True for params following *args-like
                "VAR_KEYWORD":0,            # True if **kwargs-like
                "DEFAULT":0,                # True if param has default value
                "ANNOTATION":0,             # True if parameter is annotated
                "NAME":"",                  # Parameter Name
            }
        )
        param_data[-1]["POSITIONAL_ONLY"] = \
                v.kind is inspect.Parameter.POSITIONAL_ONLY 
        param_data[-1]["POSITIONAL_OR_KEYWORD"] = \
                v.kind is inspect.Parameter.POSITIONAL_OR_KEYWORD 
        param_data[-1]["VAR_POSITIONAL"] = \
                v.kind is inspect.Parameter.VAR_POSITIONAL
        param_data[-1]["KEYWORD_ONLY"] = \
                v.kind is inspect.Parameter.KEYWORD_ONLY
        param_data[-1]["VAR_KEYWORD"] = \
                v.kind is inspect.Parameter.VAR_KEYWORD
        param_data[-1]["DEFAULT"] = \
                v.default if v.default is not inspect.Parameter.empty else False
        param_data[-1]["ANNOTATION"] = \
                v.annotation if v.annotation is not inspect.Parameter.empty else False
        param_data[-1]["NAME"] = v.name
    return param_data 

def create_function_server(func, **ui_kwargs):
    """
    Use inspect to get the properties of the function
    """

    global _functions, _UUID, _MLPUX_PORT, _app_thread, _MLPUX_IP_ADDRESS
    
    print('PROCESSING FUNCTION:', func.__name__)
    
    # if you want names and values as a dictionary:
    args_spec = inspect.getfullargspec(func)
    members = dict(inspect.getmembers(func))
    annotations = members['__annotations__']
    module_file = str(members['__globals__']['__package__'])
    if module_file is None or len(module_file) < 1:
        module_file = str(_MLPUX_PORT)
    documentation = members['__doc__']
    parameters = inspect.signature(func).parameters
    parameters = generate_ui_args(parameters, **ui_kwargs)
    _functions[func.__name__] = { 'func':func }

    # bind ui elements (if not existing) to function arguments (TODO)
    _func_data = {
        'client_uuid':_UUID,
        'PORT':_MLPUX_PORT,
        # IP - supplied by server
        'function':{ # each time this is sent, only one key is 'unknown', we can obtain this server-side.
            'parameters':parameters,
            'documentation':documentation,
            'name':func.__name__,
            'signature':str(inspect.signature(func)),
            'ui_kwargs':ui_kwargs,
            'func_uuid':str(uuid.uuid4()),
        }
    }
    
    # Start Server Thread
    if _app_thread is None:
        print("Starting server thread on port ",_MLPUX_PORT)
        print("Service for file: {}".format(module_file))
        start_server(ip = _MLPUX_IP_ADDRESS, port = _MLPUX_PORT, discovery_name = module_file) 
    print("IS MLPUX SERVER THREAD RUNNING: ", _app_thread.isAlive())

    print("SIGNATURE:",_func_data['function']['signature'])
    print("TEST UP: ",_DEMO_SERVER_ADDRESS)

    _functions[func.__name__]['attributes'] = dict(_func_data)

    data = pickle.dumps(_func_data,-1)

    if not _DEMO_SERVER_ADDRESS:
        # Demo server was not found with the discovery service.
        print("DEMO SERVICE WAS NOT DISCOVERED, MLPUX SERVER IS RUNNING IN BACKEND MODE, {}:{}".format(_MLPUX_IP_ADDRESS,_MLPUX_PORT))
    else:
        # double check that server is still up, but don't bother if its not discoverable.
        try:
            r = requests.get('http://{}/test_up'.format(_DEMO_SERVER_ADDRESS))
        except ConnectionError as e:
            if _app_thread.isAlive():
                print("DEMO SERVER DIED, MLPUX SERVER IS RUNNING IN BACKEND MODE, {}:{}".format(_MLPUX_IP_ADDRESS,_MLPUX_PORT))
                return
            else:
                raise ValueError("ERROR MLPUX SERVER IS NOT RUNNING. DEMO SERVER IS NOT RUNNING.")

        # If we're here, the connection is okay
        print("SENDING FUNCTION")
        r = requests.post(url='http://{}/register_function'.format(_DEMO_SERVER_ADDRESS),data=data)
        print(r.text)

        ret_data = json.loads(r.text)
        print("SUCCESSFULLY REGISTERED FUNCTION TO SERVER!",ret_data)
    return 

def demo(*ui_args, **ui_kwargs):
    print('*'*80)
    print ('ui_args:'  , ui_args)
    print ('ui_kwargs:', ui_kwargs)

    def decorator(func):
        create_function_server(func, **ui_kwargs) # pass as key-word arguments
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    return decorator
