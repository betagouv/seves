#!/bin/bash

gunicorn seves.wsgi --bind 127.0.0.1:8000 --log-file - &
exec bin/caddy run --config Caddyfile --adapter caddyfile
