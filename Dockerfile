FROM python:3.7

WORKDIR /usr/src/app

COPY . /usr/src/app/

RUN pip install -r requirements.txt

RUN pip install flask flask_shell2http


CMD ["python", "-m", "flask", "run", "--host", "0.0.0.0", "-p", "4000"]
