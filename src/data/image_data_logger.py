"""
Image Data Logger for BVEX Ground Station

Handles saving star camera images as JPEG files with metadata tracking.
"""

import os
import time
import threading
import logging
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from pathlib import Path

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    logging.getLogger(__name__).warning("PIL/Pillow not available for image processing")


class ImageDataLogger:
    """Handles saving images with metadata tracking"""
    
    def __init__(self, session_manager, image_type: str = "star_camera"):
        """Initialize image data logger
        
        Args:
            session_manager: SessionManager instance
            image_type: Type of images (e.g., 'star_camera')
        """
        self.logger = logging.getLogger(f"{__name__}.{image_type}")
        self.session_manager = session_manager
        self.image_type = image_type
        
        # Configuration - simplified for BVEX requirements
        self.quality = 100  # Original quality
        self.rate_limit = 1  # Save every image (no skipping)
        self.create_thumbnails = True  # Keep thumbnails for efficiency
        self.thumbnail_size = (320, 240)
        
        # State
        self.is_logging = False
        self.image_count = 0
        self.skipped_count = 0
        self.last_save_time = 0
        self.image_dir = None
        self.thumbnail_dir = None
        
        # Thread safety
        self.lock = threading.Lock()
        
        # Rate limiting
        self.image_counter = 0
        
    def start_logging(self) -> bool:
        """Start image logging"""
        if self.is_logging:
            self.logger.warning(f"{self.image_type} image logging already active")
            return True
            
        try:
            # Get image directory path
            self.image_dir = self.session_manager.get_image_path(self.image_type)
            
            # Create thumbnail directory if needed
            if self.create_thumbnails:
                self.thumbnail_dir = os.path.join(self.image_dir, "thumbnails")
                os.makedirs(self.thumbnail_dir, exist_ok=True)
                
            self.is_logging = True
            self.image_count = 0
            self.skipped_count = 0
            
            self.logger.info(f"Started {self.image_type} image logging to {self.image_dir}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start {self.image_type} image logging: {e}")
            return False
            
    def stop_logging(self) -> None:
        """Stop image logging"""
        if not self.is_logging:
            return
            
        self.is_logging = False
        self.logger.info(
            f"Stopped {self.image_type} image logging - "
            f"Saved {self.image_count} images, skipped {self.skipped_count}"
        )
        
    def save_image(self, image_data: bytes, metadata: Dict[str, Any]) -> Optional[str]:
        """Save an image with metadata
        
        Args:
            image_data: Raw image bytes
            metadata: Dictionary with image metadata
            
        Returns:
            Path to saved image file, or None if skipped/failed
        """
        if not self.is_logging:
            return None
            
        try:
            # Rate limiting
            self.image_counter += 1
            if self.rate_limit > 1 and self.image_counter % self.rate_limit != 0:
                self.skipped_count += 1
                return None
                
            # Check disk space
            if not self._check_disk_space():
                self.logger.warning("Insufficient disk space, skipping image save")
                return None
                
            # Generate filename
            timestamp = datetime.now()
            filename = self.session_manager.get_image_filename(timestamp)
            filepath = os.path.join(self.image_dir, filename)
            
            # Save image
            if PIL_AVAILABLE and image_data:
                # Convert bytes to PIL Image
                from io import BytesIO
                image = Image.open(BytesIO(image_data))
                
                # Ensure RGB mode for JPEG
                if image.mode != 'RGB':
                    image = image.convert('RGB')
                
                # Save with metadata
                image.save(filepath, 'JPEG', quality=self.quality, optimize=True)
                
                # Save thumbnail if enabled
                if self.create_thumbnails:
                    self._create_thumbnail(image, filename)
                
            else:
                # Fallback: save raw bytes
                with open(filepath, 'wb') as f:
                    f.write(image_data)
                
            # Update metadata with file info
            metadata.update({
                'image_filename': filename,
                'image_path': filepath,
                'image_size_bytes': os.path.getsize(filepath),
                'image_width': image.width if PIL_AVAILABLE else 0,
                'image_height': image.height if PIL_AVAILABLE else 0,
                'image_quality': self.quality
            })
            
            with self.lock:
                self.image_count += 1
                self.last_save_time = time.time()
                
            self.logger.debug(f"Saved image: {filename}")
            return filepath
            
        except Exception as e:
            self.logger.error(f"Error saving image: {e}")
            return None
            
    def save_image_from_pil(self, image: Image.Image, metadata: Dict[str, Any]) -> Optional[str]:
        """Save a PIL Image object
        
        Args:
            image: PIL Image object
            metadata: Dictionary with image metadata
            
        Returns:
            Path to saved image file, or None if skipped/failed
        """
        if not self.is_logging:
            return None
            
        try:
            # Rate limiting
            self.image_counter += 1
            if self.rate_limit > 1 and self.image_counter % self.rate_limit != 0:
                self.skipped_count += 1
                return None
                
            # Check disk space
            if not self._check_disk_space():
                self.logger.warning("Insufficient disk space, skipping image save")
                return None
                
            # Generate filename
            timestamp = datetime.now()
            filename = self.session_manager.get_image_filename(timestamp)
            filepath = os.path.join(self.image_dir, filename)
            
            # Ensure RGB mode for JPEG
            if image.mode != 'RGB':
                image = image.convert('RGB')
                
            # Save image
            image.save(filepath, 'JPEG', quality=self.quality, optimize=True)
            
            # Save thumbnail if enabled
            if self.create_thumbnails:
                self._create_thumbnail(image, filename)
                
            # Update metadata
            metadata.update({
                'image_filename': filename,
                'image_path': filepath,
                'image_size_bytes': os.path.getsize(filepath),
                'image_width': image.width,
                'image_height': image.height,
                'image_quality': self.quality
            })
            
            with self.lock:
                self.image_count += 1
                self.last_save_time = time.time()
                
            self.logger.debug(f"Saved PIL image: {filename}")
            return filepath
            
        except Exception as e:
            self.logger.error(f"Error saving PIL image: {e}")
            return None
            
    def _create_thumbnail(self, image: Image.Image, filename: str) -> None:
        """Create thumbnail for an image"""
        try:
            thumbnail = image.copy()
            thumbnail.thumbnail(self.thumbnail_size, Image.Resampling.LANCZOS)
            
            thumb_filename = f"thumb_{filename}"
            thumb_path = os.path.join(self.thumbnail_dir, thumb_filename)
            
            thumbnail.save(thumb_path, 'JPEG', quality=75)
            
        except Exception as e:
            self.logger.error(f"Error creating thumbnail: {e}")
            
    def _check_disk_space(self) -> bool:
        """Check if there's enough disk space"""
        try:
            if not self.image_dir:
                return False
                
            # Get available space
            stat = os.statvfs(self.image_dir)
            available_gb = (stat.f_bavail * stat.f_frsize) / (1024**3)
            
            return available_gb > 1.0  # Require at least 1GB free
            
        except Exception as e:
            self.logger.error(f"Error checking disk space: {e}")
            return True  # Assume OK if we can't check
            
    def configure(self, **kwargs) -> None:
        """Configure image saving parameters
        
        Args:
            quality: JPEG quality (1-100)
            rate_limit: Save every N images
            max_session_size_gb: Maximum session size in GB
            create_thumbnails: Whether to create thumbnails
            thumbnail_size: Tuple of (width, height) for thumbnails
        """
        if 'quality' in kwargs:
            self.quality = max(1, min(100, kwargs['quality']))
        if 'rate_limit' in kwargs:
            self.rate_limit = max(1, kwargs['rate_limit'])
        if 'max_session_size_gb' in kwargs:
            self.max_session_size_gb = kwargs['max_session_size_gb']
        if 'create_thumbnails' in kwargs:
            self.create_thumbnails = bool(kwargs['create_thumbnails'])
        if 'thumbnail_size' in kwargs:
            self.thumbnail_size = tuple(kwargs['thumbnail_size'])
            
    def get_status(self) -> Dict[str, Any]:
        """Get current image logging status
        
        Returns:
            Dictionary with image logging status
        """
        with self.lock:
            return {
                'image_type': self.image_type,
                'is_logging': self.is_logging,
                'image_dir': self.image_dir,
                'image_count': self.image_count,
                'skipped_count': self.skipped_count,
                'total_processed': self.image_count + self.skipped_count,
                'rate_limit': self.rate_limit,
                'quality': self.quality,
                'last_save_time': self.last_save_time
            }
            
    def get_session_size_mb(self) -> float:
        """Get current session image size in MB"""
        if not self.image_dir or not os.path.exists(self.image_dir):
            return 0.0
            
        try:
            total_size = 0
            for filename in os.listdir(self.image_dir):
                if filename.lower().endswith(('.jpg', '.jpeg')):
                    filepath = os.path.join(self.image_dir, filename)
                    if os.path.isfile(filepath):
                        total_size += os.path.getsize(filepath)
                        
            return total_size / (1024 * 1024)
            
        except Exception as e:
            self.logger.error(f"Error calculating session size: {e}")
            return 0.0
            
    def list_images(self) -> list:
        """List all saved images in current session
        
        Returns:
            List of image filenames sorted by name (timestamp)
        """
        if not self.image_dir or not os.path.exists(self.image_dir):
            return []
            
        try:
            images = [f for f in os.listdir(self.image_dir) 
                     if f.lower().endswith(('.jpg', '.jpeg'))]
            images.sort()
            return images
            
        except Exception as e:
            self.logger.error(f"Error listing images: {e}")
            return []