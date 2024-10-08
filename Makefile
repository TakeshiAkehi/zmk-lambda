
# docker image
build:
	docker build --platform linux/amd64 -t $(IMAGE_NAME_LEFT)  -f Dockerfile.zmk --build-arg IMAGE=$(BASEIMAGE) --build-arg SIDE=left .
	docker build --platform linux/amd64 -t $(IMAGE_NAME_RIGHT) -f Dockerfile.zmk --build-arg IMAGE=$(BASEIMAGE) --build-arg SIDE=right .

build_sudo:
	sudo docker build --platform linux/amd64 -t $(IMAGE_NAME_LEFT)  -f Dockerfile.zmk --build-arg IMAGE=$(BASEIMAGE) --build-arg SIDE=left .
	sudo docker build --platform linux/amd64 -t $(IMAGE_NAME_RIGHT) -f Dockerfile.zmk --build-arg IMAGE=$(BASEIMAGE) --build-arg SIDE=right .

rebuild:
	sudo docker build --platform linux/amd64 -t $(IMAGE_NAME_LEFT)  -f Dockerfile.zmk --build-arg IMAGE=$(BASEIMAGE) --build-arg SIDE=left . --no-cache=true
	sudo docker build --platform linux/amd64 -t $(IMAGE_NAME_RIGHT) -f Dockerfile.zmk --build-arg IMAGE=$(BASEIMAGE) --build-arg SIDE=right . --no-cache=true
	
# zmk debug
run:
	docker run --rm -it $(IMAGE_NAME_LEFT) /bin/bash