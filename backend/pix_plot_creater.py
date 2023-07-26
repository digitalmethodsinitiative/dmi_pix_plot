"""
Create a PixPlot via frontend
"""
import os
import datetime
import subprocess
from pathlib import Path

class PixPlotCreater():
    pixplot_command = ['/opt/conda/envs/env/bin/python', '-u', '/app/pixplot/pixplot.py']

    def __init__(self, path_to_images, path_to_plot):
        self.image_path = path_to_images
        self.plot_path = path_to_plot
        self.creation_process = None

        # Create path for plot
        if not os.path.isdir(self.plot_path):
            os.mkdir(self.plot_path)

    def create_new(self, metadata=False):
        command_args = ['--images', self.image_path + "/*.jpg", '--out_dir', self.plot_path,]

        # Check if metadata file exists
        if metadata:
            if os.path.isfile(os.path.join(self.image_path, 'metadata.csv')):
                metadata_file = os.path.join(self.image_path, 'metadata.csv')
                command_args += ['--metadata', metadata_file]

        creation_command = self.pixplot_command + command_args
        with Path(self.plot_path).joinpath('pixplot_creation.log').open("wb") as outfile:
            outfile.write(str.encode("%s: Starting PixPlot Creation\n" % datetime.datetime.now().strftime("%c")))
            self.creation_process = subprocess.Popen(creation_command, stdout=outfile, stderr=outfile)

    def check_complete(self):
        if self.creation_process:
            poll = self.creation_process.poll()
            if poll is None:
                return True
            else:
                return False
        else:
            return None
