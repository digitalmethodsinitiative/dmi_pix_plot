FROM python:3.7

WORKDIR /usr/src/app

COPY . /usr/src/app/

# flask and flask_shell2http could be rolled into requirements
RUN pip install -r requirements.txt && pip install flask flask_shell2http

CMD ["python", "-m", "flask", "run", "--host", "0.0.0.0", "-p", "4000"]
