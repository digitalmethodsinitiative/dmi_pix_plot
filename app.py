from flask import Flask, flash, abort, send_file, request, redirect, render_template, Markup, jsonify, url_for
from werkzeug.utils import secure_filename
from flask_executor import Executor
from flask_shell2http import Shell2HTTP
import logging
import requests
import uuid
import sys
import os
import time
import yaml

# Import config options
with open('config.yml') as file:
    config_data = yaml.load(file, Loader=yaml.FullLoader)

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
# Limit size of upload; 16 * 1024 * 1024 is 16 megabytes
#app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# Allowed upload extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}


@app.before_request
def limit_remote_addr():
    """
    Checks the incoming IP address and compares with whitelist
    """
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


def allowed_file(filename, extensions=ALLOWED_EXTENSIONS):
    """
    Check filenames to ensure they are an allowed extension
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in extensions


# File browser
def dir_listing(base_dir, req_path, template):
    # Joining the upload folder and the requested path
    abs_path = os.path.join(base_dir, req_path)

    # Return 404 if path doesn't exist
    if not os.path.exists(abs_path):
        return abort(404)

    # Check if path is a file and serve
    if os.path.isfile(abs_path):
        return send_file(abs_path)

    # Show directory contents
    files = os.listdir(abs_path)
    current_dir = req_path.split('/')[-1]
    return render_template(template, files=files, current_dir=current_dir)


# Home
@app.route('/')
def home():
    return render_template('home.html')


# Use file browser for uploads
@app.route('/uploads/', defaults={'req_path': ''})
@app.route('/uploads/<path:req_path>')
def uploads(req_path):
    return dir_listing(UPLOAD_FOLDER, req_path, 'images.html')


# Use file browser for plots
# TODO create plots specific browser
@app.route('/plots/', defaults={'req_path': ''})
@app.route('/plots/<path:req_path>')
def plots(req_path):
    return dir_listing(PLOTS_FOLDER, req_path, 'plots.html')


# Interactive upload
@app.route('/upload/', methods=['GET', 'POST'])
def upload_form():
    if request.method == 'POST':
        result_response, status_code = process_images(request)

        if status_code != 200:
            message = 'There was an error uploading photos: ' + str(result_response['reason'])
            flash(message)
            return redirect('/upload/')
        else:
            return redirect(url_for('uploads', req_path=result_response['folder_name']))
    else:
        return render_template('upload_form.html')


# Create PixPlot
@app.route('/create/', methods=['GET','POST'])
def create():
    folders = os.listdir(UPLOAD_FOLDER)

    if request.method == 'GET':
        return render_template('create.html', folders=folders)
    elif request.method == 'POST':
        form_data = request.form
        image_location = os.path.join(UPLOAD_FOLDER, form_data['folder_name'])

        destination = os.path.join(PLOTS_FOLDER, form_data['folder_name'])

        if os.path.isfile(os.path.join(image_location, 'metadata.csv')):
            metadata = os.path.join(image_location, 'metadata.csv')
            data = {"args" : ['--images', image_location + "/*.jpg", '--out_dir', destination, '--metadata', metadata]}
        else:
            data = {"args" : ['--images', image_location + "/*.jpg", '--out_dir', destination]}

        response = requests.post(request.url_root + "api/pixplot", json=data)
        app.logger.info('Create request status: ' + str(response.status_code))
        app.logger.debug('Create request status: ' + str(response.json()))

        while True:
            time.sleep(10)
            result = requests.get(response.json()['result_url'])
            app.logger.debug(str(result.json()))
            if 'status' in result.json().keys() and result.json()['status'] == 'running':
                # Still running
                continue
            elif 'report' in result.json().keys() and result.json()['report'][-6:-1] == 'Done!':
                # Complete without error
                message = Markup('<a href="/plots/%s/index.html" class="alert-link">Finished! Your PixPlot is uploaded here.</a>' % form_data['folder_name'])
                break
            else:
                # Something botched
                message = 'There was an error creating your PixPlot. Sorry.'
                app.logger.error(str(result.json()))
                break

        flash(message)
        return redirect('/create/')

    else:
        return abort(404)

# API upload images
@app.route('/api/send_photo', methods=['POST'])
def upload_photo_api():
    """
    data = {'folder_name': 'desired_name'}
    files = {'image': open('image_1.jpg', 'rb')}
    """
    folder_name = request.form.get('folder_name', None)
    if not folder_name:
        app.logger.warning('No folder_name provided')
        return jsonify({'reason' : 'Must provide folder_name for single images'}), 400

    image_folder = os.path.join(app.config['UPLOAD_FOLDER'], folder_name)

    # Make folder if it does not already exist
    if not os.path.isdir(image_folder):
        os.mkdir(image_folder)

    image = request.files.get('image', None)
    if image and allowed_file(image.filename):
        filename = secure_filename(image.filename)
        app.logger.info(f'Uploading {filename} to {folder_name}')
        image.save(os.path.join(image_folder, filename))

        json_data = {'args' : ['--images', image_folder + "/*", '--out_dir', PLOTS_FOLDER+ '/' + folder_name]}
        response = {
                    'upload_location' : request.url_root + 'uploads/' +  folder_name,
                    'folder_name' : folder_name,
                    'create_pixplot_post_info' : {
                        'url' : request.url_root + 'api/pixplot',
                        'json' : json_data,
                        },
                    }
        return response, 200
    else:
        app.logger.warning('No image received')
        return jsonify({'reason' : 'No image received'}), 400


@app.route('/api/send_metadata', methods=['POST'])
def upload_metadata_api():
    """
    data = {'folder_name': 'desired_name'}
    files = {'metadata': open('metadata.csv'), 'rb')}
    """
    folder_name = request.form.get('folder_name', None)
    if not folder_name:
        app.logger.warning('No folder_name provided')
        return jsonify({'reason' : 'Must provide folder_name for single images'}), 400

    image_folder = os.path.join(app.config['UPLOAD_FOLDER'], folder_name)

    # Make folder if it does not already exist
    if not os.path.isdir(image_folder):
        os.mkdir(image_folder)

    metadata = request.files.get('metadata', None)
    if metadata and allowed_file(metadata.filename, set(['csv'])):
        metadata_file_path = os.path.join(image_folder, 'metadata.csv')
        metadata.save(metadata_file_path)
        json_data = {'args' : ['--images', image_folder + "/*", '--out_dir', PLOTS_FOLDER + '/' + folder_name, '--metadata', metadata_file_path]}
        response = {
                    'upload_location' : request.url_root + 'uploads/' +  folder_name,
                    'folder_name' : folder_name,
                    'create_pixplot_post_info' : {
                        'url' : request.url_root + 'api/pixplot',
                        'json' : json_data,
                        },
                    }
        return response, 200
    else:
        app.logger.warning('No metadata received')
        return jsonify({'reason' : 'No metadata received'}), 400

# API upload images and metadata as one
@app.route('/api/send_photos', methods=['POST'])
def upload_photos_api():
    """
    files = [
        ('metadata', open('metadata.csv'), 'rb')),
        ('images', open('image_1.jpg', 'rb')),
        ('images', open('image_2.jpg', 'rb')),
    ]
    Optional:
    data = {'folder_name' : 'desired_name'}
    """

    result_response, status_code = process_images(request)
    return jsonify(result_response)


def process_images(request):
    if 'images' not in request.files or len(request.files.getlist('images')) < 1:
        # No images received
        app.logger.warning('No images received')
        return jsonify({'reason' : 'No images received'}), 400

    if request.form['folder_name']:
        folder_name = request.form['folder_name']
    else:
        folder_name = uuid.uuid4().hex

    app.logger.info('Uploading ' + str(len(request.files.getlist('images'))) + ' images')

    image_folder = os.path.join(app.config['UPLOAD_FOLDER'], folder_name)
    if not os.path.isdir(image_folder):
        os.mkdir(image_folder)

    images = request.files.getlist('images')
    for image in images:
        app.logger.debug('Image: ' + str(image))
        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            image.save(os.path.join(image_folder, filename))

    metadata = request.files.get('metadata', None)
    if metadata and allowed_file(metadata.filename, set(['csv'])):
        metadata_file_path = os.path.join(image_folder, 'metadata.csv')
        metadata.save(metadata_file_path)
        json_data = {'args' : ['--images', image_folder + "/*", '--out_dir', PLOTS_FOLDER + '/' + folder_name, '--metadata', metadata_file_path]}
    else:
        json_data = {'args' : ['--images', image_folder + "/*", '--out_dir', PLOTS_FOLDER+ '/' + folder_name]}

    response = {
                'upload_location' : request.url_root + 'uploads/' +  folder_name,
                'folder_name' : folder_name,
                'create_pixplot_post_info' : {
                    'url' : request.url_root + 'api/pixplot',
                    'json' : json_data,
                    },
                }

    return response, 200

# PixPlot command API
executor = Executor(app)
shell2http = Shell2HTTP(app=app, executor=executor, base_url_prefix="/api/")

shell2http.register_command(endpoint="pixplot", command_name="python /usr/src/app/pixplot/pixplot.py")
shell2http.register_command(endpoint="yale_pixplot", command_name="pixplot")

if __name__ == "__main__":
    print('Starting server...')
    app.run(host='0.0.0.0', debug=True)
