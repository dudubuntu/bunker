#! /bin/bash

gunicorn main:init_app -b 0.0.0.0:8001 --worker-class aiohttp.GunicornWebWorker --reload