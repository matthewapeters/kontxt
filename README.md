# K O N T X T

## Summary

Kontxt "context" is an AI project intended to curate a user's context based on their prompts
so that the agentic LLM's RAG context never overflows.

## Building the Project

This project uses [astral uv, so you should install it as show here](https://docs.astral.sh/uv/getting-started/installation/)

* Create and activate your virtual environment

```shell
cd kontxt
uv venv venv
source venv/bin/activate
```

* Install dependencies

```shell
# installs the packages identified in 
uv pip install .
```

* build the wheel (found in `./dist/`)

```shell
uv build --wheel
```

* build the `kontxt-api` docker image

```shell
cd docker
./build.sh
```

## Running the application

* follow instructions above for creating the kontxt-api docker image

```shell
cd docker_compose
docker compose up
```