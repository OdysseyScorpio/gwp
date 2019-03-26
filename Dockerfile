FROM python:3.7

LABEL maintainer="Adam Leyshon <aleyshon@thecodecache.net>"

RUN pip install meinheld gunicorn pipenv

COPY ./docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

COPY ./docker/start.sh /start.sh
RUN chmod +x /start.sh

COPY ./docker/gunicorn_conf.py /gunicorn_conf.py

COPY . /app
WORKDIR /app/

# Overwrite config with suitable one for Docker
COPY ./docker/config.py /app/config.py

ENV PYTHONPATH=/app

RUN pipenv lock -r > requirements.txt && pip install -r requirements.txt

ENTRYPOINT ["/entrypoint.sh"]

# Run the start script, it will check for an /app/prestart.sh script (e.g. for migrations)
# And then will start Gunicorn with Meinheld
CMD ["/start.sh"]
