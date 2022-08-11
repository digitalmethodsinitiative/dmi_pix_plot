import os
import uuid

from flask import jsonify, abort, send_file, render_template
from werkzeug.utils import secure_filename

from app import app, PLOTS_FOLDER, ALLOWED_EXTENSIONS


def process_images(request):
    if 'images' not in request.files or len(request.files.getlist('images')) < 1:
        # No images received
        app.logger.warning('No images received')
        return {'reason': 'No images received'}, 400

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
    if metadata and allowed_file(metadata.filename, {'csv'}):
        metadata_file_path = os.path.join(image_folder, 'metadata.csv')
        metadata.save(metadata_file_path)
        json_data = {'args': ['--images', image_folder + "/*", '--out_dir', PLOTS_FOLDER + '/' + folder_name,
                              '--metadata', metadata_file_path]}
    else:
        json_data = {'args': ['--images', image_folder + "/*", '--out_dir', PLOTS_FOLDER + '/' + folder_name]}

    response = {
                'upload_location': request.url_root + 'uploads/' + folder_name,
                'folder_name': folder_name,
                'create_pixplot_post_info': {
                    'url': request.url_root + 'api/pixplot',
                    'json': json_data,
                    },
                }

    return response, 200


def allowed_file(filename, extensions=ALLOWED_EXTENSIONS):
    """
    Check filenames to ensure they are an allowed extension
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in extensions


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
