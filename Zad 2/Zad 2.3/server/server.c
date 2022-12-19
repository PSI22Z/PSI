#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <netdb.h>
#include <stdio.h>
#include <arpa/inet.h>
#include <sys/un.h>

#define BUFLEN 1024
#define PORT 8888

#define MAX_FDS 5

#define max(a, b) (((a) > (b)) ? (a) : (b))

int main(void)
{
    int port, sock, msgsock, client_length, rval, i;
    struct sockaddr_in server_addr, client;
    char *client_addr, buf[BUFLEN];
    int descriptors_count, number_active, sockets[MAX_FDS];
    fd_set ready;
    struct timeval timeout;

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
        FD_ZERO(&ready);
        FD_SET(sock, &ready);
        for (i = 0; i < MAX_FDS; i++)
        {
            if (sockets[i] > 0)
            {
                FD_SET(sockets[i], &ready);
            }
        }
        timeout.tv_sec = 10;
        timeout.tv_usec = 0;

        if ((number_active = select(descriptors_count, &ready, (fd_set *)0, (fd_set *)0, &timeout)) == -1)
        {
            perror("select");
            continue;
        }

        if (FD_ISSET(sock, &ready))
        {
            client_length = sizeof(client);
            msgsock = accept(sock, (struct sockaddr *)&client, &client_length);

            if (msgsock == -1)
            {
                perror("accept");
            }
            else if (msgsock >= MAX_FDS)
            {
                printf("Too many clients\n");
                if (close(msgsock) == -1)
                {
                    perror("closing messagesock: too many descriptors");
                }
            }
            else
            {
                descriptors_count = max(descriptors_count, msgsock + 1);
                sockets[msgsock] = msgsock;

                client_addr = inet_ntoa(client.sin_addr);
                printf("Accepted from: %s:%d as %d\n", client_addr, ntohs(client.sin_port), msgsock);
            }
        }

        for (i = 0; i < MAX_FDS; i++)
        {
            if ((msgsock = sockets[i]) > 0 && FD_ISSET(sockets[i], &ready))
            {
                memset(buf, 0, sizeof buf);

                if ((rval = read(msgsock, buf, BUFLEN)) == -1)
                {
                    perror("reading stream message");
                }
                else if (rval > 0)
                {
                    printf("Message from client: %s", buf);
                }
                else if (rval == 0)
                {
                    printf("Ending connection %d\n", msgsock);
                    if (close(msgsock) == -1)
                        perror("closing message socket: ending connection");
                    sockets[msgsock] = -1;
                }
                else
                {
                    printf("- %2d -> ", msgsock);
                    fwrite(buf, 1, rval, stdout);
                    printf("\n");
                }
            }
        }

        if (number_active == 0)
            printf("Timeout...\n");
    }

    if (close(sock) == -1)
    {
        perror("closing socket");
        exit(-1);
    }

    return 0;
}
