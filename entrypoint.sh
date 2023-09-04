#!/bin/bash
#exec gunicorn --config /app/gunicorn_config.py app:app --reload

set -e

# Function to start Gunicorn with dynamic reload-extra-file options
start_gunicorn() {
    # Generate the reload-extra-file options dynamically
    extra_files=$(find /app -name "*.html" -printf "--reload-extra-file %p ")

    # Start Gunicorn
    echo "Starting Gunicorn..."
    gunicorn --config /app/gunicorn_config.py app:app --reload --reload-engine=poll $extra_files
}

# Start Gunicorn
start_gunicorn
