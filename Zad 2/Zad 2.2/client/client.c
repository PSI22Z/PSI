#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <arpa/inet.h>
#include <sys/socket.h>
#include <netdb.h>
#include <netinet/in.h>

#define BUFLEN 1024
#define PORT 8888

int DNSLookUp(char *hostname, char *ip)
{
    struct hostent *H;
    struct in_addr **AddrList;
    if ((H = gethostbyname(hostname)) == NULL)
    {
        herror("gethostbyname() error");
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
    char client_message[BUFLEN] = "Hello TCP Server";
    char server_message[BUFLEN];
    memset(server_message,'\0',sizeof(server_message));
    
    char *hostname = argv[1];
    char ip[100];
    DNSLookUp(hostname, ip);
    printf("IP %s\n",ip);

    // Create socket:
    socket_desc = socket(AF_INET, SOCK_STREAM, 0);
    
    if(socket_desc < 0){
        printf("Unable to create socket\n");
        return -1;
    }
    
    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(PORT);
    if (inet_aton(ip, &server_addr.sin_addr) == 0)
    {
        fprintf(stderr, "inet_aton() failed\n");
        exit(1);
    }
    
    // Send connection request to server:
    if(connect(socket_desc, (struct sockaddr*)&server_addr, sizeof(server_addr)) < 0){
        printf("Unable to connect\n");
        return -1;
    }
    printf("Connected with server successfully\n");

    for (i = 0; i < 3; i++)
    {
        uint32_t client_message_len = htonl(strlen(client_message));
        if(send(socket_desc, &client_message_len, sizeof(client_message_len), 0) < 0){
            printf("Unable to send message length\n");
            return -1;
        }


        // Send the message to server:
        if(send(socket_desc, client_message, strlen(client_message), 0) < 0){
            printf("Unable to send message\n");
            return -1;
        }
        
        // Receive the server's response:
        if(recv(socket_desc, server_message, sizeof(server_message), 0) < 0){
            printf("Error while receiving server's msg\n");
            return -1;
        }
        
        printf("Server's response: %s\n",server_message);
    }
    
    // Close the socket:
    close(socket_desc);
    
    return 0;
}
