FROM nvidia/cuda:12.1.1-runtime-ubuntu20.04

# Set working directory
WORKDIR /app/

# Install dependencies
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -yq \
    python3 \
    pip

# Install pixplot and additional python libraries
RUN pip install https://github.com/yaledhlab/pix-plot/archive/master.zip &&\
    pip install flask flask_shell2http "gunicorn<21" pyyaml jinja2

# Copy application
COPY . /app/

Expose 4000

# Or Start gunicorn server on startup
CMD ["python3", "-m", "gunicorn", "--worker-tmp-dir", "/dev/shm", "--workers=1", "--threads=4", "--worker-class=gthread", "--log-level=debug", "--access-logfile=gunicorn_access.log", "--reload", "--bind", "0.0.0.0:4000", "app:app"]
