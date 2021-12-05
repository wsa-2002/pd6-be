# FROM tiangolo/uvicorn-gunicorn:python3.8

FROM python:3.10

LABEL maintainer="NTUIM PDOGS 6"

RUN pip install --no-cache-dir "uvicorn[standard]" gunicorn

COPY ./docker_script/start.sh /start.sh
RUN chmod +x /start.sh

COPY ./docker_script/gunicorn_conf.py /gunicorn_conf.py

COPY ./docker_script/start-reload.sh /start-reload.sh
RUN chmod +x /start-reload.sh

WORKDIR /app

# Prometheus
# Environment variable is in lower case due to implementation of prometheus-fastapi-instrumentator.
# Can change back to upper case if there is a new fixed version
ENV prometheus_multiproc_dir=/tmp_multiproc
ENV PRE_START_PATH=/app/prestart.sh

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY . .

ENV PYTHONPATH=/app

EXPOSE 80

# Run the start script, it will check for an /app/prestart.sh script (e.g. for migrations)
# And then will start Gunicorn with Uvicorn
CMD ["/start.sh"]
