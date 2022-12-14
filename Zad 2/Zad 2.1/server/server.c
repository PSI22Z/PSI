#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <arpa/inet.h>
#include <sys/socket.h>

#define BUFLEN 1024
#define PORT 8888

int main(void)
{
    int port, sock, msgsock, client_length, rval, i;
    struct sockaddr_in server_addr, client;
    char *client_addr, buf[BUFLEN];

    sock = socket(AF_INET, SOCK_STREAM, 0);
    if (sock == -1)
    {
        perror("opening stream socket");
        exit(-1);
    }

    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(PORT);
    server_addr.sin_addr.s_addr = htonl(INADDR_ANY);

    if (bind(sock, (struct sockaddr *)&server_addr, sizeof server_addr) == -1)
    {
        perror("binding stream socket");
        exit(-1);
    }

    if (listen(sock, 5) == -1)
    {
        perror("listening");
        exit(-1);
    }

    printf("TCP server up and listening\n");

    while (1)
    {
        printf("Waiting for data...\n");
        client_length = sizeof(client);
        msgsock = accept(sock, (struct sockaddr *)&client, &client_length);
        if (msgsock == -1)
        {
            perror("accept");
        }
        else
        {
            client_addr = inet_ntoa(client.sin_addr);
            printf("Client connected at IP: %s and port: %i\n", client_addr, ntohs(client.sin_port));

            do
            {
                memset(buf, 0, sizeof buf);
                if ((rval = read(msgsock, buf, BUFLEN)) == -1)
                    perror("reading stream message");

                if (rval > 0)
                    printf("Message from client: %s\n", buf);

                if (send(msgsock, buf, strlen(buf), 0) < 0){
                    printf("Can't send\n");
                    return -1;
                }
            } while (rval > 0);
        }

        printf("Ending connection\n");

        if (close(msgsock) == -1)
            perror("closing message socket");
    }

    if (close(sock) == -1)
    {
        perror("closing socket");
        exit(-1);
    }

    return 0;
}
