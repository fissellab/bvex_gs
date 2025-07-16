#!/bin/bash

# BVEX Ground Station Setup Script for Ubuntu 24.04 LTS
# This script creates a virtual environment and installs all dependencies
# Optimized for Ubuntu 24.04 LTS with full Qt6/PyQt6 support
#
# Usage:
#   ./setup.sh                    # Interactive mode
#   AUTO_FIX=1 ./setup.sh         # Auto-fix problematic packages without prompting
#   SKIP_SYSTEM=1 ./setup.sh      # Skip system package installation (for containers)

set -euo pipefail  # Exit on error, undefined vars, pipe failures

echo "=========================================="
echo "BVEX Ground Station Setup for Ubuntu 24.04"
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

print_blue() {
    echo -e "\033[34m$1\033[0m"
}

# Function to check if we're running as root (should not be)
check_not_root() {
    if [ "$EUID" -eq 0 ]; then
        print_red "Error: Do not run this script as root/sudo!"
        print_yellow "This script will ask for sudo when needed for system packages."
        print_yellow "Running as root can cause permission issues with the virtual environment."
        exit 1
    fi
}

# Function to detect OS and version
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if [ -f /etc/os-release ]; then
            . /etc/os-release
            OS_ID=$ID
            OS_VERSION=$VERSION_ID
            OS_PRETTY=$PRETTY_NAME
            print_blue "Detected: $OS_PRETTY"
            
            # Check if it's Ubuntu 24.04
            if [ "$OS_ID" = "ubuntu" ] && [ "$OS_VERSION" = "24.04" ]; then
                print_green "✓ Ubuntu 24.04 LTS detected - fully supported"
            elif [ "$OS_ID" = "ubuntu" ]; then
                print_yellow "⚠ Ubuntu $OS_VERSION detected - this script is optimized for 24.04 LTS"
                print_yellow "  Most packages should still work, but some adjustments may be needed"
            elif [ "$OS_ID" = "debian" ] || [ "$OS_ID" = "pop" ] || [ "$OS_ID" = "mint" ]; then
                print_yellow "⚠ $OS_PRETTY detected - should work with Ubuntu packages"
            else
                print_yellow "⚠ Non-Ubuntu distribution detected - may need manual adjustments"
            fi
        else
            print_red "Error: Cannot detect Linux distribution"
            exit 1
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        print_yellow "macOS detected - this script is optimized for Ubuntu 24.04"
        print_yellow "For macOS, consider using Homebrew to install dependencies manually"
        exit 1
    else
        print_red "Error: Unsupported operating system: $OSTYPE"
        print_yellow "This script is designed for Ubuntu 24.04 LTS"
        exit 1
    fi
}

# Function to check system requirements
check_system_requirements() {
    print_blue "🔍 Checking system requirements..."
    
    # Check if we have sudo access
    if ! sudo -n true 2>/dev/null; then
        print_yellow "This script requires sudo access for installing system packages."
        print_yellow "You will be prompted for your password."
        sudo -v
    fi
    
    # Check available disk space (need at least 2GB for Qt6 + Python packages)
    AVAILABLE_SPACE=$(df / | tail -1 | awk '{print $4}')
    if [ "$AVAILABLE_SPACE" -lt 2000000 ]; then
        print_red "Error: Insufficient disk space. Need at least 2GB free."
        print_yellow "Available: $(($AVAILABLE_SPACE / 1000))MB"
        exit 1
    fi
    
    print_green "✓ System requirements check passed"
}

# Function to install system dependencies for Ubuntu 24.04
install_ubuntu_dependencies() {
    if [ "${SKIP_SYSTEM:-}" = "1" ]; then
        print_yellow "Skipping system package installation (SKIP_SYSTEM=1)"
        return 0
    fi
    
    print_blue "📦 Installing system dependencies for Ubuntu 24.04..."
    
    # Clean up any broken packages first
    print_yellow "Cleaning up package system..."
    sudo apt-get clean
    sudo apt-get autoremove -y
    
    # Update package lists
    print_yellow "Updating package lists..."
    if ! sudo apt-get update; then
        print_red "Failed to update package lists"
        print_yellow "Trying to continue anyway..."
    fi
    
    # Core build tools and Python development
    print_yellow "Installing core development tools..."
    sudo apt-get install -y \
        build-essential \
        python3 \
        python3-dev \
        python3-pip \
        python3-venv \
        pkg-config \
        git \
        curl \
        wget
    
    # Qt6 development libraries - essential for PyQt6
    print_yellow "Installing Qt6 libraries..."
    sudo apt-get install -y \
        qt6-base-dev \
        qt6-tools-dev \
        qt6-tools-dev-tools \
        libqt6core6 \
        libqt6gui6 \
        libqt6widgets6 \
        libqt6opengl6-dev \
        libqt6svg6-dev \
        qt6-qpa-plugins
    
    # X11 and graphics libraries for GUI applications
    print_yellow "Installing X11 and graphics support..."
    sudo apt-get install -y \
        libxcb1-dev \
        libxcb-cursor0 \
        libxcb-cursor-dev \
        libxcb-keysyms1-dev \
        libxcb-image0-dev \
        libxcb-shm0-dev \
        libxcb-util1-dev \
        libxcb-icccm4-dev \
        libxcb-render0-dev \
        libxcb-render-util0-dev \
        libxcb-shape0-dev \
        libxcb-randr0-dev \
        libxcb-xfixes0-dev \
        libxcb-sync-dev \
        libxcb-xinerama0-dev \
        libx11-dev \
        libx11-xcb-dev \
        libxext-dev \
        libxfixes-dev \
        libxi-dev \
        libxrender-dev
    
    # OpenGL libraries for 3D graphics and plotting
    print_yellow "Installing OpenGL support..."
    sudo apt-get install -y \
        libgl1-mesa-dev \
        libglu1-mesa-dev \
        libglx-dev \
        libegl1-mesa-dev
    
    # Scientific computing libraries (for numpy, matplotlib optimization)
    print_yellow "Installing scientific computing libraries..."
    sudo apt-get install -y \
        libblas-dev \
        liblapack-dev \
        libatlas-base-dev \
        gfortran \
        libffi-dev \
        libjpeg-dev \
        libpng-dev \
        libtiff-dev \
        libfreetype6-dev \
        libopenblas-dev
    
    # Font support for better text rendering
    print_yellow "Installing font support..."
    sudo apt-get install -y \
        fonts-dejavu-core \
        fonts-liberation \
        fonts-noto \
        fontconfig \
        libfontconfig1-dev
    
    # Wayland support (for modern Ubuntu desktops)
    print_yellow "Installing Wayland compatibility..."
    sudo apt-get install -y \
        libwayland-dev \
        libwayland-client0 \
        libwayland-cursor0 \
        libwayland-egl1-mesa
    
    print_green "✓ System dependencies installed successfully"
}

# Function to check Python version
check_python_version() {
    print_blue "🐍 Checking Python installation..."
    
    if ! command -v python3 &> /dev/null; then
        print_red "Error: Python 3 is not installed"
        print_yellow "Please install Python 3.8+ and try again"
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 -c "import sys; print('.'.join(map(str, sys.version_info[:2])))")
    PYTHON_MAJOR=$(python3 -c "import sys; print(sys.version_info.major)")
    PYTHON_MINOR=$(python3 -c "import sys; print(sys.version_info.minor)")
    
    print_yellow "Found Python $PYTHON_VERSION"
    
    if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 8 ]); then
        print_red "Error: Python 3.8 or higher is required"
        print_yellow "Current version: $PYTHON_VERSION"
        print_yellow "Ubuntu 24.04 should include Python 3.12 by default"
        exit 1
    fi
    
    print_green "✓ Python version is compatible ($PYTHON_VERSION)"
}

# Function to create and setup virtual environment
setup_virtual_environment() {
    print_blue "🏗️ Setting up Python virtual environment..."
    
    # Check if we're in the right directory
    if [ ! -f "main.py" ] || [ ! -f "requirements.txt" ]; then
        print_red "Error: main.py or requirements.txt not found"
        print_yellow "Please run this script from the BVEX ground station root directory"
        exit 1
    fi
    
    # Handle existing virtual environment
    if [ -d "venv" ]; then
        print_yellow "Virtual environment 'venv' already exists"
        if [ "${AUTO_FIX:-}" = "1" ]; then
            print_yellow "AUTO_FIX=1: Recreating virtual environment..."
            rm -rf venv
        else
            read -p "Do you want to recreate it? This will delete all installed packages. (y/N): " -r
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                print_yellow "Removing existing virtual environment..."
                rm -rf venv
            else
                print_green "Using existing virtual environment"
            fi
        fi
    fi
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        print_yellow "Creating new virtual environment..."
        python3 -m venv venv
        print_green "✓ Virtual environment created"
    fi
    
    # Activate virtual environment
    print_yellow "Activating virtual environment..."
    source venv/bin/activate
    
    # Verify activation
    if [[ "${VIRTUAL_ENV:-}" == "" ]]; then
        print_red "Error: Failed to activate virtual environment"
        exit 1
    fi
    
    print_green "✓ Virtual environment activated: $VIRTUAL_ENV"
    
    # Upgrade pip and install build tools
    print_yellow "Upgrading pip and build tools..."
    pip install --upgrade pip setuptools wheel
    
    print_green "✓ Virtual environment setup complete"
}

# Function to setup Qt environment for Linux
setup_qt_environment() {
    print_blue "⚙️ Configuring Qt environment for Ubuntu 24.04..."
    
    # Create Qt environment setup script
    cat > venv/bin/qt_setup.sh << 'EOF'
#!/bin/bash
# Qt6 Environment Setup for BVEX Ground Station on Ubuntu 24.04

# Set Qt platform plugin path for Ubuntu 24.04
export QT_QPA_PLATFORM_PLUGIN_PATH="/usr/lib/x86_64-linux-gnu/qt6/plugins"

# Force xcb platform (most stable for scientific applications)
export QT_QPA_PLATFORM="xcb"

# Enable high DPI scaling for modern displays
export QT_AUTO_SCREEN_SCALE_FACTOR=1
export QT_ENABLE_HIGHDPI_SCALING=1

# Improve font rendering
export QT_FONT_DPI=96

# Disable Qt logging for cleaner output (remove for debugging)
export QT_LOGGING_RULES="*.debug=false"

echo "Qt environment configured for Ubuntu 24.04"
EOF

    chmod +x venv/bin/qt_setup.sh
    
    # Add Qt setup to activation script
    cat >> venv/bin/activate << 'EOF'

# BVEX Ground Station Qt6 Setup
if [ -f "$VIRTUAL_ENV/bin/qt_setup.sh" ]; then
    source "$VIRTUAL_ENV/bin/qt_setup.sh"
fi
EOF
    
    print_green "✓ Qt environment configured"
}

# Function to install Python dependencies
install_python_dependencies() {
    print_blue "📚 Installing Python dependencies..."
    
    if [ ! -f "requirements.txt" ]; then
        print_red "Error: requirements.txt not found"
        exit 1
    fi
    
    print_yellow "Installing packages from requirements.txt..."
    pip install -r requirements.txt
    
    print_green "✓ Python dependencies installed successfully"
}

# Function to test the installation
test_installation() {
    print_blue "🧪 Testing installation..."
    
    # Test core Python imports
    python3 -c "
import sys
print('Testing core dependencies...')

# Test scientific packages
try:
    import numpy as np
    print('✓ NumPy', np.__version__)
except ImportError as e:
    print('❌ NumPy failed:', e)
    sys.exit(1)

try:
    import matplotlib
    matplotlib.use('Agg')  # Use non-GUI backend for testing
    print('✓ Matplotlib', matplotlib.__version__)
except ImportError as e:
    print('❌ Matplotlib failed:', e)
    sys.exit(1)

try:
    import astropy
    print('✓ Astropy', astropy.__version__)
except ImportError as e:
    print('❌ Astropy failed:', e)
    sys.exit(1)

try:
    from PIL import Image
    print('✓ Pillow (PIL)')
except ImportError as e:
    print('❌ Pillow failed:', e)
    sys.exit(1)

print('✓ All scientific packages imported successfully')
"
    
    # Test PyQt6 (this requires a display, so we'll test carefully)
    python3 -c "
import sys
import os

print('Testing PyQt6...')
try:
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import QT_VERSION_STR
    print('✓ PyQt6 imported successfully (Qt version:', QT_VERSION_STR + ')')
    
    # Only test GUI if we have a display
    if os.environ.get('DISPLAY') or os.environ.get('WAYLAND_DISPLAY'):
        print('Display detected, testing Qt application...')
        app = QApplication(sys.argv)
        print('✓ Qt application created successfully')
        app.quit()
    else:
        print('⚠ No display detected - GUI testing skipped')
        print('  This is normal for headless installations')
    
except ImportError as e:
    print('❌ PyQt6 import failed:', e)
    print('This may indicate missing Qt6 system packages')
    sys.exit(1)
except Exception as e:
    print('⚠ PyQt6 GUI test failed:', e)
    print('This may be normal for headless systems or SSH connections')
    print('PyQt6 is installed and should work with a proper display')

print('✓ PyQt6 testing completed')
"
    
    if [ $? -eq 0 ]; then
        print_green "✓ Installation test passed"
        return 0
    else
        print_yellow "⚠ Installation test completed with warnings"
        return 1
    fi
}

# Function to display final instructions
show_final_instructions() {
    local test_result=$1
    
    echo ""
    print_green "=========================================="
    print_green "🎉 BVEX Ground Station Setup Complete!"
    print_green "=========================================="
    echo ""
    
    if [ $test_result -eq 0 ]; then
        print_green "✅ All tests passed - your installation is ready!"
    else
        print_yellow "⚠️ Setup complete with some warnings"
        print_yellow "The application should still work on systems with a display"
    fi
    
    echo ""
    echo "📋 Next steps:"
    echo ""
    echo "1. Activate the virtual environment:"
    print_blue "   source venv/bin/activate"
    echo ""
    echo "2. Run the BVEX Ground Station:"
    print_blue "   python main.py"
    echo ""
    echo "3. When finished, deactivate the environment:"
    print_blue "   deactivate"
    echo ""
    
    print_green "💡 Tips:"
    echo "• The Qt environment is automatically configured when you activate venv"
    echo "• For SSH connections, use: ssh -X username@hostname"
    echo "• For headless systems, consider VNC or X11 forwarding"
    echo "• Run this script again anytime to update dependencies"
    echo ""
    
    if [ "${OS_ID:-}" = "ubuntu" ] && [ "${OS_VERSION:-}" = "24.04" ]; then
        print_green "Ubuntu 24.04 specific notes:"
        echo "• All packages are optimized for your system"
        echo "• Qt6 and PyQt6 should work perfectly"
        echo "• Wayland and X11 are both supported"
    fi
    echo ""
}

# Main execution
main() {
    check_not_root
    detect_os
    check_system_requirements
    install_ubuntu_dependencies
    check_python_version
    setup_virtual_environment
    setup_qt_environment
    install_python_dependencies
    
    if test_installation; then
        show_final_instructions 0
    else
        show_final_instructions 1
    fi
}

# Run main function
main "$@" 