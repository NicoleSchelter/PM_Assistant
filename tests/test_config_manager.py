"""Unit tests for ConfigManager class."""

import pytest
import yaml
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, mock_open

from core.config_manager import ConfigManager
from utils.exceptions import ConfigurationError


class TestConfigManager:
    """Test cases for ConfigManager class."""
    
    def test_init_default_config_path(self):
        """Test ConfigManager initialization with default config path."""
        config_manager = ConfigManager()
        assert config_manager.config_path == "config.yaml"
        assert config_manager.config_data == {}
        
    def test_init_custom_config_path(self):
        """Test ConfigManager initialization with custom config path."""
        custom_path = "custom_config.yaml"
        config_manager = ConfigManager(custom_path)
        assert config_manager.config_path == custom_path
        
    def test_load_config_success(self):
        """Test successful configuration loading."""
        valid_config = {
            "project": {
                "name": "Test Project",
                "default_path": "./test_path"
            },
            "required_documents": [
                {
                    "name": "Test Doc",
                    "patterns": ["*test*"],
                    "formats": ["md"],
                    "required": True
                }
            ],
            "modes": {
                "document_check": {"enabled": True},
                "status_analysis": {"enabled": True},
                "learning_module": {"enabled": True}
            },
            "output": {
                "directory": "./reports"
            },
            "logging": {
                "level": "INFO"
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(valid_config, f)
            temp_path = f.name
            
        try:
            config_manager = ConfigManager(temp_path)
            loaded_config = config_manager.load_config()
            
            assert loaded_config == valid_config
            assert config_manager.config_data == valid_config
        finally:
            os.unlink(temp_path)
            
    def test_load_config_file_not_found_creates_default(self):
        """Test that missing config file triggers default config creation."""
        non_existent_path = "non_existent_config.yaml"
        
        # Ensure file doesn't exist
        if os.path.exists(non_existent_path):
            os.unlink(non_existent_path)
            
        try:
            config_manager = ConfigManager(non_existent_path)
            loaded_config = config_manager.load_config()
            
            # Check that file was created
            assert os.path.exists(non_existent_path)
            
            # Check that config contains required sections
            assert "project" in loaded_config
            assert "required_documents" in loaded_config
            assert "modes" in loaded_config
            assert "output" in loaded_config
            assert "logging" in loaded_config
            
        finally:
            if os.path.exists(non_existent_path):
                os.unlink(non_existent_path)
                
    def test_load_config_invalid_yaml(self):
        """Test handling of invalid YAML syntax."""
        invalid_yaml = "invalid: yaml: content: ["
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(invalid_yaml)
            temp_path = f.name
            
        try:
            config_manager = ConfigManager(temp_path)
            with pytest.raises(ConfigurationError, match="Invalid YAML"):
                config_manager.load_config()
        finally:
            os.unlink(temp_path)
            
    def test_validate_config_missing_sections(self):
        """Test validation failure when required sections are missing."""
        incomplete_config = {
            "project": {
                "name": "Test",
                "default_path": "./test"
            }
            # Missing other required sections
        }
        
        config_manager = ConfigManager()
        config_manager.config_data = incomplete_config
        
        with pytest.raises(ConfigurationError, match="Missing required configuration sections"):
            config_manager._validate_config()
            
    def test_validate_config_missing_project_fields(self):
        """Test validation failure when project fields are missing."""
        config_with_incomplete_project = {
            "project": {
                "name": "Test"
                # Missing default_path
            },
            "required_documents": [],
            "modes": {
                "document_check": {"enabled": True},
                "status_analysis": {"enabled": True},
                "learning_module": {"enabled": True}
            },
            "output": {"directory": "./reports"},
            "logging": {"level": "INFO"}
        }
        
        config_manager = ConfigManager()
        config_manager.config_data = config_with_incomplete_project
        
        with pytest.raises(ConfigurationError, match="Missing required project fields"):
            config_manager._validate_config()
            
    def test_validate_config_missing_mode_fields(self):
        """Test validation failure when mode configurations are missing."""
        config_with_incomplete_modes = {
            "project": {
                "name": "Test",
                "default_path": "./test"
            },
            "required_documents": [],
            "modes": {
                "document_check": {"enabled": True}
                # Missing other modes
            },
            "output": {"directory": "./reports"},
            "logging": {"level": "INFO"}
        }
        
        config_manager = ConfigManager()
        config_manager.config_data = config_with_incomplete_modes
        
        with pytest.raises(ConfigurationError, match="Missing required mode configurations"):
            config_manager._validate_config()
            
    def test_validate_required_documents_invalid_structure(self):
        """Test validation of required_documents structure."""
        config_with_invalid_docs = {
            "project": {
                "name": "Test",
                "default_path": "./test"
            },
            "required_documents": [
                {
                    "name": "Test Doc"
                    # Missing required fields
                }
            ],
            "modes": {
                "document_check": {"enabled": True},
                "status_analysis": {"enabled": True},
                "learning_module": {"enabled": True}
            },
            "output": {"directory": "./reports"},
            "logging": {"level": "INFO"}
        }
        
        config_manager = ConfigManager()
        config_manager.config_data = config_with_invalid_docs
        
        with pytest.raises(ConfigurationError, match="missing required fields"):
            config_manager._validate_config()
            
    def test_validate_required_documents_invalid_types(self):
        """Test validation of required_documents field types."""
        config_with_invalid_types = {
            "project": {
                "name": "Test",
                "default_path": "./test"
            },
            "required_documents": [
                {
                    "name": "Test Doc",
                    "patterns": "not_a_list",  # Should be list
                    "formats": ["md"],
                    "required": True
                }
            ],
            "modes": {
                "document_check": {"enabled": True},
                "status_analysis": {"enabled": True},
                "learning_module": {"enabled": True}
            },
            "output": {"directory": "./reports"},
            "logging": {"level": "INFO"}
        }
        
        config_manager = ConfigManager()
        config_manager.config_data = config_with_invalid_types
        
        with pytest.raises(ConfigurationError, match="patterns must be a list"):
            config_manager._validate_config()
            
    def test_get_project_config(self):
        """Test getting project configuration section."""
        config_manager = ConfigManager()
        config_manager.config_data = {
            "project": {
                "name": "Test Project",
                "default_path": "./test"
            }
        }
        
        project_config = config_manager.get_project_config()
        assert project_config["name"] == "Test Project"
        assert project_config["default_path"] == "./test"
        
    def test_get_required_documents(self):
        """Test getting required documents configuration."""
        config_manager = ConfigManager()
        test_docs = [
            {
                "name": "Test Doc",
                "patterns": ["*test*"],
                "formats": ["md"],
                "required": True
            }
        ]
        config_manager.config_data = {"required_documents": test_docs}
        
        required_docs = config_manager.get_required_documents()
        assert required_docs == test_docs
        
    def test_get_modes_config(self):
        """Test getting modes configuration."""
        config_manager = ConfigManager()
        test_modes = {
            "document_check": {"enabled": True},
            "status_analysis": {"enabled": False}
        }
        config_manager.config_data = {"modes": test_modes}
        
        modes_config = config_manager.get_modes_config()
        assert modes_config == test_modes
        
    def test_get_output_config(self):
        """Test getting output configuration."""
        config_manager = ConfigManager()
        test_output = {"directory": "./test_reports"}
        config_manager.config_data = {"output": test_output}
        
        output_config = config_manager.get_output_config()
        assert output_config == test_output
        
    def test_get_logging_config(self):
        """Test getting logging configuration."""
        config_manager = ConfigManager()
        test_logging = {"level": "DEBUG", "file": "test.log"}
        config_manager.config_data = {"logging": test_logging}
        
        logging_config = config_manager.get_logging_config()
        assert logging_config == test_logging
        
    def test_get_project_path(self):
        """Test getting project path from configuration."""
        config_manager = ConfigManager()
        config_manager.config_data = {
            "project": {"default_path": "./custom_path"}
        }
        
        project_path = config_manager.get_project_path()
        assert project_path == "./custom_path"
        
    def test_get_project_path_default(self):
        """Test getting default project path when not configured."""
        config_manager = ConfigManager()
        config_manager.config_data = {"project": {}}
        
        project_path = config_manager.get_project_path()
        assert project_path == "./project_files"
        
    def test_is_mode_enabled_true(self):
        """Test checking if mode is enabled when it is."""
        config_manager = ConfigManager()
        config_manager.config_data = {
            "modes": {
                "document_check": {"enabled": True}
            }
        }
        
        assert config_manager.is_mode_enabled("document_check") is True
        
    def test_is_mode_enabled_false(self):
        """Test checking if mode is enabled when it's disabled."""
        config_manager = ConfigManager()
        config_manager.config_data = {
            "modes": {
                "document_check": {"enabled": False}
            }
        }
        
        assert config_manager.is_mode_enabled("document_check") is False
        
    def test_is_mode_enabled_missing_mode(self):
        """Test checking if mode is enabled when mode doesn't exist."""
        config_manager = ConfigManager()
        config_manager.config_data = {"modes": {}}
        
        assert config_manager.is_mode_enabled("nonexistent_mode") is False
        
    def test_create_default_config_io_error(self):
        """Test handling of IO error when creating default config."""
        config_manager = ConfigManager("/invalid/path/config.yaml")
        
        with pytest.raises(ConfigurationError, match="Cannot create default config file"):
            config_manager._create_default_config()
            
    def test_get_default_config_data_structure(self):
        """Test that default config data has correct structure."""
        config_manager = ConfigManager()
        default_config = config_manager._get_default_config_data()
        
        # Check all required sections are present
        assert "project" in default_config
        assert "required_documents" in default_config
        assert "modes" in default_config
        assert "output" in default_config
        assert "logging" in default_config
        
        # Check project section structure
        project = default_config["project"]
        assert "name" in project
        assert "default_path" in project
        
        # Check required_documents is a list with proper structure
        docs = default_config["required_documents"]
        assert isinstance(docs, list)
        assert len(docs) > 0
        
        for doc in docs:
            assert "name" in doc
            assert "patterns" in doc
            assert "formats" in doc
            assert "required" in doc
            assert isinstance(doc["patterns"], list)
            assert isinstance(doc["formats"], list)
            assert isinstance(doc["required"], bool)
            
        # Check modes section
        modes = default_config["modes"]
        assert "document_check" in modes
        assert "status_analysis" in modes
        assert "learning_module" in modes
        
        # Check output section
        output = default_config["output"]
        assert "directory" in output
        
        # Check logging section
        logging = default_config["logging"]
        assert "level" in logging