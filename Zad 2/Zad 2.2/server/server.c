#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <arpa/inet.h>
#include <sys/socket.h>

#define BUFLEN 2
#define INTEGER_LEN 4
#define PORT 8888

int main(void)
{
    int port, sock, msgsock, client_length, rval, i;
    struct sockaddr_in server_addr, client;
    char *client_addr, buf[BUFLEN], message_length[INTEGER_LEN], message[1024];

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
                
                if ((rval = read(msgsock, &message_length, INTEGER_LEN)) == -1)
                    perror("reading stream message length");
                if (rval > 0) {
                    memset(message, 0, sizeof message);
                    uint32_t message_len = ntohl(*((uint32_t *)message_length));
                    printf("receiving message of length %i:\n", message_len);
                    while (message_len > 0) {
                        memset(buf, 0, sizeof buf);
                        if ((rval = read(msgsock, buf, BUFLEN)) == -1)
                            perror("reading stream message");    
                        if (rval > 0) {
                            message_len -= rval;
                            char buff_with_null[BUFLEN + 1];
                            memcpy(buff_with_null, buf, BUFLEN);
                            buff_with_null[BUFLEN] = '\0';
                            strcat(message, buff_with_null);
                        }
                    }
                    printf("Message from client: %s\n", message);
                }
                if (send(msgsock, message, strlen(message), 0) < 0){
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
