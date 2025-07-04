"""
Shared Oph Client Manager for BVEX Ground Station
Centralized management of the Oph client to prevent race conditions between different widgets trying to control the same client.
"""

import logging
import threading
import time
from typing import Set, Optional
from dataclasses import dataclass
from src.data.Oph_client import OphClient, OphData


@dataclass
class ClientUser:
    """Represents a widget/component that uses the Oph client"""
    name: str
    window: str
    active: bool = False
    
    def __hash__(self):
        # Hash based on immutable fields only
        return hash((self.name, self.window))
    
    def __eq__(self, other):
        # Equality based on name and window only
        if not isinstance(other, ClientUser):
            return False
        return self.name == other.name and self.window == other.window


class SharedOphClientManager:
    """
    Centralized manager for the shared Oph client to prevent conflicts between widgets
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._client: Optional[OphClient] = None
        self._client_lock = threading.Lock()
        self._users: Set[ClientUser] = set()
        self._users_lock = threading.Lock()
        self._last_successful_data_time = None
        self._connection_stable = False
        
        self.logger.info("SharedOphClientManager initialized")
    
    def get_client(self) -> Optional[OphClient]:
        """Get the shared Oph client instance"""
        with self._client_lock:
            if self._client is None:
                self._client = OphClient()
                self._start_client()
            return self._client
    
    def register_user(self, user_name: str, window_name: str) -> ClientUser:
        """Register a new user of the Oph client"""
        user = ClientUser(name=user_name, window=window_name, active=False)
        with self._users_lock:
            # Remove any existing user with the same name/window
            self._users = {u for u in self._users if not (u.name == user_name and u.window == window_name)}
            self._users.add(user)
            
        self.logger.info(f"Registered Oph client user: {window_name}.{user_name}")
        return user
    
    def activate_user(self, user: ClientUser):
        """Activate a user (widget wants to use the client)"""
        with self._users_lock:
            if user in self._users:
                user.active = True
                active_count = sum(1 for u in self._users if u.active)
                self.logger.info(f"Activated user {user.window}.{user.name} - Total active users: {active_count}")
                
                # Ensure client is running and resumed when we have active users
                self._ensure_client_active()
    
    def deactivate_user(self, user: ClientUser):
        """Deactivate a user (widget no longer needs the client)"""
        with self._users_lock:
            if user in self._users:
                user.active = False
                active_count = sum(1 for u in self._users if u.active)
                self.logger.info(f"Deactivated user {user.window}.{user.name} - Total active users: {active_count}")
                
                # Pause client if no users are active
                if active_count == 0:
                    self._pause_client()
    
    def unregister_user(self, user: ClientUser):
        """Unregister a user (widget is being destroyed)"""
        with self._users_lock:
            self._users.discard(user)
            active_count = sum(1 for u in self._users if u.active)
            self.logger.info(f"Unregistered user {user.window}.{user.name} - Remaining users: {len(self._users)}")
            
            # Pause client if no users are active
            if active_count == 0:
                self._pause_client()
    
    def get_data(self) -> OphData:
        """Get data from the client with enhanced error handling"""
        client = self.get_client()
        if not client:
            return OphData()  # Return empty data if no client
        
        try:
            data = client.get_data()
            
            # Track successful data retrieval
            if data.valid:
                self._last_successful_data_time = time.time()
                if not self._connection_stable:
                    self._connection_stable = True
                    self.logger.info("✅ Oph client connection stabilized")
            else:
                # Check if we should consider connection unstable
                if self._last_successful_data_time:
                    time_since_success = time.time() - self._last_successful_data_time
                    if time_since_success > 10.0 and self._connection_stable:  # 10 seconds without valid data
                        self._connection_stable = False
                        self.logger.warning("⚠️ Oph client connection appears unstable")
            
            return data
            
        except Exception as e:
            self.logger.error(f"Error getting data from Oph client: {e}")
            return OphData()
    
    def is_connected(self) -> bool:
        """Check if the client is connected and stable"""
        client = self.get_client()
        if not client:
            return False
        
        # Consider connected if client reports connected AND we've had recent successful data
        basic_connected = client.is_connected()
        
        if self._last_successful_data_time:
            time_since_success = time.time() - self._last_successful_data_time
            recent_success = time_since_success < 15.0  # Within last 15 seconds
            return basic_connected and recent_success
        
        return basic_connected
    
    def get_connection_status(self) -> str:
        """Get detailed connection status string"""
        if not self._client:
            return "Not initialized"
        
        if not self._client.running:
            return "Stopped"
        
        if self._client.is_paused():
            active_users = sum(1 for u in self._users if u.active)
            return f"Paused ({active_users} users waiting)"
        
        if self.is_connected():
            return "Connected"
        elif self._connection_stable:
            return "Connecting..."
        else:
            return "Unstable"
    
    def get_active_users(self) -> list:
        """Get list of currently active users"""
        with self._users_lock:
            return [(u.window, u.name) for u in self._users if u.active]
    
    def get_debug_info(self) -> dict:
        """Get comprehensive debug information"""
        client = self.get_client()
        active_users = self.get_active_users()
        
        return {
            'client_running': client.running if client else False,
            'client_paused': client.is_paused() if client else True,
            'client_valid_data': client.get_data().valid if client else False,
            'total_users': len(self._users),
            'active_users': len(active_users),
            'active_user_list': active_users,
            'connection_stable': self._connection_stable,
            'last_success_ago': time.time() - self._last_successful_data_time if self._last_successful_data_time else None,
            'connection_status': self.get_connection_status(),
            'client_debug': client.get_debug_info() if client else {}
        }
    
    def _start_client(self):
        """Start the Oph client (internal use only)"""
        if self._client and not self._client.running:
            if self._client.start():
                self.logger.info("✅ Shared Oph client started successfully")
                # Start paused - will be resumed when users become active
                self._client.pause()
            else:
                self.logger.error("❌ Failed to start shared Oph client")
    
    def _ensure_client_active(self):
        """Ensure client is running and resumed (internal use only)"""
        if self._client:
            if not self._client.running:
                self._start_client()
            
            if self._client.running and self._client.is_paused():
                self._client.resume()
                self.logger.debug("🔄 Shared Oph client resumed for active users")
    
    def _pause_client(self):
        """Pause the client when no users are active (internal use only)"""
        if self._client and self._client.running and not self._client.is_paused():
            self._client.pause()
            self.logger.debug("⏸️ Shared Oph client paused (no active users)")
    
    def cleanup(self):
        """Clean up the shared client"""
        with self._client_lock:
            with self._users_lock:
                self._users.clear()
            
            if self._client:
                self._client.cleanup()
                self._client = None
                self.logger.info("🧹 Shared Oph client cleaned up")


# Global shared instance
_shared_manager: Optional[SharedOphClientManager] = None
_manager_lock = threading.Lock()


def get_shared_oph_manager() -> SharedOphClientManager:
    """Get the global shared Oph client manager (singleton)"""
    global _shared_manager
    
    with _manager_lock:
        if _shared_manager is None:
            _shared_manager = SharedOphClientManager()
        return _shared_manager


def cleanup_shared_oph_manager():
    """Clean up the global shared manager"""
    global _shared_manager
    
    with _manager_lock:
        if _shared_manager:
            _shared_manager.cleanup()
            _shared_manager = None 