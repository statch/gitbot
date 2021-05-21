FROM python:alpine
COPY . /app
CMD pip install -r requirements.txt
WORKDIR /app
CMD python bot.py