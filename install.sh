#!/bin/bash

MODEL="gemma3:1b"
REQUIRED_PYTHON_MODULES=("curses" "subprocess" "textwrap" "threading" "requests" "datetime" "time" "sys")

echo "Checking required Python modules..."

for MODULE in "${REQUIRED_PYTHON_MODULES[@]}"; do
    if ! python3 -c "import $MODULE" &> /dev/null; then
        echo "Installing missing module: $MODULE"
        if [ "$MODULE" == "curses" ]; then
            echo "The 'curses' module is typically pre-installed with Python on Unix systems."
        elif [ "$MODULE" == "datetime" ] || [ "$MODULE" == "time" ] || [ "$MODULE" == "sys" ] || [ "$MODULE" == "threading" ] || [ "$MODULE" == "textwrap" ] || [ "$MODULE" == "subprocess" ]; then
            echo "The '$MODULE' module is part of the Python standard library."
        else
            pip install $MODULE
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
