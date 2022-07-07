from flask import Flask, abort, request
from flask_executor import Executor
from flask_shell2http import Shell2HTTP
import logging
import sys
import os
import yaml

def update_config(config_filepath='config.yml'):
    # Import config options

    with open(config_filepath) as file:
        config_data = yaml.load(file, Loader=yaml.FullLoader)
    return config_data

# Import config options
config_data = update_config()
trusted_proxies = config_data.get('TRUSTED_PROXIES')
ip_whitelist = config_data.get('IP_WHITELIST')

# Flask application instance
app = Flask(__name__)

# Set up logging if run by gunicorn
if __name__ != '__main__':
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)

# Log file
logFormatter = logging.Formatter("%(asctime)s [%(levelname)-5.5s]  %(message)s")
file_handler = logging.FileHandler("pix_plot.log")
file_handler.setFormatter(logFormatter)
app.logger.addHandler(file_handler)

# Flask_shell2http logger
fs2h_logger = logging.getLogger("flask_shell2http")
# create new handler
handler = logging.StreamHandler(sys.stdout)
fs2h_logger.addHandler(handler)
fs2h_logger.addHandler(file_handler)
# log messages of severity DEBUG or lower to the console
fs2h_logger.setLevel(logging.DEBUG)  # this is really important!

# # Test logs
# app.logger.debug('this is a DEBUG message')
# app.logger.info('this is an INFO message')
# app.logger.warning('this is a WARNING message')
# app.logger.error('this is an ERROR message')
# app.logger.critical('this is a CRITICAL message')

# Set upload folder
path = os.getcwd()
UPLOAD_FOLDER = os.path.join(path, 'data/uploads')
PLOTS_FOLDER = os.path.join(path, 'data/plots')
# Make dir if does not exist
for folder in [UPLOAD_FOLDER, PLOTS_FOLDER]:
    if not os.path.isdir(folder):
        os.makedirs(folder)

# Config app
app.secret_key = "secret key"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SERVER_HTTPS'] = config_data.get('HTTPS')
# Limit size of upload; 16 * 1024 * 1024 is 16 megabytes
#app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# Allowed upload extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}


@app.before_request
def limit_remote_addr():
    """
    Checks the incoming IP address and compares with whitelist
    """
    config_data = update_config()
    trusted_proxies = config_data.get('TRUSTED_PROXIES')
    ip_whitelist = config_data.get('IP_WHITELIST')

    if ip_whitelist:
        # Allow all to view plots
        if "/plots/" in request.path:
            return

        # Check that whitelist exists
        route = request.access_route + [request.remote_addr]
        remote_addr = next((addr for addr in reversed(route) if addr not in trusted_proxies), request.remote_addr)
        app.logger.debug('remote_address: '+str(remote_addr))
        if remote_addr not in ip_whitelist:
            abort(403)  # Forbidden
    else:
        # No whitelist = access for all
        return

# Import simple web interface
import simple_interface

# Import flask API endpoints
import api

# PixPlot command API
executor = Executor(app)
shell2http = Shell2HTTP(app=app, executor=executor, base_url_prefix="/api/")

shell2http.register_command(endpoint="pixplot", command_name="python /usr/src/app/pixplot/pixplot.py")
shell2http.register_command(endpoint="yale_pixplot", command_name="pixplot")

if __name__ == "__main__":
    print('Starting server...')
    app.run(host='0.0.0.0', debug=True)
