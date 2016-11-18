# Python libraries
import flask
import logging as log
import threading
import os

# Framework

# GLOBALS #####################################################################
HOSTNAME = '0.0.0.0'
PORT = 6969
STATIC = os.path.join(os.path.dirname(__file__),'demo_framework_server')
TEMPLATES = os.path.join(os.path.dirname(__file__),'demo_framework_server/templates')
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

@app.route('/webhook', methods=['GET','POST'])
def webhook():
    content = flask.request
    print(content)

@app.route('/')
def index():
    return flask.render_template('index.html')
# END FLASK APPLICATION ROUTES ################################################

# HELPER FUNCTIONS ############################################################
def monitor_modules():
    pass

# END HELPER FUNCTIONS ########################################################

# UNIT TESTS ##################################################################
# END UNIT TESTS ##############################################################

if __name__ == "__main__":
    app.run(
        host=HOSTNAME,
        port=PORT,
        debug=True
    )
