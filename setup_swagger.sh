#!/bin/bash
# Download Swagger spec
curl -O https://developers.strava.com/swagger/swagger.json

# Generate client (adjust based on your setup)
swagger-codegen generate -i swagger.json -l python -o ./swagger_client

# Install it
cd swagger_client
pip install -e .
cd ..

echo "Swagger client generated and installed!"