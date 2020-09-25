FROM python:3.8-slim

WORKDIR /app

RUN apt-get update && apt-get install gcc -y

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD [ "python", "-u", "./main.py" ]
