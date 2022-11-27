FROM python:3.10-alpine
COPY ./client.py /client/
WORKDIR /client
ENTRYPOINT ["python", "client.py"]