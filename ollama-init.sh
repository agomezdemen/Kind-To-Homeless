#!/bin/bash

# Start Ollama in the background
ollama serve &

# Wait for Ollama to be ready
sleep 10

# Pull the nemotron-mini model
ollama pull nemotron-mini

# Keep the container running
wait

