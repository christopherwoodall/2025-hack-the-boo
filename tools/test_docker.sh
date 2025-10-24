#!/bin/bash

# This script builds a Docker image, runs a container, and attaches a bash session to it.

# Exit immediately if a command exits with a non-zero status (e),
# treat unset variables as an error (u), and pipelines fail on first error (o pipefail).
set -euo pipefail

# --- Configuration ---
IMAGE_BASE_NAME="us-docker.pkg.dev/gemini-code-dev/gemini-cli/sandbox"
DOCKERFILE_PATH=".gemini/sandbox.Dockerfile"
# Get the directory of the script to ensure context is set correctly.
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." &>/dev/null && pwd)


# --- Pre-flight Checks ---
if ! command -v docker &> /dev/null; then
    echo "Error: 'docker' command not found. Please ensure Docker is installed and in your PATH."
    exit 1
fi

if ! command -v gemini &> /dev/null; then
    echo "Error: 'gemini' command not found. Please ensure it is installed and in your PATH."
    exit 1
fi

if [ ! -f "${SCRIPT_DIR}/${DOCKERFILE_PATH}" ]; then
    echo "Error: Dockerfile not found at '${SCRIPT_DIR}/${DOCKERFILE_PATH}'"
    exit 1
fi

# --- Set Dynamic Image Name ---
# Get the version tag from the 'gemini --version' command.
# 'set -e' will cause the script to exit if 'gemini --version' fails.
echo "Fetching image tag from 'gemini --version'..."
IMAGE_TAG=$(gemini --version)

# Additional check in case the command succeeds but returns an empty string
if [ -z "${IMAGE_TAG}" ]; then
    echo "Error: 'gemini --version' returned an empty string. Cannot determine image tag."
    exit 1
fi

# Combine the base name and the dynamic tag
IMAGE_NAME="${IMAGE_BASE_NAME}:${IMAGE_TAG}"


# --- Build ---
echo "Building Docker image: ${IMAGE_NAME}"
echo "Context: ${SCRIPT_DIR}"
if ! docker build -t "${IMAGE_NAME}" -f "${SCRIPT_DIR}/${DOCKERFILE_PATH}" "${SCRIPT_DIR}"; then
    echo "Error: Docker build failed."
    exit 1
fi
echo "Build successful."

# --- Run & Attach ---
echo "Running container and attaching a bash session..."
echo "To exit the container and automatically remove it, simply type 'exit'."
docker run --rm -it "${IMAGE_NAME}" /bin/bash

echo "Container session closed. Script finished."
