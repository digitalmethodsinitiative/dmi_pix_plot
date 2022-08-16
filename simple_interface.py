import os
import time

import requests
from flask import render_template, request, flash, redirect, url_for, abort
from jinja2.utils import markupsafe

from app import app, PLOTS_FOLDER, UPLOAD_FOLDER
from functions import dir_listing, process_images
from backend.pix_plot_creater import PixPlotCreater


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

        app.logger.debug('Create request for %s' % form_data['folder_name'])

        create_url = request.url_root + "api/pixplot"
        # TODO: use ProxyFix
        create_url = create_url.replace('http://', 'https://')
        app.logger.debug('Create request url: ' + str(create_url))

        creater = PixPlotCreater(image_location, destination)
        creater.create_new(metadata=True)
        app.logger.info('Creation started for %s' % form_data['folder_name'])

        message = markupsafe.Markup('<a href="/plots/%s/index.html" class="alert-link">Finished! Your PixPlot is uploaded here.</a>' % form_data['folder_name'])
        log_message = 'Creation completed for %s' % form_data['folder_name']
        start = time.time()
        while creater.check_complete():
            time.sleep(10)
            if time.time() - start > 600:
                # Taking a long time
                message = markupsafe.Markup('<a href="/plots/%s/index.html" class="alert-link">Taking longer than 10 minutes; check back later at this link</a>' % form_data['folder_name'])
                log_message = 'Took longer than 10 minutes to create %s' % form_data['folder_name']
                break

        app.logger.info(log_message)
        flash(message)
        return redirect(url_for_wrapper('create'))

    else:
        return abort(404)
