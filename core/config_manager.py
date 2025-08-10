"""Configuration management for PM Analysis Tool.

This module provides configuration loading, validation, and management
functionality using YAML configuration files.
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from utils.exceptions import ConfigurationError
from utils.logger import get_logger

logger = get_logger(__name__)


class ConfigManager:
    """Manages configuration loading and validation for the PM Analysis Tool."""

    def __init__(self, config_path: Optional[str] = None):
        """Initialize ConfigManager with optional config file path.

        Args:
            config_path: Path to configuration file. If None, uses default config.yaml
        """
        self.config_path = config_path or "config.yaml"
        self.config_data: Dict[str, Any] = {}
        self._required_sections = ["project", "required_documents", "modes", "output", "logging"]
        self._required_project_fields = ["name", "default_path"]
        self._required_mode_fields = ["document_check", "status_analysis", "learning_module"]
        self._required_output_fields = ["directory"]
        self._required_logging_fields = ["level"]

    def load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file.

        Returns:
            Dictionary containing configuration data

        Raises:
            ConfigurationError: If config file cannot be loaded or is invalid
        """
        try:
            config_path = Path(self.config_path)

            if not config_path.exists():
                logger.warning(f"Config file {self.config_path} not found, creating default config")
                self._create_default_config()

            with open(config_path, "r", encoding="utf-8") as file:
                self.config_data = yaml.safe_load(file) or {}

            logger.info(f"Configuration loaded from {self.config_path}")
            self._validate_config()
            return self.config_data

        except yaml.YAMLError as e:
            raise ConfigurationError(f"Invalid YAML in config file {self.config_path}: {e}")
        except IOError as e:
            raise ConfigurationError(f"Cannot read config file {self.config_path}: {e}")

    def _validate_config(self) -> None:
        """Validate that all required configuration sections and fields are present.

        Raises:
            ConfigurationError: If required configuration is missing
        """
        # Check required top-level sections
        missing_sections = [
            section for section in self._required_sections if section not in self.config_data
        ]

        if missing_sections:
            raise ConfigurationError(f"Missing required configuration sections: {missing_sections}")

        # Validate project section
        project_config = self.config_data.get("project", {})
        missing_project_fields = [
            field for field in self._required_project_fields if field not in project_config
        ]

        if missing_project_fields:
            raise ConfigurationError(f"Missing required project fields: {missing_project_fields}")

        # Validate modes section
        modes_config = self.config_data.get("modes", {})
        missing_mode_fields = [
            field for field in self._required_mode_fields if field not in modes_config
        ]

        if missing_mode_fields:
            raise ConfigurationError(f"Missing required mode configurations: {missing_mode_fields}")

        # Validate output section
        output_config = self.config_data.get("output", {})
        missing_output_fields = [
            field for field in self._required_output_fields if field not in output_config
        ]

        if missing_output_fields:
            raise ConfigurationError(f"Missing required output fields: {missing_output_fields}")

        # Validate logging section
        logging_config = self.config_data.get("logging", {})
        missing_logging_fields = [
            field for field in self._required_logging_fields if field not in logging_config
        ]

        if missing_logging_fields:
            raise ConfigurationError(f"Missing required logging fields: {missing_logging_fields}")

        # Validate required_documents structure
        self._validate_required_documents()

        logger.info("Configuration validation completed successfully")

    def _validate_required_documents(self) -> None:
        """Validate the required_documents configuration structure.

        Raises:
            ConfigurationError: If required_documents structure is invalid
        """
        required_docs = self.config_data.get("required_documents", [])

        if not isinstance(required_docs, list):
            raise ConfigurationError("required_documents must be a list")

        for i, doc in enumerate(required_docs):
            if not isinstance(doc, dict):
                raise ConfigurationError(f"Document {i} must be a dictionary")

            required_doc_fields = ["name", "patterns", "formats", "required"]
            missing_fields = [field for field in required_doc_fields if field not in doc]

            if missing_fields:
                raise ConfigurationError(f"Document {i} missing required fields: {missing_fields}")

            # Validate field types
            if not isinstance(doc["patterns"], list):
                raise ConfigurationError(f"Document {i} patterns must be a list")
            if not isinstance(doc["formats"], list):
                raise ConfigurationError(f"Document {i} formats must be a list")
            if not isinstance(doc["required"], bool):
                raise ConfigurationError(f"Document {i} required must be a boolean")

    def get_project_config(self) -> Dict[str, Any]:
        """Get project configuration section.

        Returns:
            Project configuration dictionary
        """
        return self.config_data.get("project", {})

    def get_required_documents(self) -> List[Dict[str, Any]]:
        """Get required documents configuration.

        Returns:
            List of required document configurations
        """
        return self.config_data.get("required_documents", [])

    def get_modes_config(self) -> Dict[str, Any]:
        """Get operation modes configuration.

        Returns:
            Modes configuration dictionary
        """
        return self.config_data.get("modes", {})

    def get_output_config(self) -> Dict[str, Any]:
        """Get output configuration.

        Returns:
            Output configuration dictionary
        """
        return self.config_data.get("output", {})

    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration.

        Returns:
            Logging configuration dictionary
        """
        return self.config_data.get("logging", {})

    def get_project_path(self) -> str:
        """Get the default project path from configuration.

        Returns:
            Default project path
        """
        return self.get_project_config().get("default_path", "./project_files")

    def is_mode_enabled(self, mode: str) -> bool:
        """Check if a specific operation mode is enabled.

        Args:
            mode: Mode name to check

        Returns:
            True if mode is enabled, False otherwise
        """
        modes_config = self.get_modes_config()
        mode_config = modes_config.get(mode, {})
        return mode_config.get("enabled", False)

    def _create_default_config(self) -> None:
        """Create a default configuration file if none exists."""
        default_config = self._get_default_config_data()

        try:
            with open(self.config_path, "w", encoding="utf-8") as file:
                yaml.dump(default_config, file, default_flow_style=False, indent=2)
            logger.info(f"Created default configuration file: {self.config_path}")
        except IOError as e:
            raise ConfigurationError(f"Cannot create default config file: {e}")

    def _get_default_config_data(self) -> Dict[str, Any]:
        """Get default configuration data structure.

        Returns:
            Default configuration dictionary
        """
        return {
            "project": {"name": "PM Analysis Project", "default_path": "./project_files"},
            "required_documents": [
                {
                    "name": "Project Charter",
                    "patterns": ["*charter*", "*project*charter*"],
                    "formats": ["md", "docx"],
                    "required": True,
                },
                {
                    "name": "Scope Statement",
                    "patterns": ["*scope*", "*project*scope*"],
                    "formats": ["md", "docx"],
                    "required": True,
                },
                {
                    "name": "Risk Management Plan",
                    "patterns": ["*risk*", "*risk*management*"],
                    "formats": ["md", "docx"],
                    "required": True,
                },
                {
                    "name": "Work Breakdown Structure",
                    "patterns": ["*wbs*", "*work*breakdown*", "*breakdown*structure*"],
                    "formats": ["md", "docx"],
                    "required": True,
                },
                {
                    "name": "Roadmap",
                    "patterns": ["*roadmap*", "*timeline*", "*schedule*"],
                    "formats": ["md", "docx", "mpp"],
                    "required": True,
                },
                {
                    "name": "Stakeholder Register",
                    "patterns": ["*stakeholder*", "*stakeholder*register*"],
                    "formats": ["xlsx", "csv"],
                    "required": True,
                },
            ],
            "modes": {
                "document_check": {"enabled": True, "output_formats": ["markdown", "console"]},
                "status_analysis": {
                    "enabled": True,
                    "output_formats": ["markdown", "excel"],
                    "include_charts": True,
                },
                "learning_module": {"enabled": True, "content_path": "./learning/modules"},
            },
            "output": {
                "directory": "./reports",
                "timestamp_files": True,
                "overwrite_existing": False,
            },
            "logging": {"level": "INFO", "file": "pm_analysis.log", "console": True},
        }
