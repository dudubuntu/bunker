#! /bin/bash

gunicorn main:my_web_app -b 0.0.0.0:8001 --worker-class aiohttp.GunicornWebWorker --reload