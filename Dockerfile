FROM continuumio/anaconda3

# Create conda environment
RUN conda update -n base -c defaults conda &&\
    conda create -n env python=3.7 &&\
    echo "source activate env" > ~/.bashrc
ENV PATH /opt/conda/envs/env/bin:$PATH

# Set working Dir
WORKDIR /usr/src/app

# Copy application
COPY . /usr/src/app/

# Install pixplot and additional python libraries
RUN pip uninstall pixplot &&\
    pip install https://github.com/yaledhlab/pix-plot/archive/master.zip &&\
    pip install flask flask_shell2http gunicorn

# Start Flask server on startup
# CMD ["python", "-m", "flask", "run", "--host", "0.0.0.0", "-p", "4000"]

# Or Start gunicorn server on startup
CMD ["python", "-m", "gunicorn", "--worker-tmp-dir", "/dev/shm", "--workers=2", "--threads=4", "--worker-class=gthread", "--log-level=debug", "--reload", "--bind", "0.0.0.0:4000", "app:app"]
