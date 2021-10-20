import os

from flask import request, jsonify
from werkzeug.utils import secure_filename

from app import app, PLOTS_FOLDER
from functions import process_images, allowed_file


@app.route('/api/list_filenames', methods=['GET'])
def list_filenames():
    """
    Get request to list all filenames in a particular folder
    """
    # Query ?folder_name=your_folder_name
    folder_name = request.args.get('folder_name', None)
    if not folder_name:
        app.logger.warning('No folder_name provided')
        return jsonify({'reason': 'Must provide folder_name as ?folder_name=your_folder_name'}), 400
    else:
        image_folder = os.path.join(app.config['UPLOAD_FOLDER'], folder_name)

        # check if folder exists
        if not os.path.exists(image_folder):
            return jsonify({'reason': 'folder_name %s does not exist' % folder_name}), 400

        files = os.listdir(image_folder)

        return jsonify({
                        'folder_name': folder_name,
                        'filenames': files
                       }), 200


@app.route('/api/send_photo', methods=['POST'])
def upload_photo_api():
    """
    Upload a single photo to a specific folder

    data = {'folder_name': 'desired_name'}
    files = {'image': open('image_1.jpg', 'rb')}
    """
    folder_name = request.form.get('folder_name', None)
    if not folder_name:
        app.logger.warning('No folder_name provided')
        return jsonify({'reason': 'Must provide folder_name for single images'}), 400

    image_folder = os.path.join(app.config['UPLOAD_FOLDER'], folder_name)

    # Make folder if it does not already exist
    if not os.path.isdir(image_folder):
        os.mkdir(image_folder)

    image = request.files.get('image', None)
    if image and allowed_file(image.filename):
        filename = secure_filename(image.filename)
        app.logger.info(f'Uploading {filename} to {folder_name}')
        image.save(os.path.join(image_folder, filename))

        json_data = {'args': ['--images', image_folder + "/*", '--out_dir', PLOTS_FOLDER + '/' + folder_name]}
        response = {
                    'upload_location': request.url_root + 'uploads/' + folder_name,
                    'folder_name': folder_name,
                    'create_pixplot_post_info': {
                        'url': request.url_root + 'api/pixplot',
                        'json': json_data,
                        'images_folder': image_folder,
                        'plot_folder_root': PLOTS_FOLDER,
                        },
                    }
        return response, 200
    else:
        app.logger.warning('No image received')
        return jsonify({'reason': 'No image received'}), 400


@app.route('/api/send_metadata', methods=['POST'])
def upload_metadata_api():
    """
    Upload the metadata.csv file to a specific folder

    data = {'folder_name': 'desired_name'}
    files = {'metadata': open('metadata.csv'), 'rb')}
    """
    folder_name = request.form.get('folder_name', None)
    if not folder_name:
        app.logger.warning('No folder_name provided')
        return jsonify({'reason': 'Must provide folder_name for single images'}), 400

    image_folder = os.path.join(app.config['UPLOAD_FOLDER'], folder_name)

    # Make folder if it does not already exist
    if not os.path.isdir(image_folder):
        os.mkdir(image_folder)

    metadata = request.files.get('metadata', None)
    if metadata and allowed_file(metadata.filename, {'csv'}):
        metadata_file_path = os.path.join(image_folder, 'metadata.csv')
        metadata.save(metadata_file_path)
        json_data = {'args': ['--images', image_folder + "/*", '--out_dir', PLOTS_FOLDER + '/' + folder_name,
                              '--metadata', metadata_file_path]}
        response = {
                    'upload_location': request.url_root + 'uploads/' + folder_name,
                    'folder_name': folder_name,
                    'create_pixplot_post_info': {
                        'url': request.url_root + 'api/pixplot',
                        'json': json_data,
                        'images_folder': image_folder,
                        'plot_folder_root': PLOTS_FOLDER,
                        'metadata_filepath': metadata_file_path,
                        },
                    }
        return response, 200
    else:
        app.logger.warning('No metadata received')
        return jsonify({'reason': 'No metadata received'}), 400


@app.route('/api/send_photos', methods=['POST'])
def upload_photos_api():
    """
    Upload multiple photos (and metadata if provided) to folder.
    If no folder_name provided, a random one will be generated.

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
