sock_path=debug_sock
name=mk12apis-debug
image=mk12_floyd:debug

(docker rm -f $name) || echo "$name was not up"
docker build -t $image -f Dockerfile .
docker run -it -d \
        --name $name \
        -v `pwd`/secrets-debug.yaml:/app/secrets.yaml \
        -v $sock_path:/app/sock \
	-v `pwd`/db-dbg:/app/db \
        --log-opt max-size=1m \
        --log-opt max-file=1 \
	-p 23333:8000 \
        $image
docker logs -tf $name

