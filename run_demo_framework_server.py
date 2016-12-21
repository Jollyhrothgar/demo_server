# Python libraries
import flask
import threading
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

# Framework

# GLOBALS #####################################################################
HOSTNAME = '0.0.0.0'
GITLAB_SERVER = '192.168.0.125'
PORT = 80
CLIENT_PORT = 35557
STATIC = os.path.join(os.path.dirname(__file__),'demo_framework_server')
TEMPLATES = os.path.join(os.path.dirname(__file__),'demo_framework_server/templates')
DEMO_DIR = os.path.join(os.path.dirname(__file__),'demos')
API_TOKEN = '8icMAisLE_cMZZ9v1TtE'
API_URL = 'http://192.168.0.125/api/v3/projects/all?private_token={}'
API_URL = API_URL.format(API_TOKEN)
app = flask.Flask(__name__, static_folder=STATIC, template_folder=TEMPLATES)

# regestry of known instances of mlpux decorated functions.
mlpux_instances = {} # maps uuid to mlpux decorated function

# template for how to talk to functions
mlpux_instance = {
    'PORT':None,
    'IP':None,
    'functions':[], # dict of func name to func params
}

# TODO
# Need a periodic check to see if the various function servers are up, and if not, kill from UI
def check_up(server_ip, port):
    """
    checks for whether or not attached mlpux clients are alive
    """

    return True

def print_config():
    """
    prints configuration to console
    """
    global HOSTNAME, GITLAB_SERVER, PORT, STATIC, TEMPLATES, DEMO_DIR, API_TOKEN, API_URL, API_URL
    print(80*"=")
    print('HOSTNAME : {}'.format(HOSTNAME))
    print('GITLAB_SERVER : {}'.format(GITLAB_SERVER))
    print('PORT : {}'.format(PORT))
    print('STATIC : {}'.format(STATIC))
    print('TEMPLATES : {}'.format(TEMPLATES))
    print('DEMO_DIR : {}'.format(DEMO_DIR))
    print('API_TOKEN : {}'.format(API_TOKEN))
    print('API_URL : {}'.format(API_URL))
    print(80*"=")


# FLASK APPLICATION ROUTES ####################################################
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
    data = flask.request.json
    recreate_demo(data['repository']['name'])
    print("webhook:", json.dumps(data,indent=2) ,"end webhook.")
    return ""

@app.route('/')
def index():
    return flask.render_template('index.html')

@app.route("/hello",methods=['GET'])
def hello():
    print("HELLO")
    return flask.make_response("200".encode(encoding="utf8"))

# mlpux_instances structure:
#    {
#        uuid: {
#            'PORT':<port number>,
#            'IP':<ip address>,
#            'functions':[
#                'parameters':parameters,
#                'documentation':documentation, 
#                'name':func.__name__,
#                'ui_args':ui_kwargs,
#                'uuid':_UUID
#            ],
#            ...similarly for all functions associated with the uuid
#        }
#    }
@app.route("/get_demos",methods=['GET'])
def get_demos():
    """
    Respond to front end request for demo list. Returns a list of demos to populate
    a selection on the UI.

    Sends UUID for the function and a UUID to talk to the mlpux server.
    """

    # Check for dead clients
    dead_clients = []
    for uuid,client in mlpux_instances.items():
        if not check_up(mlpux_instances[uuid]['IP'], mlpux_instances[uuid]['PORT']):
            dead_clients.append(uuid)

    # Remove dead clients
    for uuid in dead_clients:
        print ("LOST CONTACT WITH", mlpux_instances['uuid'], "REMOVING")
        del mlpux_instances[uuid]

    # Now that we've pruned the dead stuff, we may proceed.
    return_data = []
    for uuid,client in mlpux_instances.items():
        for function in client['functions']:
            return_data.append({"uuid":uuid,"IP":mlpux_instances[uuid]['IP'], "PORT":mlpux_instances[uuid]['PORT'], "name":function['name']})
    return flask.jsonify(return_data)

@app.route('/register_function',methods=['POST'])
def register_function():
    global mlpux_instance, mlpux_instances, CLIENT_PORT
    request_content = flask.request.data
    ip = flask.request.remote_addr
    _func_data = pickle.loads(request_content) # mlpux.py: _func_data
    uuid = _func_data['uuid']
    
    if uuid not in mlpux_instances:
        mlpux_instances[uuid] = dict(mlpux_instance) 
        mlpux_instances[uuid]['PORT'] = CLIENT_PORT 
        mlpux_instances[uuid]['IP'] = ip
        mlpux_instances[uuid]['functions'] = [ dict(_func_data['function']) ]
        CLIENT_PORT += 1
    else:
        # if somehow the connection dies to the client, there will be a new
        # uuid, so there should not be duplicate functions within one uuid.
        mlpux_instances[uuid]['functions'].append(dict(_func_data['function']))
        
    print("FLASK SERVER UPDATED WITH ", mlpux_instances[uuid]['functions'][-1]['name'])
    print("CLIENT AT {}:{}".format(mlpux_instances[uuid]['IP'], mlpux_instances[uuid]['PORT']))
    print(80*"=")
   
    # TODO implement failure handling
    ret_val = {'status':'SUCCESS', 'PORT':mlpux_instances[uuid]['PORT']}
    return flask.jsonify(ret_val)

# END FLASK APPLICATION ROUTES ################################################

# HELPER FUNCTIONS ############################################################
def monitor_modules():
    pass

def git_cmd(*args):
    """
    Take a comma separated list of arguments and pass to git in shell subprocess
    """
    return subprocess.check_output(['git']+list(args))

def recreate_demo(project_name):
    if os.path.isdir('{}/{}'.format(DEMO_DIR, project_name)):
        print("Removing Demo Area: {}/{}".format(DEMO_DIR, project_name))
        shutil.rmtree('{}/{}'.format(DEMO_DIR, project_name))
    print("Creating Demo Area")
    git_cmd('clone', 'http://{}/demos/{}'.format(GITLAB_SERVER, project_name), '{}/{}'.format(DEMO_DIR, project_name))
    open('{}/__init__.py'.format(DEMO_DIR),'a').close()

    # example - we can import everything, but we still don't have access to the output
    # of mlpux.build_ui decorator. 
    exec("import demos.test_module.test_module as {}".format(project_name))
    # for i in dir(project_name):
        # print(i)
    stuff = eval("{}.no_args()".format(project_name))
    print(stuff)
    return


#### MAYBE KILL THIS PART? TODO ####
def clear_demos():
    global demos
    demos = []
    print("Emptying the demos area")
    try:
        shutil.rmtree(DEMO_DIR)
        shutil.os.mkdir(DEMO_DIR)
    except:
        shutil.os.mkdir(DEMO_DIR)
    print("Ready for Demos")
    return

def get_demos():
    """
    Uses the GitLab API to get a full repository listing and extract the projects
    which belong to the demos group.
    """
    global demos
    all_projects = json.loads(urlopen(API_URL).read().decode())
    for project in all_projects:
        if project['namespace']['name'] == 'demos':
            tokens = project['name_with_namespace'].split()
            demos.append(tokens[2]) # third token is project name
            print("DEMO FOUND: ", project['path_with_namespace'])
    for demo in demos:
        recreate_demo(demo)
    return

#### END MAYBE KILL THIS PART ####

# END HELPER FUNCTIONS ########################################################

# UNIT TESTS ##################################################################
# END UNIT TESTS ##############################################################

def reset():
    clear_demos()
    get_demos()

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
    time.sleep(2)
    print_config()
    #reset() # waiting for GitLab server to be back up
