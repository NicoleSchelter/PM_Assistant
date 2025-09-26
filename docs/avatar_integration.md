# Avatar Integration Guide

This document explains how to integrate and use avatar functionality in the PM Assistant web interface using either D-ID or HeyGen services.

## Overview

The PM Assistant includes an avatar assistant feature that provides an interactive interface for users. The avatar can be configured to use either D-ID or HeyGen services to create realistic talking avatars.

## Configuration

To enable avatar functionality, you need to configure the avatar settings in your `config.yaml` file:

```yaml
avatar:
  # Enable avatar functionality in web interface
  enabled: true
  
  # Avatar service provider: "did" for D-ID, "heygen" for HeyGen
  provider: "did"
  
  # D-ID API settings (if provider is "did")
  did:
    # API key for D-ID service
    api_key: "your-did-api-key-here"
    # Default avatar ID to use
    avatar_id: "default"
    # Voice ID for speech synthesis
    voice_id: "en-US-JennyNeural"
    
  # HeyGen API settings (if provider is "heygen")
  heygen:
    # API key for HeyGen service
    api_key: "your-heygen-api-key-here"
    # Default avatar ID to use
    avatar_id: "default"
    # Voice ID for speech synthesis
    voice_id: "en-US-JennyNeural"
    
  # Default avatar greeting message
  greeting: "Hello! I'm your project management assistant. How can I help you today?"
```

## Obtaining API Keys

### D-ID API Key

1. Visit the [D-ID website](https://www.d-id.com/)
2. Sign up for an account
3. Navigate to the API section
4. Generate an API key
5. Add the API key to your configuration

### HeyGen API Key

1. Visit the [HeyGen website](https://www.heygen.com/)
2. Sign up for an account
3. Navigate to the API dashboard
4. Generate an API key
5. Add the API key to your configuration

## Web Interface Usage

Once configured, the avatar will appear in the right sidebar of the Streamlit web interface. Users can interact with the avatar by typing questions in the text input field.

## Implementation Details

The avatar functionality is implemented in the `service/avatar.py` module, which provides:

- `AvatarService` class for managing avatar functionality
- Support for both D-ID and HeyGen APIs
- Methods for generating avatar HTML
- Methods for making the avatar speak

## Customization

You can customize the avatar appearance and behavior by modifying the configuration values:

- Change the `provider` to switch between D-ID and HeyGen
- Update `avatar_id` to use a specific avatar
- Modify `voice_id` to change the voice
- Update the `greeting` message

## Troubleshooting

If the avatar is not appearing:

1. Check that `enabled` is set to `true`
2. Verify that the API key is correctly configured
3. Ensure that the web interface is properly loading the configuration
4. Check the application logs for any error messages

## Security Considerations

- Keep your API keys secure and do not commit them to version control
- Use environment variables or secure configuration management for production deployments
- Rotate API keys regularly