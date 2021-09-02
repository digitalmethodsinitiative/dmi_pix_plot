FROM continuumio/anaconda3

RUN conda update -n base -c defaults conda && conda create -n env python=3.7 && echo "source activate env" > ~/.bashrc
ENV PATH /opt/conda/envs/env/bin:$PATH

WORKDIR /usr/src/app

COPY . /usr/src/app/

# flask and flask_shell2http could be rolled into requirements
RUN pip uninstall pixplot && pip install https://github.com/yaledhlab/pix-plot/archive/master.zip && pip install flask flask_shell2http

CMD ["python", "-m", "flask", "run", "--host", "0.0.0.0", "-p", "4000"]
