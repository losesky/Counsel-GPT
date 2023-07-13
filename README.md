# Counsel-GPT

docker build -f Dockerfile -t counsel-gpt:latest .

docker run --gpus all -d --name counsel-gpt -p 8080:8080 counsel-gpt:latest

docker exec -it counsel-gpt bash




docker build -t charles94jp/ddns .

docker run -d --name ddns -v <local dir>:/home/NameSilo-DDNS:rw --network host charles94jp/ddns