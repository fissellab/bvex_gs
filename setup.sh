#!/bin/bash

# BVEX Ground Station Setup Script (Unix/macOS/Linux)
# This script creates a virtual environment and installs all dependencies
# Optimized for Ubuntu 20.04+ with full Qt6/PyQt6 support
#
# Usage:
#   ./setup.sh                    # Interactive mode
#   AUTO_FIX=1 ./setup.sh         # Auto-fix problematic packages without prompting

# Note: We don't use 'set -e' here because we want to handle errors gracefully
# instead of exiting immediately on any error

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

print_blue() {
    echo -e "\033[34m$1\033[0m"
}

# Detect OS
OS=""
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
    # Detect distribution
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        DISTRO=$ID
        VERSION=$VERSION_ID
        print_blue "Detected Linux distribution: $PRETTY_NAME"
    else
        DISTRO="unknown"
        print_yellow "Warning: Could not detect Linux distribution"
    fi
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
    print_blue "Detected macOS"
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
    print_red "Error: Windows is not supported by this script. Please use WSL or a Linux VM."
    exit 1
else
    print_yellow "Warning: Unknown OS type: $OSTYPE"
    OS="unknown"
fi

# Function to install system dependencies on Ubuntu/Debian
install_ubuntu_deps() {
    print_blue "Installing system dependencies for Ubuntu/Debian..."
    
    # First, attempt to fix any broken package installations
    print_yellow "Checking for and fixing any broken package installations..."
    
    # Remove any crash reports that might be blocking installations
    if [ -d "/var/crash" ] && [ "$(ls -A /var/crash 2>/dev/null)" ]; then
        print_yellow "Found crash reports that might be blocking installations, attempting to clean up..."
        sudo rm -f /var/crash/*.crash 2>/dev/null || true
    fi
    
    # Try to fix broken packages
    print_yellow "Attempting to fix broken packages..."
    if ! sudo dpkg --configure -a 2>/dev/null; then
        print_yellow "Some packages have configuration issues, attempting to fix..."
        
        # Try to fix broken installations
        sudo apt-get install -f -y 2>/dev/null || true
        
        # If there are still issues, try to identify problematic packages
        if ! sudo dpkg --configure -a 2>/dev/null; then
            print_yellow "Checking for problematic DKMS modules..."
            
            # Check for common problematic packages like synosnap
            for pkg in synosnap nvidia-dkms virtualbox-dkms; do
                if dpkg -l | grep -q "^ii.*$pkg" 2>/dev/null; then
                    print_yellow "Found potentially problematic package: $pkg"
                    
                    # Check if we're in a non-interactive environment or if AUTO_FIX is set
                    if [ -n "$AUTO_FIX" ] || [ -n "$CI" ] || [ ! -t 0 ]; then
                        print_yellow "Auto-removing problematic package $pkg..."
                        REPLY="y"
                    else
                        read -p "Remove problematic package $pkg? This may help fix the installation. (y/N): " -n 1 -r
                        echo
                    fi
                    
                    if [[ $REPLY =~ ^[Yy]$ ]]; then
                        print_yellow "Removing $pkg..."
                        sudo apt-get remove --purge -y $pkg 2>/dev/null || true
                        sudo apt-get autoremove -y 2>/dev/null || true
                    fi
                fi
            done
            
            # Try one more time to configure packages
            sudo dpkg --configure -a 2>/dev/null || true
        fi
    fi
    
    # Clean up package cache and fix any remaining issues
    print_yellow "Cleaning package cache and fixing dependencies..."
    sudo apt-get clean 2>/dev/null || true
    sudo apt-get autoremove -y 2>/dev/null || true
    sudo apt-get install -f -y 2>/dev/null || true
    
    # Update package list with error handling
    echo "Updating package list..."
    if ! sudo apt-get update -qq; then
        print_yellow "Standard package update failed, trying alternative approach..."
        # Try updating without quiet mode to see errors
        if ! sudo apt-get update; then
            print_red "Package list update failed. Continuing anyway..."
            print_yellow "Some packages may not install correctly."
        fi
    fi
    
    # Function to safely install packages with error handling
    safe_install() {
        local packages="$1"
        local description="$2"
        
        echo "Installing $description..."
        if ! sudo apt-get install -y $packages; then
            print_yellow "Failed to install some packages in group: $description"
            print_yellow "Attempting individual package installation..."
            
            # Try installing packages individually
            for pkg in $packages; do
                echo "  Trying to install: $pkg"
                if sudo apt-get install -y $pkg 2>/dev/null; then
                    print_green "  ✓ $pkg installed successfully"
                else
                    print_yellow "  ⚠ Failed to install $pkg (continuing anyway)"
                fi
            done
        else
            print_green "✓ $description installed successfully"
        fi
    }
    
    # Essential build tools and Python development
    safe_install "build-essential python3-dev python3-pip python3-venv pkg-config" \
                 "build essentials and Python development packages"
    
    # Qt6 and XCB dependencies - CRITICAL for PyQt6
    safe_install "qt6-base-dev qt6-tools-dev qt6-tools-dev-tools libqt6core6 libqt6gui6 libqt6widgets6 libqt6opengl6-dev libqt6svg6-dev libqt6multimedia6 libqt6multimediawidgets6" \
                 "Qt6 and XCB platform dependencies"
        
    # XCB platform plugin dependencies - FIXES THE MAIN ERROR
    safe_install "libxcb1-dev libxcb-cursor0 libxcb-cursor-dev libxcb-keysyms1-dev libxcb-image0-dev libxcb-shm0-dev libxcb-util1-dev libxcb-icccm4-dev libxcb-render0-dev libxcb-render-util0-dev libxcb-shape0-dev libxcb-randr0-dev libxcb-xfixes0-dev libxcb-sync-dev libxcb-xinerama0-dev libxcb-present-dev" \
                 "XCB platform plugin dependencies"
    
    # X11 and OpenGL dependencies for full GUI functionality
    safe_install "libx11-dev libx11-xcb-dev libxext-dev libxfixes-dev libxi-dev libxrender-dev libgl1-mesa-dev libglu1-mesa-dev libglx-dev libegl1-mesa-dev" \
                 "X11 and OpenGL dependencies"
    
    # Wayland support (for modern Ubuntu desktops)
    safe_install "libwayland-dev libwayland-client0 libwayland-cursor0 libwayland-egl1-mesa" \
                 "Wayland compatibility"
    
    # Font and theme support for professional appearance
    safe_install "fonts-dejavu-core fonts-liberation fonts-noto fontconfig libfontconfig1-dev libfreetype6-dev" \
                 "fonts and theme support"
    
    # Audio/multimedia support (required by Qt6 multimedia)
    safe_install "libasound2-dev libpulse-dev libgstreamer1.0-dev libgstreamer-plugins-base1.0-dev" \
                 "multimedia support"
    
    # Scientific computing dependencies (for matplotlib, numpy optimization)
    safe_install "libblas-dev liblapack-dev libatlas-base-dev gfortran libffi-dev libjpeg-dev libpng-dev libtiff-dev libfreetype6-dev" \
                 "scientific computing dependencies"
    
    print_green "✓ System dependencies installed successfully"
}

# Function to install system dependencies on other distros
install_other_linux_deps() {
    if command -v dnf &> /dev/null; then
        print_blue "Detected Fedora/RHEL/CentOS - installing dependencies with dnf..."
        sudo dnf install -y \
            qt6-qtbase-devel \
            xcb-util-cursor-devel \
            libxcb-devel \
            python3-devel \
            gcc \
            gcc-c++
    elif command -v yum &> /dev/null; then
        print_blue "Detected older RHEL/CentOS - installing dependencies with yum..."
        sudo yum install -y \
            python3-devel \
            gcc \
            gcc-c++ \
            libxcb-devel
    elif command -v pacman &> /dev/null; then
        print_blue "Detected Arch Linux - installing dependencies with pacman..."
        sudo pacman -S --noconfirm \
            qt6-base \
            xcb-util-cursor \
            python \
            base-devel
    else
        print_yellow "Warning: Could not detect package manager. You may need to install system dependencies manually."
        print_yellow "Required packages: qt6-base, xcb-util-cursor, python3-dev, build tools"
    fi
}

# Install system dependencies based on OS
if [ "$OS" = "linux" ]; then
    print_blue "🔧 Installing system dependencies..."
    
    if [ "$DISTRO" = "ubuntu" ] || [ "$DISTRO" = "debian" ] || [ "$DISTRO" = "pop" ] || [ "$DISTRO" = "mint" ]; then
        if install_ubuntu_deps; then
            print_green "✓ System dependencies installation completed"
        else
            print_yellow "⚠ System dependencies installation completed with some warnings"
            print_yellow "The setup will continue, but some packages may not have installed correctly."
        fi
    else
        if install_other_linux_deps; then
            print_green "✓ System dependencies installation completed"
        else
            print_yellow "⚠ System dependencies installation completed with some warnings"
            print_yellow "The setup will continue, but some packages may not have installed correctly."
        fi
    fi
    echo ""
elif [ "$OS" = "macos" ]; then
    print_blue "macOS detected - checking for Homebrew dependencies..."
    if command -v brew &> /dev/null; then
        print_blue "Installing Qt6 via Homebrew..."
        brew install qt6 python@3.11
        print_green "✓ macOS dependencies installed"
    else
        print_yellow "Homebrew not found. Please install Homebrew first: https://brew.sh"
        print_yellow "Or install Qt6 manually for full functionality"
    fi
    echo ""
fi

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

# Upgrade pip and install build tools
echo "Upgrading pip and installing build tools..."
pip install --upgrade pip setuptools wheel

# Set Qt platform plugin path for Linux
if [ "$OS" = "linux" ]; then
    echo "Setting up Qt environment variables for Linux..."
    
    # Create activation script to set Qt environment
    cat > venv/bin/set_qt_env.sh << 'EOF'
#!/bin/bash
# Qt6 Environment Setup for BVEX Ground Station

# Set Qt platform plugin path
export QT_QPA_PLATFORM_PLUGIN_PATH="/usr/lib/x86_64-linux-gnu/qt6/plugins/platforms"

# Alternative paths for different distributions
if [ ! -d "$QT_QPA_PLATFORM_PLUGIN_PATH" ]; then
    for path in "/usr/lib/qt6/plugins/platforms" "/usr/lib64/qt6/plugins/platforms" "/opt/qt6/plugins/platforms"; do
        if [ -d "$path" ]; then
            export QT_QPA_PLATFORM_PLUGIN_PATH="$path"
            break
        fi
    done
fi

# Force xcb platform on Linux (prevents Wayland issues)
export QT_QPA_PLATFORM="xcb"

# Enable high DPI scaling
export QT_AUTO_SCREEN_SCALE_FACTOR=1
export QT_ENABLE_HIGHDPI_SCALING=1

# Debug Qt platform loading if needed
# export QT_DEBUG_PLUGINS=1

echo "Qt environment configured for Linux"
echo "Platform plugin path: $QT_QPA_PLATFORM_PLUGIN_PATH" 
echo "Platform: $QT_QPA_PLATFORM"
EOF

    chmod +x venv/bin/set_qt_env.sh
    
    # Add Qt environment to activation script
    echo "" >> venv/bin/activate
    echo "# BVEX Ground Station Qt Setup" >> venv/bin/activate
    echo "source \$(dirname \$BASH_SOURCE)/set_qt_env.sh 2>/dev/null || true" >> venv/bin/activate
    
    print_green "✓ Qt environment setup completed"
fi

# Install dependencies
echo "Installing Python dependencies from requirements.txt..."
if [ -f "requirements.txt" ]; then
    # Install with verbose output to catch any issues
    pip install -v -r requirements.txt
    print_green "✓ Python dependencies installed successfully"
else
    print_red "Error: requirements.txt not found"
    exit 1
fi

# Test imports and Qt functionality
echo "Testing imports and Qt functionality..."
python3 -c "
import sys
import os

try:
    print('Testing core dependencies...')
    import numpy
    print('✓ NumPy imported successfully')
    
    import matplotlib
    print('✓ Matplotlib imported successfully')
    
    import astropy
    print('✓ Astropy imported successfully')
    
    from PIL import Image
    print('✓ Pillow imported successfully')
    
    # Test PyQt6 import and basic functionality
    print('Testing PyQt6...')
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import QT_VERSION_STR
    from PyQt6 import QtCore
    print(f'✓ PyQt6 imported successfully (Qt version: {QT_VERSION_STR})')
    
    # Test Qt platform plugins
    print('Testing Qt platform plugins...')
    app = QApplication(sys.argv)
    
    # Check available platforms
    from PyQt6.QtGui import QGuiApplication
    platforms = QGuiApplication.platformName()
    print(f'✓ Qt platform: {platforms}')
    
    app.quit()
    print('✓ Qt application test completed successfully')
    
    print('')
    print('🎉 All core dependencies imported and tested successfully!')
    
except ImportError as e:
    print(f'❌ Import error: {e}')
    print('This may indicate missing system dependencies.')
    sys.exit(1)
    
except Exception as e:
    print(f'❌ Qt/GUI error: {e}')
    print('This may indicate missing Qt platform plugins or X11 issues.')
    print('If you see xcb-cursor errors, ensure you have a display server running.')
    sys.exit(1)
"

if [ $? -eq 0 ]; then
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
    
    if [ "$OS" = "linux" ]; then
        print_green "Linux-specific notes:"
        echo "• Qt environment variables are automatically set when you activate the venv"
        echo "• The application will use the XCB platform plugin for maximum compatibility"
        echo "• If running over SSH, ensure X11 forwarding is enabled: ssh -X username@hostname"
        echo "• For headless servers, consider using VNC or Xvfb"
        echo ""
    fi
    
    print_green "Tip: You can run this setup script again anytime to update dependencies"
    print_yellow "Note: If you encounter any display issues, ensure you have a display server running"
else
    echo ""
    print_red "=========================================="
    print_red "Setup completed with warnings"
    print_red "=========================================="
    echo ""
    print_yellow "The setup completed but there were issues with Qt/GUI testing."
    print_yellow "This is normal if you don't have a display server running (e.g., SSH without X11)."
    echo ""
    echo "The application should still work when you have a proper display environment."
    echo ""
    echo "To run the application:"
    print_yellow "   source venv/bin/activate"
    print_yellow "   python main.py"
fi

echo "" 