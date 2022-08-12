FROM python:3.9-slim

RUN pip install --upgrade pip

WORKDIR /app

COPY . .

RUN pip3 install -r requirements.txt --no-cache-dir

ENTRYPOINT ["python3", "main.py"]
