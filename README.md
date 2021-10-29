run:
```angular2html
docker run -e TOKEN --network host tgbot
docker run -e TOKEN -v "$(pwd)":/app --network host tgbot
```
build:
```angular2html
docker build -t tgbot .  
```
before rebuild:
```angular2html
docker rm $(docker ps --filter status=exited -q)
```