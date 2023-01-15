FROM python:3.11.1-bullseye

ADD . /filesync

WORKDIR /filesync

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

RUN mkdir "dir_to_sync"

ENTRYPOINT ["python", "main.py", "dir_to_sync", "eth0"]