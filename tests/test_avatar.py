"""Tests for the avatar service module."""

import pytest
from service.avatar import AvatarService


def test_avatar_service_initialization():
    """Test avatar service initialization with empty config."""
    config = {}
    avatar_service = AvatarService(config)
    
    assert avatar_service is not None
    assert avatar_service.enabled is False
    assert avatar_service.provider == "did"
    assert avatar_service.greeting == "Hello! How can I help you?"


def test_avatar_service_with_config():
    """Test avatar service initialization with config."""
    config = {
        "avatar": {
            "enabled": True,
            "provider": "heygen",
            "greeting": "Welcome!",
            "heygen": {
                "api_key": "test-key",
                "avatar_id": "test-avatar",
                "voice_id": "test-voice"
            }
        }
    }
    
    avatar_service = AvatarService(config)
    
    assert avatar_service.enabled is True
    assert avatar_service.provider == "heygen"
    assert avatar_service.greeting == "Welcome!"
    assert avatar_service.api_key == "test-key"
    assert avatar_service.avatar_id == "test-avatar"
    assert avatar_service.voice_id == "test-voice"


def test_avatar_service_is_enabled():
    """Test avatar service enabled check."""
    # Test with disabled service
    config = {
        "avatar": {
            "enabled": False
        }
    }
    avatar_service = AvatarService(config)
    assert avatar_service.is_enabled() is False
    
    # Test with enabled service but no API key
    config = {
        "avatar": {
            "enabled": True,
            "provider": "did",
            "did": {
                "api_key": ""
            }
        }
    }
    avatar_service = AvatarService(config)
    assert avatar_service.is_enabled() is False
    
    # Test with enabled service and API key
    config = {
        "avatar": {
            "enabled": True,
            "provider": "did",
            "did": {
                "api_key": "test-key"
            }
        }
    }
    avatar_service = AvatarService(config)
    assert avatar_service.is_enabled() is True


def test_get_avatar_html():
    """Test getting avatar HTML."""
    config = {
        "avatar": {
            "enabled": True,
            "provider": "did",
            "did": {
                "api_key": "test-key"
            }
        }
    }
    
    avatar_service = AvatarService(config)
    html = avatar_service.get_avatar_html(300, 300)
    
    assert isinstance(html, str)
    assert len(html) > 0
    assert "did-avatar-container" in html


if __name__ == "__main__":
    pytest.main([__file__])