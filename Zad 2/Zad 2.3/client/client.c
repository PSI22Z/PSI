#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <sys/socket.h>
#include <arpa/inet.h>
#include <netinet/in.h>
#include <netdb.h>
#include <fcntl.h>
#include <errno.h>
#include <sys/select.h>
#include <unistd.h>

#define PORT 8888
#define BUFF_SIZE 1024

int DNSLookUp(char *hostname, char *ip)
{
    struct hostent *H;
    struct in_addr **AddrList;
    if ((H = gethostbyname(hostname)) == NULL)
    {
        perror("gethostbyname() error");
        return 1;
    }
    AddrList = (struct in_addr **)H->h_addr_list;
    for (int i = 0; AddrList[i] != NULL; i++)
    {
        strcpy(ip, inet_ntoa(*AddrList[i]));
        return 0;
    }
    return 1;
}

int main(int argc, char *argv[])
{
    if (argc > 2)
    {
        printf("Too many arguments.\n");
        return 1;
    }
    else if (argc == 1)
    {
        printf("One argument expected.\n");
        return 1;
    }

    int socket_desc, i;
    struct sockaddr_in server_addr;
    char *hostname, message[BUFF_SIZE];
    hostname = argv[1];
    char ip[100];
    DNSLookUp(hostname, ip);
    printf("IP %s\n", ip);

    // create a non-blocking socket
    if ((socket_desc = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP)) == -1)
    {
        perror("Failed to create socket.");
        return 1;
    }

    // use fnctl() to set the socket to non-blocking
    int flags = fcntl(socket_desc, F_GETFL, 0);
    int status = fcntl(socket_desc, F_SETFL, flags | O_NONBLOCK);

    if (status == -1)
    {
        perror("fcntl failed");
        return 1;
    }

    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(PORT);
    if (inet_aton(ip, &server_addr.sin_addr) == 0)
    {
        perror("inet_aton() failed\n");
        exit(1);
    }

    int connect_result = connect(socket_desc, (struct sockaddr *)&server_addr, sizeof(server_addr));
    if (connect_result < 0)
    {
        if (errno != EINPROGRESS)
        {
            perror("Failed to connect to server.");
            return 1;
        }
    }
    else if (connect_result == 0)
    {
        printf("Connected to %s:%d successfully\n", hostname, PORT);
        goto done;
    }

    // wait for the socket to be ready for writing
    fd_set writefds;
    FD_ZERO(&writefds);
    FD_SET(socket_desc, &writefds);

    struct timeval timeout;
    timeout.tv_sec = 5;
    timeout.tv_usec = 0;
    int select_result = select(socket_desc + 1, (fd_set *)0, &writefds, (fd_set *)0, &timeout);
    if (select_result == -1)
    {
        perror("select failed");
        return 1;
    }
    else if (select_result == 0)
    {
        perror("select timeout");
        return 1;
    }

    // check if the socket is ready for writing
    int so_error;
    socklen_t len = sizeof so_error;
    if (FD_ISSET(socket_desc, &writefds))
    {
        if (getsockopt(socket_desc, SOL_SOCKET, SO_ERROR, &so_error, &len) < 0)
        {
            perror("getsockopt failed");
            return 1;
        }
    }
    else
    {
        perror("neither readfs nor writefds is set");
        return 1;
    }

done:
    printf("Connected to %s:%d successfully\n", hostname, PORT);

    // send 10 messages via TCP, make sure to send all data (like python sendall())
    for (i = 0; i < 10; i++)
    {
        sprintf(message, "Message %d", i + 1);
        if (send(socket_desc, message, strlen(message), 0) < 0)
        {
            perror("Failed to send message.");
            return 1;
        }
        printf("Sent \"%s\" to %s:%d\n", message, hostname, PORT);
    }

    close(socket_desc);
    return 0;
}