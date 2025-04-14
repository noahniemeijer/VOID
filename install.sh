#!/bin/bash

MODEL="gemma3:1b"
REQUIRED_PYTHON_MODULES=("curses" "subprocess" "textwrap" "threading" "requests" "datetime" "time" "sys")

PYTHON=$(command -v python3)

echo "Using Python: $PYTHON"
echo "Checking required Python modules..."

for MODULE in "${REQUIRED_PYTHON_MODULES[@]}"; do
    if ! "$PYTHON" -c "import $MODULE" &> /dev/null; then
        echo "Installing missing module: $MODULE"
        if [[ "$MODULE" =~ ^(curses|datetime|time|sys|subprocess|textwrap|threading)$ ]]; then
            echo "The '$MODULE' module is part of the Python standard library."
        else
            "$PYTHON" -m pip install "$MODULE"
        fi
    fi
done

echo "Checking if $MODEL is installed..."

if ollama list | grep -q "$MODEL"; then
    echo "$MODEL is already installed."
else
    echo "$MODEL not found. Pulling model..."
    ollama pull $MODEL
    echo "$MODEL installation complete."
fi
