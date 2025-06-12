#!/bin/bash

# BVEX Ground Station Setup Script (Unix/macOS/Linux)
# This script creates a virtual environment and installs all dependencies

set -e  # Exit on any error

echo "=========================================="
echo "BVEX Ground Station Setup"
echo "=========================================="

# Function to print colored output
print_green() {
    echo -e "\033[32m$1\033[0m"
}

print_red() {
    echo -e "\033[31m$1\033[0m"
}

print_yellow() {
    echo -e "\033[33m$1\033[0m"
}

# Check if Python 3.8+ is available
if ! command -v python3 &> /dev/null; then
    print_red "Error: Python 3 is not installed or not in PATH"
    echo "Please install Python 3.8 or higher and try again"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c "import sys; print('.'.join(map(str, sys.version_info[:2])))")
echo "Detected Python version: $PYTHON_VERSION"

# Check if version is 3.8 or higher
if python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
    print_green "✓ Python version is compatible"
else
    print_red "Error: Python 3.8 or higher is required"
    echo "Current version: $PYTHON_VERSION"
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "main.py" ]; then
    print_red "Error: main.py not found. Please run this script from the BVEX ground station root directory."
    exit 1
fi

# Create virtual environment
echo "🔧 Creating virtual environment..."
if [ -d "venv" ]; then
    print_yellow "Virtual environment 'venv' already exists"
    read -p "Do you want to recreate it? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Removing existing virtual environment..."
        rm -rf venv
    else
        print_green "Using existing virtual environment"
    fi
fi

if [ ! -d "venv" ]; then
    python3 -m venv venv
    print_green "✓ Virtual environment created successfully"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Verify virtual environment is active
if [[ "$VIRTUAL_ENV" != "" ]]; then
    print_green "✓ Virtual environment activated: $VIRTUAL_ENV"
else
    print_red "Error: Failed to activate virtual environment"
    exit 1
fi

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install wheel to avoid build issues
echo "Installing wheel for better package installation..."
pip install wheel

# Install dependencies
echo "Installing dependencies from requirements.txt..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    print_green "✓ Dependencies installed successfully"
else
    print_red "Error: requirements.txt not found"
    exit 1
fi

# Test import of main modules
echo "Testing imports..."
python3 -c "
try:
    import PyQt6
    import matplotlib
    import numpy
    import astropy
    from PIL import Image
    print('✓ All core dependencies import successfully')
except ImportError as e:
    print(f'⚠ Import error: {e}')
    exit(1)
"

echo ""
print_green "=========================================="
print_green "Setup completed successfully!"
print_green "=========================================="
echo ""
echo "Next steps:"
echo "1. Activate the virtual environment:"
print_yellow "   source venv/bin/activate"
echo ""
echo "2. Run the application:"
print_yellow "   python main.py"
echo ""
echo "3. When done, deactivate the virtual environment:"
print_yellow "   deactivate"
echo ""
print_green "Tip: You can run this setup script again anytime to update dependencies"
echo ""
print_yellow "Note: Make sure you have a display server running if using SSH (X11 forwarding or VNC)"
echo "" 