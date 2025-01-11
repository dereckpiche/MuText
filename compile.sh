#!/bin/bash

# Ensure the script works in the directory it's located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Variables
SCRIPT_NAME="letterlock.py"
APP_NAME="LetterLock"
ICON_NAME="letterlock.icns" # macOS requires .icns files for icons

# Check if PyInstaller is installed
if ! command -v pyinstaller &> /dev/null; then
    echo "PyInstaller is not installed. Installing it now..."
    pip3 install pyinstaller
    if [ $? -ne 0 ]; then
        echo "Error installing PyInstaller. Please check your Python environment."
        exit 1
    fi
fi

# Check if the icon file exists
if [ ! -f "$ICON_NAME" ]; then
    echo "Icon file ($ICON_NAME) not found. Please make sure it's in the same directory."
    exit 1
fi

# Check if the Python script exists
if [ ! -f "$SCRIPT_NAME" ]; then
    echo "Python script ($SCRIPT_NAME) not found. Please make sure it's in the same directory."
    exit 1
fi

# Compile the script using PyInstaller to create a macOS .app bundle
echo "Compiling $SCRIPT_NAME into a macOS .app bundle..."
pyinstaller --windowed --noconfirm --icon="$ICON_NAME" --name="$APP_NAME" "$SCRIPT_NAME"

# Check if the compilation was successful
if [ $? -eq 0 ]; then
    echo "Compilation successful!"
    echo "App bundle created: dist/$APP_NAME.app"
else
    echo "Compilation failed. Check the error messages above."
    exit 1
fi

# Move the app bundle to the script's directory
echo "Moving the .app bundle to the script's directory..."
mv "dist/$APP_NAME.app" "$SCRIPT_DIR/$APP_NAME.app"

# Clean up build files
echo "Cleaning up temporary files..."
rm -rf build __pycache__ "$APP_NAME.spec" dist

echo "Done! Your macOS app bundle is now available as $SCRIPT_DIR/$APP_NAME.app"
