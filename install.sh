#!/bin/bash

MODEL="gemma3:1b"

echo "Checking if $MODEL is installed..."

if ollama list | grep -q "$MODEL"; then
    echo "$MODEL is already installed."
else
    echo "$MODEL not found. Pulling model..."
    ollama pull $MODEL
    echo "$MODEL installation complete."
fi
