run:
```angular2html
docker run -e COLLAB_HOST=https://a7d3-34-90-75-191.ngrok.io -e TOKEN -e HUGGINFACE_KEY -v "$(pwd)":/app --network host tgbot
```
build:
```angular2html
docker build -t tgbot .  
```
before rebuild:
```angular2html
docker rm $(docker ps --filter status=exited -q)
```