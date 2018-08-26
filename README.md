### Cleaning local docker repository

```bash
docker ps -a | egrep "[Ee]xited" | awk '{print $1}' | xargs -Izz55 docker rm zz55
docker images | sed -E "s/[[:space:]]+/ /g" | awk '{print $3}' | xargs -Izz55 docker rmi zz55
docker volume ls | sed -E "s/[[:space:]]+/ /g" | awk '{print $2}' | xargs -Izz55 docker volume rm zz55
```

### Build
```bash
docker build -t scraper .
```

### Running an interactive shell
```bash
docker run -it scraper /bin/bash
```
#### Run scrapper
```python scrape.py --headless```

#### xvfb (optionally to use but aint working as of today)

#### Test if xvfb works
* ```cd /usr/local/scraper```
* ```python test.py```  

* expected output:
```
display started
Google
display stopped
```

#### Run scrapper with xvfb
```python scrape.py xvfb``` 
