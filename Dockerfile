FROM python:3.10-slim-buster
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt --exists-action=w --disable-pip-version-check --no-cache-dir 2>&1
CMD python launcher.py
