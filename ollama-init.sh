#!/bin/bash

# Start Ollama in the background
ollama serve &

# Wait for Ollama to be ready
sleep 10

# Pull nemotron-70B
ollama pull nemotron:70B

# Keep the container running
wait

