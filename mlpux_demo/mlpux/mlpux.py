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

from formencode.variabledecode import variable_decode
from formencode.variabledecode import variable_encode

import discovery 

# GLOBALS
try:
    _DEMO_SERVER_ADDRESS = discovery.get_ip("demo server backend")
except:
    _DEMO_SERVER_ADDRESS = '127.0.0.1'
# _DEMO_SERVER_ADDRESS = '127.0.0.1'

_IP_ADDRESS = '0.0.0.0'
# _DEMO_SERVER_ADDRESS = '127.0.0.1' # maybe use discovery service?
_UUID = str(uuid.uuid4())

_functions = {}

app = flask.Flask(__name__)
_kill_server = threading.Event()
_app_thread = None
_kill_server.clear()

# Rigel's meeting To-Dos

# 1. TODO:
# Need discovery service for the server
# - tough for project network
# - can be done

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

_PORT = 52758 #PickUnusedPort() # development
#_PORT = discovery.select_unused_port()

# Flask App
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
    # FIXME needs to be handled with a handshake
    # - send a message, wait, then try again until success
    time.sleep(0.5)

# TODO: does server persist? Is the server process orphaned? Why can't we access this part?
# We probably need a main.py that imports the module, runs, and waits.
@app.route('/test_up', methods=['GET'])
def get_functions():
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
    #   call signature: call('this','is','the order') 
    #   unnamed arguments - i.e. *args
    #   then: {'0':'this','1':'is','2':'the order'} args are sorted into a list
    #
    #   kwargs: order doesn't matter because there are keywords. 
    # Try to execute function, catch the exception if any.
    # 
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

# TODO: more robust
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
                "POSITIONAL_ONLY":0,
                "POSITIONAL_OR_KEYWORD":0,
                "VAR_POSITIONAL":0,
                "KEYWORD_ONLY":0,
                "VAR_KEYWORD":0,
                "DEFAULT":0,
                "ANNOTATION":0,
                "NAME":"",
            }
        )
        # can be tricky
        param_data[-1]["POSITIONAL_ONLY"] = \
                v.kind is inspect.Parameter.POSITIONAL_ONLY 

        # standard binding behavior for functions
        param_data[-1]["POSITIONAL_OR_KEYWORD"] = \
                v.kind is inspect.Parameter.POSITIONAL_OR_KEYWORD 

        # true for things like *args
        param_data[-1]["VAR_POSITIONAL"] = \
                v.kind is inspect.Parameter.VAR_POSITIONAL

        # true for params after *args in func def
        param_data[-1]["KEYWORD_ONLY"] = \
                v.kind is inspect.Parameter.KEYWORD_ONLY

        # True for **kwargs like arguments
        param_data[-1]["VAR_KEYWORD"] = \
                v.kind is inspect.Parameter.VAR_KEYWORD

        # True if parameter is a default argument
        param_data[-1]["DEFAULT"] = \
                v.default if v.default is not inspect.Parameter.empty else False

        # True if parameter is annotated
        param_data[-1]["ANNOTATION"] = \
                v.annotation if v.annotation is not inspect.Parameter.empty else False

        # The name of the parameter
        param_data[-1]["NAME"] = v.name

    # TODO? Now some logic can be done with function stuff.
    return param_data 

def create_function_server(func, **ui_kwargs):
    """
    Use inspect to get the properties of the function
    """

    global _functions, _UUID, _PORT, _app_thread, _IP_ADDRESS
    
    # Start Server Thread
    if _app_thread is None:
        print("Starting server thread on port ",_PORT)
        start_server(_IP_ADDRESS, _PORT) 

    print("IS MLPUX SERVER THREAD RUNNING: ", _app_thread.isAlive())

    print('PROCESSING FUNCTION:', func.__name__)
    # if you want names and values as a dictionary:
    args_spec = inspect.getfullargspec(func)
    members = dict(inspect.getmembers(func))
    annotations = members['__annotations__']
    documentation = members['__doc__']
    parameters = inspect.signature(func).parameters
    parameters = generate_ui_args(parameters, **ui_kwargs)

    _functions[func.__name__] = { 'func':func }

    # bind ui elements (if not existing) to function arguments (TODO)
    _func_data = {
        'client_uuid':_UUID,
        'PORT':_PORT,
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
    print("SIGNATURE:",_func_data['function']['signature'])

    _functions[func.__name__]['attributes'] = dict(_func_data)

    data = pickle.dumps(_func_data,-1)
    print("SENDING FUNCTION")

    # FIXME replace with discovery service
    try:
        h = http.client.HTTPConnection('0.0.0.0', 80) 
        test = h.request("HEAD","/")
        test_resp = h.getresponse()
    except ConnectionRefusedError as e:
        if _app_thread.isAlive():
            print("NO RESPONSE FROM DEMO SERVER, MLPUX SERVER IS RUNNING IN BACKEND MODE, {}:{}".format(_IP_ADDRESS,_PORT))
            return
        else:
            raise ValueError("MLPUX SERVER IS NOT RUNNING. DEMO SERVER IS NOT RUNNING.")
        
    # If we're here, the connection is okay
    h.request('POST', '/register_function', data)
    response = h.getresponse()
    print(response.status)

    ret_data = json.loads(response.read().decode('utf8'))
    print("SUCCESSFULLY REGISTERED FUNCTION TO SERVER!")
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
