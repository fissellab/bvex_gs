"""
Session Manager for BVEX Ground Station Data Logging

Manages timestamped session directories and provides utilities for organizing
log files and images by session.
"""

import os
import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any


class SessionManager:
    """Manages session-based data logging directories"""
    
    def __init__(self, base_dir: str = "data"):
        """Initialize session manager with base directory"""
        self.logger = logging.getLogger(__name__)
        self.base_dir = base_dir
        self.current_session_dir = None
        self.session_metadata = {}
        
        # Ensure base directory exists
        os.makedirs(self.base_dir, exist_ok=True)
        
    def create_session(self, session_name: Optional[str] = None) -> str:
        """Create a new timestamped session directory
        
        Args:
            session_name: Optional custom session name prefix
            
        Returns:
            Path to the created session directory
        """
        # Generate timestamp for session
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        
        if session_name:
            session_dir_name = f"{timestamp}_{session_name}_session"
        else:
            session_dir_name = f"{timestamp}_session"
            
        session_path = os.path.join(self.base_dir, session_dir_name)
        
        try:
            # Create session directory
            os.makedirs(session_path, exist_ok=True)
            
            # Create subdirectories for different data types
            subdirs = [
                "star_camera_images",
                "spectra_data",
                "logs"
            ]
            
            for subdir in subdirs:
                os.makedirs(os.path.join(session_path, subdir), exist_ok=True)
                
            # Create session metadata
            self.session_metadata = {
                "start_time": timestamp,
                "session_name": session_name or "default",
                "data_types": [],
                "total_images": 0,
                "total_csv_files": 0,
                "session_size_mb": 0.0
            }
            
            # Save session metadata
            metadata_path = os.path.join(session_path, "session_metadata.json")
            with open(metadata_path, 'w') as f:
                json.dump(self.session_metadata, f, indent=2)
                
            self.current_session_dir = session_path
            self.logger.info(f"Created new session directory: {session_path}")
            
            return session_path
            
        except Exception as e:
            self.logger.error(f"Failed to create session directory: {e}")
            raise
            
    def get_current_session_path(self) -> Optional[str]:
        """Get the current active session directory"""
        return self.current_session_dir
        
    def get_csv_path(self, data_type: str) -> str:
        """Get path for a specific CSV file
        
        Args:
            data_type: Type of data (e.g., 'gps', 'spectrometer', 'star_camera')
            
        Returns:
            Full path to the CSV file
        """
        if not self.current_session_dir:
            raise RuntimeError("No active session")
            
        filename = f"{data_type}_data.csv"
        return os.path.join(self.current_session_dir, filename)
        
    def get_image_path(self, image_type: str = "star_camera") -> str:
        """Get path for image storage directory
        
        Args:
            image_type: Type of images (e.g., 'star_camera')
            
        Returns:
            Path to the image storage directory
        """
        if not self.current_session_dir:
            raise RuntimeError("No active session")
            
        return os.path.join(self.current_session_dir, f"{image_type}_images")
        
    def get_image_filename(self, timestamp: datetime, extension: str = "jpg") -> str:
        """Generate standardized image filename
        
        Args:
            timestamp: Image timestamp
            extension: File extension (default: 'jpg')
            
        Returns:
            Formatted filename
        """
        return timestamp.strftime(f"%Y-%m-%d_%H-%M-%S_%f")[:-3] + f".{extension}"
        
    def update_session_metadata(self, updates: Dict[str, Any]) -> None:
        """Update session metadata file
        
        Args:
            updates: Dictionary of metadata updates
        """
        if not self.current_session_dir:
            return
            
        try:
            metadata_path = os.path.join(self.current_session_dir, "session_metadata.json")
            
            # Load existing metadata
            if os.path.exists(metadata_path):
                with open(metadata_path, 'r') as f:
                    self.session_metadata = json.load(f)
                    
            # Apply updates
            self.session_metadata.update(updates)
            
            # Save updated metadata
            with open(metadata_path, 'w') as f:
                json.dump(self.session_metadata, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Failed to update session metadata: {e}")
            
    def get_session_stats(self) -> Dict[str, Any]:
        """Get current session statistics
        
        Returns:
            Dictionary with session statistics
        """
        if not self.current_session_dir:
            return {}
            
        try:
            # Calculate directory size
            total_size = 0
            for dirpath, dirnames, filenames in os.walk(self.current_session_dir):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    if os.path.isfile(filepath):
                        total_size += os.path.getsize(filepath)
                        
            stats = {
                "session_path": self.current_session_dir,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "created_files": len(os.listdir(self.current_session_dir))
            }
            
            # Count images if directory exists
            image_path = self.get_image_path("star_camera")
            if os.path.exists(image_path):
                stats["total_images"] = len([f for f in os.listdir(image_path) 
                                           if f.lower().endswith(('.jpg', '.jpeg'))])
            else:
                stats["total_images"] = 0
                
            return stats
            
        except Exception as e:
            self.logger.error(f"Failed to get session stats: {e}")
            return {}
            
    def list_sessions(self) -> list:
        """List all available sessions
        
        Returns:
            List of session directory paths sorted by creation time (newest first)
        """
        try:
            if not os.path.exists(self.base_dir):
                return []
                
            sessions = []
            for item in os.listdir(self.base_dir):
                session_path = os.path.join(self.base_dir, item)
                if os.path.isdir(session_path) and "_session" in item:
                    # Check if it's a valid session with metadata
                    metadata_path = os.path.join(session_path, "session_metadata.json")
                    if os.path.exists(metadata_path):
                        sessions.append(session_path)
                        
            # Sort by modification time (newest first)
            sessions.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            return sessions
            
        except Exception as e:
            self.logger.error(f"Failed to list sessions: {e}")
            return []
            
    def cleanup_old_sessions(self, max_age_days: int = 30) -> int:
        """Clean up old session directories
        
        Args:
            max_age_days: Maximum age in days to keep sessions
            
        Returns:
            Number of sessions cleaned up
        """
        try:
            cutoff_time = datetime.now().timestamp() - (max_age_days * 24 * 3600)
            sessions = self.list_sessions()
            cleaned = 0
            
            for session_path in sessions:
                if os.path.getmtime(session_path) < cutoff_time:
                    import shutil
                    shutil.rmtree(session_path)
                    self.logger.info(f"Cleaned up old session: {session_path}")
                    cleaned += 1
                    
            return cleaned
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup old sessions: {e}")
            return 0