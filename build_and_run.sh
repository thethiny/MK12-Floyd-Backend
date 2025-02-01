sock_path=/var/www/socks
name=mk12apis
image=mk12_floyd

(docker rm -f $name && echo "Stopped running $name") || echo "$name was not up"
docker build -t $image -f sock.Dockerfile .
docker run -it -d \
        --name $name \
        -v `pwd`/secrets.yaml:/app/secrets.yaml \
        -v $sock_path:/app/sock \
        -v `pwd`/db:/app/db \
        --log-opt max-size=1m \
        --log-opt max-file=1 \
        --restart=on-failure \
        $image
docker logs -tf $name

