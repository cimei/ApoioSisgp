#!/bin/bash
exec gunicorn --config /app/gunicorn_config.py app:app --preload