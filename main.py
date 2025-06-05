#!/usr/bin/env python3
"""
BVEX Ground Station - Main Entry Point
Balloon-borne VLBI Experiment Ground Station Software

Usage: python main.py
"""

import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.gui.main_window import main

if __name__ == "__main__":
    main() 
 