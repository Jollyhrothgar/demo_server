# Python libraries
import ast
import flask
import threading
import sys
import os
import shutil
import json
import subprocess
import shlex
import inspect
import itertools
from functools import wraps
from collections import OrderedDict
import pickle
from urllib.request import urlopen
import time
import threading
import discovery
import requests
import random
from threading import Lock

# Plotting
import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt
plt.ioff()
import mpld3
from mpld3 import plugins

from formencode.variabledecode import variable_decode
from formencode.variabledecode import variable_encode
# Framework

# GLOBALS #####################################################################
discovery.discoverable(service_name="demo server")
HOSTNAME = '0.0.0.0'
GITLAB_SERVER = '192.168.0.125'
PORT = 5002 # switch to 80 for deployment
STATIC = os.path.join(os.path.dirname(__file__),'demo_framework_server')
TEMPLATES = os.path.join(os.path.dirname(__file__),'demo_framework_server/templates')
DEMO_DIR = os.path.join(os.path.dirname(__file__),'demos')
API_TOKEN = '8icMAisLE_cMZZ9v1TtE'
API_URL = 'http://192.168.0.125/api/v3/projects/all?private_token={}'
API_URL = API_URL.format(API_TOKEN)
app = flask.Flask(__name__, static_folder=STATIC, template_folder=TEMPLATES)
lock = Lock() # global lock used for plotting (maybe plot with interactive: on)

# regestry of known instances of mlpux decorated functions.
mlpux_instances = {} # maps client_uuid to mlpux decorated function
""" 
    mlpux_instances = 
    {
        <mlpux client uuid>:{
            "IP":           < mlpux client ip address >,
            "PORT":         < mlpux client port >,
            "client_uuid":  < mlpux client ip >,
            "functions":[
                { 
                    "PORT":          < duplicate mlpux client port >,
                    "client_uuid":   < duplicate mlpux client ip >,
                    "display":       < display parameters >,
                    "documentation": < mlpux client function docstring >,
                    "func_key":      < mlpux client function func_key >,
                    "func_name":     < mlpux client function name >,
                    "func_scope":    < mlpux client function scope: either: < file > or < module dir >.< file >,
                    "func_uuid":     < mlpux client function uuid (currently func_key >,
                    "signature":     < mlpux stringified signature >,
                    "parameters":[
                        {
                            "annotation":    < parameter annotation  >,
                            "default_value": < parameter default value, or None >,
                            "name":          < parameter name >,
                            "param_gui":     < dict of gui parametrs >,
                            "position":      < int referring to param position in function signature > ,
                            "type":          <"standard", "keyword", or "positional" >,
                        },
                        {...}, # for all parameters in the funciton signature
                    ]
                },
                { .. }, # another function
            ]
    }
"""

# TODO
# Need a periodic check to see if the various function servers are up, and if not, kill from UI
def check_up(client_uuid):
    """
    checks for whether or not attached mlpux clients are alive
    """
    global mlpux_instances
    try:
        ip = mlpux_instances[client_uuid]['IP']
        port = mlpux_instances[client_uuid]['PORT']
        r = requests.get(url="http://{}:{}/test_up".format(ip,port))
    except:
        return False
    return True

def print_config():
    """
    prints configuration to console
    """
    global HOSTNAME, GITLAB_SERVER, PORT, STATIC, TEMPLATES, DEMO_DIR, API_TOKEN, API_URL, API_URL
    print(80*"=", file=sys.stderr)
    print('HOSTNAME : {}'.format(HOSTNAME), file=sys.stderr)
    print('GITLAB_SERVER : {}'.format(GITLAB_SERVER), file=sys.stderr)
    print('PORT : {}'.format(PORT), file=sys.stderr)
    print('STATIC : {}'.format(STATIC), file=sys.stderr)
    print('TEMPLATES : {}'.format(TEMPLATES), file=sys.stderr)
    print('DEMO_DIR : {}'.format(DEMO_DIR), file=sys.stderr)
    print('API_TOKEN : {}'.format(API_TOKEN), file=sys.stderr)
    print('API_URL : {}'.format(API_URL), file=sys.stderr)
    print(80*"=", file=sys.stderr)


def process_output(data):
    """
    returns exception message if data cannot be json serialized.
    returns jsonified data otherwise.
    """
    if 'error' in data:
        return flask.jsonify(data)

    if data['display'] == 'plot':
        lock = Lock()
        x = data['x']
        y = data['y']

        with lock:
            fig, ax = plt.subplots()
            ax.plot(x, y)
        try:
            data['plot_soup'] = mpld3.fig_to_html(fig)
            return flask.jsonify(data)
        except Exception as e:
            return flask.jsonify({'error':"couldn't plot data: {}, {}, exception: {}".format(repr(x), repr(y), e)})
    else:
        try:
            return flask.jsonify(data)
        except Exception as e:
            return flask.jsonify({"error":"flask.jsonify failed with data:{}".format(data)})

# FLASK APPLICATION ROUTES ####################################################
@app.route('/test_plot',methods=['GET'])
def test_plot():
    lock = Lock()
    x = range(100)
    y = [a**2 for a in x]
    with lock:
        fig, ax = plt.subplots()
        ax.plot(x, y)
    return mpld3.fig_to_html(fig)

@app.route('/test_up',methods=['GET'])
def test_up():
    return flask.make_response("200".encode(encoding="utf8"))
    
@app.route('/favicon.ico')
def favicon():
    search_path = os.path.join(app.root_path,STATIC)
    print ('FAVICON PATH:',search_path)
    return flask.send_from_directory(
        search_path,
        'favicon.ico',
        mimetype='image/vnd.microsoft.icon'
    )

@app.route('/webhook', methods=['GET','POST','TCP'])
def webhook():
    recreate_demos()
    # For individual projects which are each cloned to demos
    # data = flask.request.json
    # recreate_demo(data['repository']['name'])
    # print("webhook:", json.dumps(data,indent=2) ,"end webhook.", file=sys.stderr)
    return ""

@app.route('/')
def index():
    return flask.render_template('index.html')

@app.route('/show_mlpux', methods=['GET'])
def show_mlpux():
    global mlpux_instances
    # Crashes with a direct dump for some stupid fucking reason.
    return flask.jsonify(json.loads(json.dumps(mlpux_instances)))

@app.route("/request_demo_list",methods=['GET'])
def request_demo_list():
    """
    Respond to front end request for demo list. Returns a list of demos to populate
    a selection on the UI.

    Sends UUID for the function and a UUID to talk to the mlpux server.
    """
    global mlpux_instances

    # Check for dead clients
    dead_clients = []
    for client_uuid,client in mlpux_instances.items():
        if not check_up(client_uuid):
            dead_clients.append(client_uuid)

    # Remove dead clients
    for client_uuid in dead_clients:
        print ("LOST CONTACT WITH", mlpux_instances[client_uuid]['IP'],':',mlpux_instances[client_uuid]['PORT'], "REMOVING", file=sys.stderr)
        del mlpux_instances[client_uuid]

    # Now that we've pruned the dead stuff, we may proceed.
    return_data = []
    for client_uuid,client in mlpux_instances.items():
        for function in client['functions']:
            #print(mlpux_instances[client_uuid], file=sys.stderr)
            ret = {
                'IP':mlpux_instances[client_uuid]['IP'],
                'PORT':mlpux_instances[client_uuid]['PORT'],
                'client_uuid':client_uuid,
                'func_uuid':function['func_uuid'],
                'func_name':function['func_name'],
                'func_scope':function['func_scope'],
                'func_key':function['func_key']
            }
            return_data.append(dict(ret))
    return flask.jsonify(return_data)

@app.route("/request_demo",methods=['POST'])
def request_demo():
    """
    Back endpoint for UI request for a demo function. Request is a JSON object
    of the form:

        {'func_uuid':<uuid for function>, 'client_uuid':<uuid for client>}

    """
    global mlpux_instances
    try:
        request_content = flask.request.get_data().decode('utf-8')
        request_content = json.loads(request_content)
    except:
        return flask.jsonify({'error':"<h1> DEMO CONNECTION FAILED </h1>"})
    
    if 'func_key' not in request_content or 'client_uuid' not in request_content:
        return flask.jsonify({'error':"<h1> KEYS FOR FUNCTION UUID OR CLIENT UUID MISSING </h1>"})

    client_uuid = request_content['client_uuid']
    func_key = request_content['func_key']

    if not check_up(client_uuid):
        return flask.jsonify({'error','<h1> CLIENT SERVER FOR FUNCTION IS DOWN </h1>'})

    if client_uuid not in mlpux_instances:
        return flask.jsonify({'error':'client is unknown'})

    for function in mlpux_instances[client_uuid]['functions']:
        if func_key == function['func_key']:
            d = {k:v for k,v in function.items() if k in ['annotation','func_name','func_scope','documentation','signature','func_key','parameters','param_gui']}
            d['client_uuid'] = client_uuid
            return flask.jsonify(dict(d))
    return flask.jsonify({"error":"function not found"})

@app.route('/register_function',methods=['POST'])
def register_function():
    global mlpux_instance, mlpux_instances
    request_content = flask.request.data
    ip = flask.request.remote_addr
    _func_data = pickle.loads(request_content) # mlpux.py: _func_data
    client_uuid = _func_data['client_uuid']
    function = None
    if client_uuid not in mlpux_instances:

        mlpux_instances[client_uuid] = {
            "IP":ip,
            "PORT":_func_data['PORT'],
            'functions':[dict(_func_data)]

        }
        function = dict(_func_data)
    else:
        append_function = True
        for i,function in enumerate(mlpux_instances[client_uuid]['functions']):
            if function['func_uuid'] == _func_data['func_uuid']:
                # Update Existing Function
                mlpux_instances[client_uuid]['functions'][i] = dict(_func_data)
                append_function = False
                function = dict(_func_data)
        # Add New Function
        if append_function:
            mlpux_instances[client_uuid]['functions'].append(dict(_func_data))
            function = dict(_func_data)

    # Print message that a parameter has been updated.
    for param in function['parameters']:
        if param['param_gui'] is not None:
            print("FLASK SERVER UPDATED WITH ", function['func_name'], function['parameters'], file=sys.stderr)
            print("CLIENT AT {}:{}".format(mlpux_instances[client_uuid]['IP'], mlpux_instances[client_uuid]['PORT']), file=sys.stderr)
    # Keep output separated
    print(80*"=", file=sys.stderr)
    ret_val = {'status':'SUCCESS', 'PORT':mlpux_instances[client_uuid]['PORT']}
    return flask.jsonify(ret_val)

@app.route('/execute/<string:func_scope>/<string:func_name>', methods=['GET'])
def execute(func_scope, func_name):
    """
    Argument parsing is independant of the funciton actually working. We parse arguments here
    and here only, then pass them along to the appropriate mlpux server via pickled data stream

    Convention:
    args are passed in args array in get request
    kwargs are passed as typical for get request.
    Example argument scenarios:
    endpoint/func?args=[x,y,z...]&A=a&B=b&... (positional and keyword)".format(e,func_key,func_args)}
    endpoint/func?args=[x,y,z...] (positional only)".format(e, func_key,func_args)}
    endpoint/func?X=x&Y=y&Z=z... (keyword only) ".format(e, func_key,func_args)}
    endpoint type: endpoint/func (no arguments)".format(e,func_key)}
    """

    func_key = func_scope + "." + func_name
    print("RECEIVED ARGUMENTS FROM GET REQUEST: ",flask.request.args, file=sys.stderr)
    print("CONVERTED TO DICT:",variable_decode(flask.request.args), file=sys.stderr)

    # Dictionary of args
    func_args = variable_decode(flask.request.args) 
    args = []
    kwargs = {}

    # Parse out args and kwargs
    # Any function can be called with *args and/or **kwargs.
    try:
        for k,v in func_args.items():
            print(k, v, file=sys.stderr)
            if k == 'args':
                try:
                    args += ast.literal_eval(v)
                except:
                    msg = {"error":"Parsing args parameter in GET reqeust failed. Could not evaluate {0} as an *args array with ast.literal_eval({0}).".format(v)}
                    print(msg, file=sys.stderr)
                    return flask.jsonify(msg)
            else:
                kwargs[k] = ast.literal_eval(v)
    except Exception as e:
        print("args:",args,"kwargs:",kwargs,file=sys.stderr)
        msg = {"error":"could not parse arguments! Exception: '{}'".format(e)}
        print(msg, file=sys.stderr)
        msg.update(func_args)
        return flask.jsonify(msg)

    # now that args and kwargs are filled, send via pickled POST message.
    arguments = {
        'func_key':func_key,
        'args':args,
        'kwargs':kwargs
    }
    print('PARSED ARGUMENTS {} FOR {}'.format(repr(arguments),func_key),file=sys.stderr)

    for client_uuid, client in mlpux_instances.items():
        for function in client['functions']:
            if func_key == function['func_key'] and func_name == function['func_name']:
                mlpux_ip = mlpux_instances[client_uuid]['IP']
                mlpux_port = mlpux_instances[client_uuid]['PORT']

                send_data = pickle.dumps(arguments,-1)
                # Check if client is up TODO
                # try:
                    # r = requests.get(url='http:{}/{}'.format(mlpux_ip, mlpux_port))
                # except Exception as e:
                    # msg = {'error':"MLPUX server seems to be unreachable: {}:{}".format(mlpux_ip,mlpux_port)}
                    # msg.update({'remove_function':{'func_name':func_name,'func_key':func_key}})
                    # return flask.jsonify(msg)
                   

                try:
                    print('POSTING ARGUMENTS {} to mlpux server for {}'.format(repr(arguments),func_key), file=sys.stderr)
                    print('BINARY DATA: ', send_data, file=sys.stderr) 
                    r = requests.post(url='http://{}:{}/execute'.format(mlpux_ip,mlpux_port), data=send_data)
                    print("SENT TO URL",r.url, file=sys.stderr)
                    print("Received response from client {}".format(repr(r.json())), file=sys.stderr)
                    return process_output(r.json())
                except Exception as e:
                    return flask.jsonify({'error':'problem communicating with mlpux client {}:{}. Exception: {}'.format(mlpux_ip,mlpux_port,e)})
    return flask.jsonify({"error":"No function was found. Function: {}".format(func_key)})

# END FLASK APPLICATION ROUTES ################################################

# HELPER FUNCTIONS ############################################################
def lookup_function_name(client_uuid, func_key, mlpux_instances):
    """
    Looks up function name from client and function uuid. Linear time, may need
    to make more efficient if number of functions becomes very large.
    """
    func_name = None
    if client_uuid not in mlpux_instances:
        print("ERROR: client {} does not exist.".format(client_uuid), file=sys.stderr)
        return func_name
    functions = mlpux_instances[client_uuid]['functions']
    for function in functions:
        if func_key == function['func_key']:
            func_name = function['func_name']
            return func_name
    print("ERROR: function {} does not exist for client {}".format(func_name,client_uuid), file=sys.stderr)
    return func_name

def git_cmd(*args):
    """
    Take a comma separated list of arguments and pass to git in shell subprocess
    """
    return subprocess.check_output(['git']+list(args))

# all demos live in one repo
def recreate_demo():
    if os.path.isdir('{}/{}'.format(DEMO_DIR, project_name)):
        print("Removing Demo Area: {}/{}".format(DEMO_DIR, project_name), file=sys.stderr)
        shutil.rmtree('{}/{}'.format(DEMO_DIR, project_name))
    print("Creating Demo Area", file=sys.stderr)
    git_cmd('clone', 'http://{}/demos'.format(GITLAB_SERVER))

    # Deploy MLPUX Demos
    subprocess.check_output(['./deploy.sh'])
    return

# used for when each demo had its own repo
# def recreate_demo(project_name):
    # if os.path.isdir('{}/{}'.format(DEMO_DIR, project_name)):
        # print("Removing Demo Area: {}/{}".format(DEMO_DIR, project_name), file=sys.stderr)
        # shutil.rmtree('{}/{}'.format(DEMO_DIR, project_name))
    # print("Creating Demo Area", file=sys.stderr)
    # git_cmd('clone', 'http://{}/demos/{}'.format(GITLAB_SERVER, project_name), '{}/{}'.format(DEMO_DIR, project_name))
    # open('{}/__init__.py'.format(DEMO_DIR),'a').close()

    # # example - we can import everything, but we still don't have access to the output
    # # of mlpux.build_ui decorator. 
    # exec("import demos.test_module.test_module as {}".format(project_name))
    # # for i in dir(project_name):
        # # print(i, file=sys.stderr)
    # stuff = eval("{}.no_args()".format(project_name))
    # print(stuff, file=sys.stderr)
    # return
# def get_demos():
    # """
    # Uses the GitLab API to get a full repository listing and extract the projects
    # which belong to the demos group.
    # """
    # global demos
    # all_projects = json.loads(urlopen(API_URL).read().decode())
    # for project in all_projects:
        # if project['namespace']['name'] == 'demos':
            # tokens = project['name_with_namespace'].split()
            # demos.append(tokens[2]) # third token is project name
            # print("DEMO FOUND: ", project['path_with_namespace'], file=sys.stderr)
    # for demo in demos:
        # recreate_demo(demo)
    # return


# END HELPER FUNCTIONS ########################################################

# UNIT TESTS ##################################################################
# END UNIT TESTS ##############################################################

if __name__ == "__main__":
    app_thread = threading.Thread(
        target=app.run,
        kwargs = {
            'host':HOSTNAME,
            'port':PORT,
            'debug':False,
            'threaded':True,
        }
    )
    app_thread.start()
    time.sleep(0.5)
    print_config()
    #reset() # waiting for GitLab server to be back up
