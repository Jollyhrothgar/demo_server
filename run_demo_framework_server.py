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
import json
import pickle
from urllib.request import urlopen
import time
import threading

# Framework

# GLOBALS #####################################################################
HOSTNAME = '0.0.0.0'
GITLAB_SERVER = '192.168.0.125'
PORT = 6969
CLIENT_PORT = 35557
STATIC = os.path.join(os.path.dirname(__file__),'demo_framework_server')
TEMPLATES = os.path.join(os.path.dirname(__file__),'demo_framework_server/templates')
DEMO_DIR = os.path.join(os.path.dirname(__file__),'demos')
API_TOKEN = '8icMAisLE_cMZZ9v1TtE'
API_URL = 'http://192.168.0.125/api/v3/projects/all?private_token={}'
API_URL = API_URL.format(API_TOKEN)
app = flask.Flask(__name__, static_folder=STATIC, template_folder=TEMPLATES)

mlpux_instances = {} # maps uuid to mlpux_instance copy
mlpux_instance = {
    'PORT':None,
    'IP':None,
    'func':{}, # dict of func name to func params
}

# dict of uuids pointing to mlpux_instance dicts

def print_config():
    """
    prints configuration to console
    """
    global HOSTNAME, GITLAB_SERVER, PORT, STATIC, TEMPLATES, DEMO_DIR, API_TOKEN, API_URL, API_URL
    print('HOSTNAME : {}'.format(HOSTNAME))
    print('GITLAB_SERVER : {}'.format(GITLAB_SERVER))
    print('PORT : {}'.format(PORT))
    print('STATIC : {}'.format(STATIC))
    print('TEMPLATES : {}'.format(TEMPLATES))
    print('DEMO_DIR : {}'.format(DEMO_DIR))
    print('API_TOKEN : {}'.format(API_TOKEN))
    print('API_URL : {}'.format(API_URL))


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


@app.route('/register_function',methods=['POST'])
def register_function():
    global mlpux_instance, mlpux_instances, CLIENT_PORT
    content = flask.request.data
    ip = flask.request.remote_addr
    data = pickle.loads(content)
    uuid = data['uuid']
    mlpux_instances[uuid] = dict(mlpux_instance)
    mlpux_instances[uuid]['PORT'] = CLIENT_PORT 
    mlpux_instances[uuid]['IP'] = ip
    CLIENT_PORT += 1
    mlpux_instances[uuid]['func'][data['name']] = {'parameters':data['parameters'], 'documentation':data['documentation']}

    print("FLASK SERVER UPDATED", mlpux_instances)
    print("ORIGIN IP: ", ip)
    return "AWESOME".encode(encoding='utf8')

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
