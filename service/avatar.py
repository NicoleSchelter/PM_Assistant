"""Avatar service for integrating D-ID or HeyGen avatars in the web interface."""

import base64
import json
import logging
import time
from typing import Dict, Optional

import requests

from utils.logger import get_logger

logger = get_logger(__name__)


class AvatarService:
    """Service for managing avatar functionality with D-ID or HeyGen."""

    def __init__(self, config: Dict):
        """Initialize avatar service with configuration.
        
        Args:
            config: Avatar configuration dictionary
        """
        self.config = config.get("avatar", {})
        self.enabled = self.config.get("enabled", False)
        self.provider = self.config.get("provider", "did")
        self.greeting = self.config.get("greeting", "Hello! How can I help you?")
        
        # Provider-specific configuration
        if self.provider == "did":
            self.did_config = self.config.get("did", {})
            self.api_key = self.did_config.get("dm9ud2FuZGhvZmVuQGdteC5kZQ:v0Z_I3oWP9Odb06hIGJ_K", "")
            self.avatar_id = self.did_config.get("avatar_id", "default")
            self.voice_id = self.did_config.get("voice_id", "en-US-JennyNeural")
        elif self.provider == "heygen":
            self.heygen_config = self.config.get("heygen", {})
            self.api_key = self.heygen_config.get("api_key", "")
            self.avatar_id = self.heygen_config.get("avatar_id", "default")
            self.voice_id = self.heygen_config.get("voice_id", "en-US-JennyNeural")
        
        self.session_id = None

    def is_enabled(self) -> bool:
        """Check if avatar service is enabled and properly configured.
        
        Returns:
            True if avatar service is enabled and configured, False otherwise
        """
        if not self.enabled:
            return False
            
        if not self.api_key or self.api_key == "your-api-key-here":
            logger.warning("Avatar service enabled but API key not configured")
            return False
            
        return True

    def get_avatar_html(self, width: int = 400, height: int = 400) -> str:
        """Generate HTML for displaying the avatar.
        
        Args:
            width: Width of the avatar container
            height: Height of the avatar container
            
        Returns:
            HTML string for embedding the avatar
        """
        if not self.is_enabled():
            return "<p>Avatar service not configured</p>"
            
        if self.provider == "did":
            return self._get_did_avatar_html(width, height)
        elif self.provider == "heygen":
            return self._get_heygen_avatar_html(width, height)
        else:
            return "<p>Unsupported avatar provider</p>"

    def _get_did_avatar_html(self, width: int, height: int) -> str:
        """Generate HTML for D-ID avatar.
        
        Args:
            width: Width of the avatar container
            height: Height of the avatar container
            
        Returns:
            HTML string for embedding the D-ID avatar
        """
        # For D-ID, we would typically use their streaming API
        # This is a placeholder that would need to be implemented with their JavaScript SDK
        return f"""
        <div id="did-avatar-container" style="width: {width}px; height: {height}px; border: 1px solid #ccc; display: flex; align-items: center; justify-content: center;">
            <p>D-ID Avatar Placeholder<br/>(Implementation requires D-ID JavaScript SDK)</p>
        </div>
        <script>
        // D-ID integration would go here
        // This requires their JavaScript SDK and API key
        </script>
        """

    def _get_heygen_avatar_html(self, width: int, height: int) -> str:
        """Generate HTML for HeyGen avatar.
        
        Args:
            width: Width of the avatar container
            height: Height of the avatar container
            
        Returns:
            HTML string for embedding the HeyGen avatar
        """
        # For HeyGen, we would typically use their API to generate videos
        # This is a placeholder that would need to be implemented
        return f"""
        <div id="heygen-avatar-container" style="width: {width}px; height: {height}px; border: 1px solid #ccc; display: flex; align-items: center; justify-content: center;">
            <p>HeyGen Avatar Placeholder<br/>(Implementation requires HeyGen API integration)</p>
        </div>
        """

    def speak(self, text: str) -> Optional[str]:
        """Make the avatar speak the given text.
        
        Args:
            text: Text for the avatar to speak
            
        Returns:
            URL to the generated video/speech or None if failed
        """
        if not self.is_enabled():
            return None
            
        try:
            if self.provider == "did":
                return self._speak_with_did(text)
            elif self.provider == "heygen":
                return self._speak_with_heygen(text)
            else:
                logger.error(f"Unsupported avatar provider: {self.provider}")
                return None
        except Exception as e:
            logger.error(f"Error making avatar speak: {e}")
            return None

    def _speak_with_did(self, text: str) -> Optional[str]:
        """Make the D-ID avatar speak.
        
        Args:
            text: Text for the avatar to speak
            
        Returns:
            URL to the generated video or None if failed
        """
        # D-ID API endpoint for creating videos
        url = "https://api.d-id.com/v1/talks"
        
        # Prepare headers
        auth_string = f"Authorization: Basic {base64.b64encode(f':{self.api_key}'.encode()).decode()}"
        headers = {
            "Authorization": f"Basic {base64.b64encode(f':{self.api_key}'.encode()).decode()}",
            "Content-Type": "application/json"
        }
        
        # Prepare payload
        payload = {
            "script": {
                "type": "text",
                "input": text,
                "subtitles": "false",
                "provider": {
                    "type": "microsoft",
                    "voice_id": self.voice_id
                }
            },
            "config": {
                "fluent": "false",
                "pad_audio": "0.0"
            }
        }
        
        # Add avatar if specified
        if self.avatar_id != "default":
            payload["source_url"] = f"https://api.d-id.com/v1/avatars/{self.avatar_id}"
        
        # Make API request
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 201:
            result = response.json()
            talk_id = result.get("id")
            
            # Wait for video to be generated
            video_url = self._wait_for_did_video(talk_id)
            return video_url
        else:
            logger.error(f"D-ID API error: {response.status_code} - {response.text}")
            return None

    def _wait_for_did_video(self, talk_id: str) -> Optional[str]:
        """Wait for D-ID video to be generated.
        
        Args:
            talk_id: ID of the talk to wait for
            
        Returns:
            URL to the generated video or None if failed
        """
        url = f"https://api.d-id.com/v1/talks/{talk_id}"
        headers = {
            "Authorization": f"Basic {base64.b64encode(f':{self.api_key}'.encode()).decode()}"
        }
        
        # Poll for completion (max 30 seconds)
        for _ in range(30):
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                result = response.json()
                if result.get("status") == "done":
                    return result.get("result_url")
                elif result.get("status") == "error":
                    logger.error(f"D-ID video generation failed: {result.get('error')}")
                    return None
            time.sleep(1)
        
        logger.error("D-ID video generation timed out")
        return None

    def _speak_with_heygen(self, text: str) -> Optional[str]:
        """Make the HeyGen avatar speak.
        
        Args:
            text: Text for the avatar to speak
            
        Returns:
            URL to the generated video or None if failed
        """
        # HeyGen API endpoint for creating videos
        url = "https://api.heygen.com/v1/video.generate"
        
        # Prepare headers
        headers = {
            "X-Api-Key": self.api_key,
            "Content-Type": "application/json"
        }
        
        # Prepare payload
        payload = {
            "avatar_id": self.avatar_id,
            "voice_id": self.voice_id,
            "text": text
        }
        
        # Make API request
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            result = response.json()
            # HeyGen typically returns a video ID that needs to be polled
            video_id = result.get("data", {}).get("video_id")
            if video_id:
                return self._wait_for_heygen_video(video_id)
        
        logger.error(f"HeyGen API error: {response.status_code} - {response.text}")
        return None

    def _wait_for_heygen_video(self, video_id: str) -> Optional[str]:
        """Wait for HeyGen video to be generated.
        
        Args:
            video_id: ID of the video to wait for
            
        Returns:
            URL to the generated video or None if failed
        """
        url = f"https://api.heygen.com/v1/video.get?video_id={video_id}"
        headers = {
            "X-Api-Key": self.api_key
        }
        
        # Poll for completion (max 30 seconds)
        for _ in range(30):
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                result = response.json()
                status = result.get("data", {}).get("status")
                if status == "completed":
                    return result.get("data", {}).get("video_url")
                elif status == "failed":
                    logger.error(f"HeyGen video generation failed")
                    return None
            time.sleep(1)
        
        logger.error("HeyGen video generation timed out")
        return None