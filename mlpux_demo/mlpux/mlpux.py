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

_function_registry = {}
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
            print(r.text, file=sys.stderr)
        except:
            time.sleep(0.2)
        else:
            if int(r.text) == 200:
                done = True

def generate_ui_args(func):
    """
    Parse the information extracted from inspecting a function, along with the
    instructions given by the decoration. 

    For now, we simply make a list of args. Annotations to be handled later.

    Here we should infer all the UI types. For now we just handle the basic
    case.

    All callable parameters must have default values.
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
                "input_type":'input',
                "default_value":None,
                "user_input":None,
                "annotation":None,
                "ui_type":None # to be filled when needed
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
    module_file = os.path.splitext(os.path.basename(os.path.normpath(members['__globals__']['__file__'])))[0]
    print(type(module_folder), file=sys.stderr)
    
    func_scope = ""
    if module_folder is None:
        func_scope = module_file
    else:
        func_scope = module_folder + "." + module_file
    func_key = func_scope + "." + func_name
    return func_key, func_scope, func_name

def parse_function(func):
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

    print('UPDATING INFORMATION FOR FUNCTION:', func_name, file=sys.stderr)
    print('FUNCTION SCOPE',func_scope, file=sys.stderr)
    print('FUNCTION KEY:',func_key, file=sys.stderr)

    try:
        parameters = generate_ui_args(func)
    except Exception as e:
        print("Problem with function: {}, Exception '{}'. Skipping".format(func_key,e), file=sys.stderr)
        return

    parsed = {
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
    return func_key, parsed

def wait_for_demo_server_discovery(seconds=5):
    """
    Waits for discovery service to update the value of _DEMO_SERVER_IP.
    """
    global _DEMO_SERVER_IP
    while not _DEMO_SERVER_IP:
        wait_interval = 0.25
        time.sleep(wait_interval)
        seconds += wait_interval
        if seconds > 5:
            # Use default for local running
            print("WAITED FOR {} SECONDS AND NO DISCOVERY. USING DEFAULT ADDRESS FOR DEMO SERVER: 0.0.0.0".format(seconds), file=sys.stderr)
            _DEMO_SERVER_IP = '0.0.0.0'
            break
    return

def check_if_demo_server_alive(ip,port=80):
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

    print('MLPUX LOCAL ADDRESS {}:{}'.format(_MLPUX_IP_ADDRESS,_MLPUX_PORT), file=sys.stderr)

    if _app_thread is None:
        print("Starting server thread on port ",_MLPUX_PORT, file=sys.stderr)
        start_server(ip = _MLPUX_IP_ADDRESS, port = _MLPUX_PORT) 
    else:
        print("IS MLPUX SERVER THREAD RUNNING: ", _app_thread.isAlive(), file=sys.stderr)
    
    wait_for_demo_server_discovery(seconds=5)
    if not _DEMO_SERVER_IP:
        # Demo server was not found with the discovery service.
        print("DEMO SERVICE WAS NOT DISCOVERED, REQUESTS MUST BE SENT TO:  {}:{}".format(_MLPUX_IP_ADDRESS,_MLPUX_PORT), file=sys.stderr)
        raise ValueError("Server backend is unreachable {}:{}".format(_MLPUX_IP_ADDRESS,_MLPUX_PORT))
    else:
        # In case server went down since last time a function was registered.
        check_if_demo_server_alive(ip=_DEMO_SERVER_IP, port=5002)
        print("SENDING FUNCTION", file=sys.stderr)

        # Update func_data with network information to call back
        payload = _function_registry[func_key]['info']
        payload['PORT'] = _MLPUX_PORT
        payload['client_uuid'] = _UUID
        data = pickle.dumps(payload,-1)

        r = requests.post(url='http://{}:{}/register_function'.format(_DEMO_SERVER_IP,5002),data=data)
        print(r.text, file=sys.stderr)

        ret_data = json.loads(r.text)
        print("SUCCESSFULLY REGISTERED FUNCTION TO SERVER!",ret_data, file=sys.stderr)
    return 


### DECORATORS ################################################################
def slider(func, arg, min_val, max_val, div):
    """
    if arg is matched in func signature, its UI representation will be a slider
    with minimum min_val, maximum max_val, and divisions div.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args,**kwargs)
    return wrapper

def demo(func):
    """
    inspects a function, func and spins off a server which can be used to 
    remotely call the function via a web interface or REST API.

    API generated for function is called through base server at _DEMO_SERVER_IP.

    ui_kwargs will  be generated and passed in by functions which decorate 
    the demo decorator.
    """
    global _function_registry

    print('*'*80, file=sys.stderr)
    # parse func args first.
    func_key, func_data = parse_function(func)
    error_if_func_exists(func_key,_function_registry)
    _function_registry[func_key] = func_data
    update_demo_server(func_key)
    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper

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
    return flask.jsonify({"msg":"success","result":result})
