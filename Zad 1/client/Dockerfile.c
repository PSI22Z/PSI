FROM gcc:4.9
COPY ./client.c /client/
WORKDIR /client
RUN gcc -o client client.c -std=c99
ENTRYPOINT ["./client"]