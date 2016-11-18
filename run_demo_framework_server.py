# Python libraries
import flask
import logging as log
import threading
import os
import shutil
import json
import subprocess

# Framework

# GLOBALS #####################################################################
HOSTNAME = '0.0.0.0'
GITLAB_SERVER = '10.0.1.10'
PORT = 6969
STATIC = os.path.join(os.path.dirname(__file__),'demo_framework_server')
TEMPLATES = os.path.join(os.path.dirname(__file__),'demo_framework_server/templates')
DEMO_DIR = '/home/mike/workspace/demo_framework/demos'
app = flask.Flask(__name__, static_folder=STATIC, template_folder=TEMPLATES)

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
# END FLASK APPLICATION ROUTES ################################################

# HELPER FUNCTIONS ############################################################
def monitor_modules():
    pass

def git_cmd(*args):
    """
    Take a comma separated list of arguments and pass to git in shell subprocesss
    """
    return subprocess.check_output(['git']+list(args))


def recreate_demo(project_name):
    if os.path.isdir('{}/{}'.format(DEMO_DIR, project_name)):
        print("Removing Demo Area: {}".format(DEMO_DIR, project_name))
        shutil.rmtree('{}/{}'.format(DEMO_DIR, project_name))
    print("Creating Demo Area")
    git_cmd('clone', 'http://{}/demos/{}'.format(GITLAB_SERVER, project_name), '{}/{}'.format(DEMO_DIR, project_name))
    return

def clear_demos():
    try:
        shutil.rmtree(DEMO_DIR)
        shutil.os.mkdir(DEMO_DIR)
    except:
        shutil.os.mkdir(DEMO_DIR)
# END HELPER FUNCTIONS ########################################################

# UNIT TESTS ##################################################################
# END UNIT TESTS ##############################################################

def startup_tasks():
    clear_demos()

if __name__ == "__main__":
    startup_tasks()
    app.run(
        host=HOSTNAME,
        port=PORT,
        debug=True
    )
