docker build -t z21_22_client_py -f ./client/Dockerfile.py ./client

for ARGUMENT in "$@"
do
   KEY=$(echo $ARGUMENT | cut -f1 -d=)

   KEY_LENGTH=${#KEY}
   VALUE="${ARGUMENT:$KEY_LENGTH+1}"

   export "$KEY"="$VALUE"
done

if [[ -z $server ]]; then
    echo "Argument 'server' is required. Please choose 'c' or 'py'"
    exit
fi

if [ $server == "c" ]; then
    server_dns="z21_22_server_c"
elif [ $server == "py" ]; then
    server_dns="z21_22_server_py"
else
    echo "Wrong 'server' argument. Please choose 'c' or 'py'"
fi

docker run -it --rm --network-alias z21_22_client_py --network z21_network --name z21_22_client_py z21_22_client_py $server_dns