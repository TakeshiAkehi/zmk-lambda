# configs
IMAGE_BASENAME=zmk-api
TAG=latest
BASEIMAGE=zmkfirmware/zmk-dev-arm:3.5

# scripts
IMAGE_BASENAME_ZMK=$(IMAGE_BASENAME)
IMAGE_NAME_ZMK=$(IMAGE_BASENAME):$(TAG)
CONTAINER_NAME_ZMK=$(CONTAINER_BASENAME)

# docker image
build:
	docker build --platform linux/amd64 -t $(IMAGE_NAME_ZMK)  -f Dockerfile.zmk --build-arg IMAGE=$(BASEIMAGE) .

# zmk debug
run:
	docker run --rm -it $(IMAGE_NAME_ZMK) /bin/bash
