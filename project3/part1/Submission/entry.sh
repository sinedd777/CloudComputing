#!/bin/sh
# Check if running in Lambda environment
if [ -z "$AWS_LAMBDA_RUNTIME_API" ]; then
    exec /usr/bin/aws-lambda-rie /usr/local/bin/python -m awslambdaric "$@"
else
    exec /usr/local/bin/python -m awslambdaric "$@"
fi
