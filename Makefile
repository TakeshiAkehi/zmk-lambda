# configs
IMAGE_BASENAME=zmk-lambda
TAG=latest
CONTAINER_BASENAME=zmk-lambda
BASEIMAGE=zmkfirmware/zmk-dev-arm:3.5

# configs(.env)
ECR_REPOSITORY=$(shell cat .env | grep -v ^\#  | grep ECR_REPOSITORY= | cut -f 2 -d "=")

# scripts
IMAGE_BASENAME_ZMK=$(IMAGE_BASENAME)
IMAGE_BASENAME_PROD=$(IMAGE_BASENAME)-prod
IMAGE_BASENAME_LOCAL=$(IMAGE_BASENAME)-local
IMAGE_NAME_ZMK=$(IMAGE_BASENAME):$(TAG)
IMAGE_NAME_PROD=$(IMAGE_BASENAME)-prod:$(TAG)
IMAGE_NAME_LOCAL=$(IMAGE_BASENAME)-local:$(TAG)
CONTAINER_NAME_ZMK=$(CONTAINER_BASENAME)
CONTAINER_NAME_LOCAL=$(CONTAINER_BASENAME)-local

# docker image
build:
	docker build --platform linux/amd64 -t $(IMAGE_NAME_ZMK)  -f Dockerfile.zmk --build-arg IMAGE=$(BASEIMAGE) .
	docker build --platform linux/amd64 -t $(IMAGE_NAME_PROD)  -f Dockerfile.prod --build-arg IMAGE=$(IMAGE_NAME_ZMK) .
	docker build --platform linux/amd64 -t $(IMAGE_NAME_LOCAL)  -f Dockerfile.local --build-arg IMAGE=$(IMAGE_NAME_PROD) .

# zmk debug
zmk:
	docker run --rm -it --name $(CONTAINER_NAME_ZMK) $(IMAGE_NAME_ZMK) /bin/bash

fish:
	docker cp ./build_fish.py $(CONTAINER_NAME_ZMK):/zmk-firmware/build_fish.py
	docker exec $(CONTAINER_NAME_ZMK)  /usr/bin/python3 /zmk-firmware/build_fish.py fish

# local lambda debug
local:
	docker run --rm -p 9000:8080 --name $(CONTAINER_NAME_LOCAL) $(IMAGE_NAME_LOCAL)

curl:
	curl -d '{}' http://localhost:9000/2015-03-31/functions/function/invocations

curl2:
	curl -d '{"mode":"test"}' http://localhost:9000/2015-03-31/functions/function/invocations

# prod
push:
	aws ecr get-login-password | docker login --username AWS --password-stdin $(ECR_REPOSITORY)
	docker tag $(IMAGE_NAME_PROD) $(ECR_REPOSITORY):$(TAG)
	docker push $(ECR_REPOSITORY):$(TAG)


dbg:
	docker tag $(IMAGE_NAME_PROD) $(ECR_REPOSITORY)/$(IMAGE_NAME_PROD)