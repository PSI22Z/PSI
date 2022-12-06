FROM python:3.10-alpine
COPY ./server.py /server/
WORKDIR /server
CMD ["python", "server.py"]