FROM gcc:4.9
COPY ./server.c /server/
WORKDIR /server
RUN gcc -o server server.c
CMD ["./server"]