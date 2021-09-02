from flask import Flask, flash, abort, send_file, request, redirect, render_template, Markup, jsonify, url_for
from werkzeug.utils import secure_filename
from flask_executor import Executor
from flask_shell2http import Shell2HTTP
import logging
import requests
import uuid
import os
import time

# Flask application instance
app = Flask(__name__)

# Logging
app.logger.setLevel(logging.DEBUG)
# Log file
logFormatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")
file_handler = logging.FileHandler("pix_plot.log")
file_handler.setFormatter(logFormatter)
app.logger.addHandler(file_handler)

# logging.basicConfig(
#     level=logging.DEBUG,
#     format=f'%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s',
#     handlers=[
#             logging.FileHandler("debug.log"),
#             logging.StreamHandler()
#         ],
#     )

# # Set up logging if run by gunicorn
# if __name__ != '__main__':
#     gunicorn_logger = logging.getLogger('gunicorn.error')
#     app.logger.handlers = gunicorn_logger.handlers
#     app.logger.setLevel(gunicorn_logger.level)

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
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])

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

if __name__ == "__main__":
    print('Starting server...')
    app.run(host='0.0.0.0', debug=True)
