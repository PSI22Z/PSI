docker build -t z21_23_server_c -f ./server/Dockerfile.c ./server

docker run -it --rm --network-alias z21_23_server_c --network z21_network --name z21_23_server_c z21_23_server_c