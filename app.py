from flask import Flask, flash, abort, send_file, request, redirect, render_template, Markup
from werkzeug.utils import secure_filename
from flask_executor import Executor
from flask_shell2http import Shell2HTTP
import os

# Flask application instance
app = Flask(__name__)

# Set upload folder
path = os.getcwd()
UPLOAD_FOLDER = os.path.join(path, 'uploads')
# Make dir if does not exist
if not os.path.isdir(UPLOAD_FOLDER):
    os.mkdir(UPLOAD_FOLDER)

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
@app.route('/uploads/', defaults={'req_path': ''})
@app.route('/uploads/<path:req_path>')
def dir_listing(req_path):
    # Joining the upload folder and the requested path
    abs_path = os.path.join(UPLOAD_FOLDER, req_path)

    # Return 404 if path doesn't exist
    if not os.path.exists(abs_path):
        return abort(404)

    # Check if path is a file and serve
    if os.path.isfile(abs_path):
        return send_file(abs_path)

    # Show directory contents
    files = os.listdir(abs_path)
    return render_template('files.html', files=files)

# Interactive upload
@app.route('/upload/')
def upload_form():
    return render_template('upload.html')

# Post uploads
@app.route('/upload/', methods=['POST'])
def upload_file():
    if request.method == 'POST':

        form_data = request.form
        if form_data['folder_name']:
            folder = os.path.join(app.config['UPLOAD_FOLDER'], form_data['folder_name'])
            if not os.path.isdir(folder):
                os.mkdir(folder)
        else:
            folder = app.config['UPLOAD_FOLDER']

        if 'files[]' not in request.files:
            flash('No images selected')
            return redirect(request.url)

        files = request.files.getlist('files[]')

        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(folder, filename))

        metadata = request.files.get('metadata', None)
        if metadata and allowed_file(metadata.filename, set(['csv'])):
            filename = secure_filename(metadata.filename)
            metadata.save(os.path.join(folder, filename))

        url_reference = '<a href="/uploads/%s" class="alert-link">Image(s) successfully uploaded here</a>' % form_data['folder_name']
        flash(Markup(url_reference))
        return redirect('/upload/')


# API
executor = Executor(app)
shell2http = Shell2HTTP(app=app, executor=executor, base_url_prefix="/api/")

shell2http.register_command(endpoint="pixplot", command_name="python /usr/src/app/pixplot/pixplot.py")

if __name__ == "__main__":
	print('Starting server...')
	app.run(host='0.0.0.0', debug=True)
