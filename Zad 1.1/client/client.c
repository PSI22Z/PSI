#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <arpa/inet.h>
#include <sys/socket.h>
#include <netdb.h>
#include <netinet/in.h>

#define BUFLEN 1024
#define PORT 8888

int DNSLookUp(char* hostname, char* ip)
{
    struct hostent *H;
    struct in_addr **AddrList;
    if((H = gethostbyname(hostname)) == NULL)
    {
        herror("gethostbyname() error");
        return 1;
    }
    AddrList = (struct in_addr **) H->h_addr_list;
    for (int i = 0; AddrList[i] != NULL; i++)
    {
        strcpy(ip, inet_ntoa(*AddrList[i]));
        return 0;
    }
    return 1;
}

void die(char *s)
{
    perror(s);
    exit(1);
}

int main(int argc, char *argv[])
{
    if (argc > 2) {
        printf("Too many arguments.\n");
        return 1;
    }
    else if (argc == 1) {
        printf("One argument expected.\n");
        return 1;
    }

    struct sockaddr_in si_other;
    int s, i, slen = sizeof(si_other);
    char buf[BUFLEN];
    char message[BUFLEN] = "Hello UDP Server";

    char *hostname = argv[1];
    char ip[100];
    DNSLookUp(hostname, ip);

    if ((s = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP)) == -1)
    {
        die("socket");
    }

    memset((char *)&si_other, 0, sizeof(si_other));
    si_other.sin_family = AF_INET;
    si_other.sin_port = htons(PORT);

    if (inet_aton(ip, &si_other.sin_addr) == 0)
    {
        fprintf(stderr, "inet_aton() failed\n");
        exit(1);
    }

    if (sendto(s, message, strlen(message), 0, (struct sockaddr *)&si_other, slen) == -1)
    {
        die("sendto()");
    }

    // receive a reply and print it
    // clear the buffer by filling null, it might have previously received data
    memset(buf, '\0', BUFLEN);
    // try to receive some data, this is a blocking call
    if (recvfrom(s, buf, BUFLEN, 0, (struct sockaddr *)&si_other, &slen) == -1)
    {
        die("recvfrom()");
    }
    
    printf("Message received from the server: \"%s\"\n", buf);

    close(s);
    return 0;
}