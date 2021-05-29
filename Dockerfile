FROM python:3.9-slim-buster
RUN apt update && apt-get install -y \
    cloc
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt --exists-action=w --disable-pip-version-check --no-cache-dir 2>&1
CMD python bot.py