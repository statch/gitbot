FROM python:alpine
COPY . /app
WORKDIR /app
CMD pip install -r requirements.txt
CMD python bot.py