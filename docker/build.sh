#! /usr/bin/bash

pushd ../
uv build --wheel
uv pip freeze |grep -v "kontxt"> docker/requirements.txt

cp dist/*.whl docker/
popd

docker build . -t kontxt-api 

