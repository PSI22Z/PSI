docker build -t z21_23_server_py -f ./server/Dockerfile.py ./server

docker run -it --rm --network-alias z21_23_server_py --network z21_network --name z21_23_server_py z21_23_server_py