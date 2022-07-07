import os
import time

import requests
from flask import render_template, request, flash, redirect, url_for, abort
from jinja2 import Markup

from app import app, PLOTS_FOLDER, UPLOAD_FOLDER
from functions import dir_listing, process_images


def url_for_wrapper(path, **kwargs):
    if app.config['SERVER_HTTPS']:
        return url_for(path, _external=True, _scheme='https', **kwargs)
    else:
        return url_for(path, **kwargs)

@app.route('/')
def home():
    return render_template('home.html')


@app.route('/uploads/', defaults={'req_path': ''})
@app.route('/uploads/<path:req_path>')
def uploads(req_path):
    return dir_listing(UPLOAD_FOLDER, req_path, 'images.html')


@app.route('/plots/', defaults={'req_path': ''})
@app.route('/plots/<path:req_path>')
def plots(req_path):
    return dir_listing(PLOTS_FOLDER, req_path, 'plots.html')


@app.route('/upload/', methods=['GET', 'POST'])
def upload_form():
    if request.method == 'POST':
        result_response, status_code = process_images(request)

        if status_code != 200:
            message = 'There was an error uploading photos: ' + str(result_response['reason'])
            flash(message)
            return redirect(url_for_wrapper('upload_form'))
        else:
            return redirect(url_for_wrapper('uploads', req_path=result_response['folder_name']))
    else:
        return render_template('upload_form.html')


@app.route('/create/', methods=['GET', 'POST'])
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
            data = {"args": ['--images', image_location + "/*.jpg", '--out_dir', destination, '--metadata', metadata]}
        else:
            data = {"args": ['--images', image_location + "/*.jpg", '--out_dir', destination]}
        app.logger.debug('Create request data: ' + str(data))

        create_url = request.url_root + "api/pixplot"
        # TODO: use ProxyFix
        create_url = create_url.replace('http://', 'https://')
        app.logger.debug('Create request url: ' + str(create_url))

        response = requests.post(create_url, json=data)
        app.logger.info('Create request status: ' + str(response.status_code))
        app.logger.debug('Create request status: ' + str(response.json()))

        while True:
            time.sleep(10)
            result = requests.get(response.json()['result_url'].replace('http://', 'https://'))
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
        return redirect(url_for_wrapper('create'))

    else:
        return abort(404)
