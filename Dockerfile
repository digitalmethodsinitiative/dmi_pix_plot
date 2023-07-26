FROM nvidia/cuda:12.1.1-runtime-ubuntu20.04

# Install dependencies
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -yq \
    build-essential

# Copy Anaconda3 from existing Docker image
COPY --from=continuumio/anaconda3 /opt/conda /opt/conda

ENV PATH=/opt/conda/bin:$PATH

# Create conda environment
RUN conda update -n base -c defaults conda && \
    conda create -n env python=3.7 && \
    /bin/bash -c conda activate env && \
    conda install cudatoolkit=11 && \
    conda install -c anaconda cudnn && \
    echo "/bin/bash conda activate env" > ~/.bashrc
ENV PATH=/opt/conda/envs/env/bin:$PATH
ENV LD_LIBRARY_PATH=/opt/conda/lib:$LD_LIBRARY_PATH

# Install pixplot itself
RUN python -m pip install python-dev-tools --user --upgrade && \
    python -m pip install https://github.com/yaledhlab/pix-plot/archive/master.zip flask_shell2http flask "gunicorn<21" pyyaml jinja2

# Set working directory
WORKDIR /app/

# Copy application
COPY . /app/

Expose 4000

# Or Start gunicorn server on startup
CMD ["python", "-m", "gunicorn", "--worker-tmp-dir", "/dev/shm", "--workers=1", "--threads=4", "--worker-class=gthread", "--log-level=debug", "--access-logfile=gunicorn_access.log", "--reload", "--bind", "0.0.0.0:4000", "app:app"]
