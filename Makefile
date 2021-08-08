DIR=$(PWD)

all: build run
build:
	docker build -t clean_survey .
run:
	docker run --rm -v $(DIR)/data:/data clean_survey
