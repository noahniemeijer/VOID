#!/bin/bash

# --- Configuration ---
MODEL="gemma3:1b"
REQUIRED_PYTHON_MODULES=("curses" "subprocess" "textwrap" "threading" "requests" "datetime" "time" "sys")
EXECUTABLE_NAME="void" # Changed from voidchat to void
TARGET_BIN_DIR="$HOME/bin" # Standard user-specific binary directory

# Get the absolute path to main.py, assuming install.sh is in the same directory as main.py
SCRIPT_PATH="$(pwd)/main.py" 

# Determine the Python executable to use
PYTHON=$(command -v python3)
if [ -z "$PYTHON" ]; then
    echo "Error: python3 not found. Please install Python 3."
    exit 1
fi

# --- 1. Python Module Installation ---
echo "--- Checking Python Modules ---"
for MODULE in "${REQUIRED_PYTHON_MODULES[@]}"; do
    # Check if the module can be imported
    if ! "$PYTHON" -c "import $MODULE" &> /dev/null; then
        echo "Module '$MODULE' not found."
        # Standard library modules (curses, datetime, time, sys, subprocess, textwrap, threading)
        # do not need to be installed via pip. 'requests' is an example of one that might.
        if [[ "$MODULE" =~ ^(curses|datetime|time|sys|subprocess|textwrap|threading)$ ]]; then
            echo "The '$MODULE' module is part of the Python standard library and should be available."
            echo "If you are seeing errors related to this, your Python installation might be corrupted."
        else
            echo "Installing missing module: $MODULE"
            "$PYTHON" -m pip install "$MODULE"
        fi
    else
        echo "Module '$MODULE' is already installed."
    fi
done
echo "--- Python Module Check Complete ---"

# --- 2. Ollama Model Pull ---
echo "--- Checking Ollama Model ---"
# Check if ollama command exists
if ! command -v ollama &> /dev/null; then
    echo "Error: Ollama command not found. Please install Ollama from https://ollama.com."
    exit 1
fi

echo "Checking for Ollama model: $MODEL"
if ! ollama list | grep -q "$MODEL"; then
    echo "Pulling Ollama model: $MODEL. This may take some time..."
    ollama pull "$MODEL"
    if [ $? -ne 0 ]; then
        echo "Error pulling Ollama model. Please check your Ollama installation and internet connection."
        exit 1
    fi
else
    echo "Ollama model $MODEL is already available."
fi
echo "--- Ollama Model Check Complete ---"

# --- 3. Setup Command in PATH ---
echo "--- Setting up '$EXECUTABLE_NAME' command ---"

# Create the target directory if it doesn't exist
if [ ! -d "$TARGET_BIN_DIR" ]; then
    echo "Creating directory: $TARGET_BIN_DIR"
    mkdir -p "$TARGET_BIN_DIR"
fi

# Create a symbolic link to main.py
if [ -L "$TARGET_BIN_DIR/$EXECUTABLE_NAME" ]; then
    echo "Existing symlink '$TARGET_BIN_DIR/$EXECUTABLE_NAME' found, updating it..."
    rm "$TARGET_BIN_DIR/$EXECUTABLE_NAME"
    ln -s "$SCRIPT_PATH" "$TARGET_BIN_DIR/$EXECUTABLE_NAME"
elif [ -f "$TARGET_BIN_DIR/$EXECUTABLE_NAME" ]; then
    echo "Warning: A regular file named '$EXECUTABLE_NAME' already exists in $TARGET_BIN_DIR."
    echo "Please move or remove it manually if you want to create a symlink."
    echo "Skipping symlink creation for '$EXECUTABLE_NAME'."
else
    echo "Creating symlink: $TARGET_BIN_DIR/$EXECUTABLE_NAME -> $SCRIPT_PATH"
    ln -s "$SCRIPT_PATH" "$TARGET_BIN_DIR/$EXECUTABLE_NAME"
fi

# Ensure the original main.py script is executable
if [ -f "$SCRIPT_PATH" ]; then
    chmod +x "$SCRIPT_PATH"
    echo "'$SCRIPT_PATH' set as executable."
else
    echo "Error: 'main.py' not found at '$SCRIPT_PATH'. Cannot make it executable."
fi


# Add $TARGET_BIN_DIR to PATH if not already present
echo "--- Updating PATH ---"
PATH_ADDED=false
SHELL_CONFIG_FILES=("$HOME/.zshrc" "$HOME/.bashrc" "$HOME/.bash_profile" "$HOME/.profile")

for CONFIG_FILE in "${SHELL_CONFIG_FILES[@]}"; do
    if [ -f "$CONFIG_FILE" ]; then
        # Check if the directory is already in PATH with common syntax
        if ! grep -q "export PATH=.*${TARGET_BIN_DIR/\//\\/}:" "$CONFIG_FILE" && \
           ! grep -q "export PATH=.*:${TARGET_BIN_DIR/\//\\/}" "$CONFIG_FILE" && \
           ! grep -q "PATH=.*${TARGET_BIN_DIR/\//\\/}:" "$CONFIG_FILE" && \
           ! grep -q "PATH=.*:${TARGET_BIN_DIR/\//\\/}" "$CONFIG_FILE"; then
            
            echo "Adding '$TARGET_BIN_DIR' to PATH in $CONFIG_FILE..."
            echo -e "\n# Add user's local bin directory to PATH for voidchat" >> "$CONFIG_FILE"
            echo "export PATH=\"$TARGET_BIN_DIR:\$PATH\"" >> "$CONFIG_FILE"
            PATH_ADDED=true
            break
        fi
    fi
done

if [ "$PATH_ADDED" = true ]; then
    echo "PATH updated in your shell configuration file."
    echo ""
    echo "=================================================================="
    echo "  INSTALLATION COMPLETE!"
    echo "  The 'void' command is now set up."
    echo "  Please RESTART your terminal (close and open a new one)"
    echo "  Then, simply type 'void' to start the program."
    echo "=================================================================="
else
    echo "'$TARGET_BIN_DIR' appears to be already in your PATH or a compatible entry exists."
    echo ""
    echo "=================================================================="
    echo "  INSTALLATION COMPLETE!"
    echo "  The 'void' command is now set up."
    echo "  You should be able to run it directly."
    echo "  If not, please RESTART your terminal and try 'void' again."
    echo "=================================================================="
fi

echo "--- Setup Complete ---"
echo "You can now run 'void' from any directory (after restarting your terminal if needed)."
echo "If 'void' doesn't work, try running 'source ~/.bashrc' or 'source ~/.zshrc' based on your shell."