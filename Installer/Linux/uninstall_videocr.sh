#!/bin/bash

DESKTOP_FILE="$HOME/.local/share/applications/VideOCRplus.desktop"
CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/VideOCRplus"
LOG_DIR="${XDG_STATE_HOME:-$HOME/.local/state}/VideOCRplus"

if [ -f "$DESKTOP_FILE" ]; then
    echo "Removing desktop shortcut..."
    rm "$DESKTOP_FILE"
    update-desktop-database ~/.local/share/applications 2>/dev/null
    echo "Desktop entry removed."
else
    echo "Desktop shortcut not found."
fi

# Check if either the config or log directory exists, and ask the user
if [ -d "$CONFIG_DIR" ] || [ -d "$LOG_DIR" ]; then
    read -p "Do you also want to delete your VideOCRplus settings and log files? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf "$CONFIG_DIR"
        rm -rf "$LOG_DIR"
        echo "Configuration and logs successfully removed."
    else
        echo "Configuration kept at $CONFIG_DIR"
        echo "Logs kept at $LOG_DIR"
    fi
fi

echo "--------------------------------------------------------"
echo "You can now safely delete the VideOCRplus folder from your system if no longer needed."
