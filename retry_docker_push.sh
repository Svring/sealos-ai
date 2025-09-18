#!/bin/bash

# Docker push command to retry
DOCKER_COMMAND="docker push crpi-xgxlm7ulopyatpv5.cn-shanghai.personal.cr.aliyuncs.com/hydrangeas/sealos-brain-frontend:v0.4"

# Error pattern to check for
ERROR_PATTERN="write tcp.*broken pipe"

# Counter for attempts
attempt=1

echo "Starting docker push retry script..."
echo "Command: $DOCKER_COMMAND"
echo "Will retry until the 'broken pipe' error no longer appears"
echo "----------------------------------------"

while true; do
    echo "Attempt #$attempt - $(date)"
    
    # Run the docker push command and capture both stdout and stderr
    output=$($DOCKER_COMMAND 2>&1)
    exit_code=$?
    
    # Check if the command was successful (exit code 0)
    if [ $exit_code -eq 0 ]; then
        echo "✅ SUCCESS! Docker push completed successfully on attempt #$attempt"
        echo "Final output:"
        echo "$output"
        break
    fi
    
    # Check if the output contains the specific broken pipe error
    if echo "$output" | grep -q "$ERROR_PATTERN"; then
        echo "❌ Attempt #$attempt failed with broken pipe error. Retrying in 5 seconds..."
        echo "Error output: $output"
        echo "----------------------------------------"
        sleep 5
        ((attempt++))
    else
        echo "❌ Command failed with a different error. Stopping retry loop."
        echo "Exit code: $exit_code"
        echo "Error output: $output"
        exit $exit_code
    fi
done

echo "Docker push retry script completed successfully!"
