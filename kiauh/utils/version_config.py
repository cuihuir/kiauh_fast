"""Version configuration loader for component version pinning.

Reads component_versions.json to determine which git tag
each component should be checked out to during installation.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

from core.logger import Logger

VERSION_CONFIG_FILE = Path(__file__).resolve().parent.parent.parent.joinpath(
    "component_versions.json"
)

@dataclass
class ComponentVersionConfig:
    """Version configuration for a single component."""
    repo_url: str
    tag: str
    install_dir: str
    env_dir: str

class VersionConfigManager:
    """Manages component version configuration from component_versions.json."""

    _instance: Optional["VersionConfigManager"] = None
    _configs: Dict[str, ComponentVersionConfig] = {}

    def __new__(cls) -> "VersionConfigManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if self._configs:
            return
        self._load_config()

    def _load_config(self) -> None:
        """Load version configuration from JSON file."""
        if not VERSION_CONFIG_FILE.exists():
            Logger.print_warn(
                f"Version config file not found: {VERSION_CONFIG_FILE}"
            )
            return

        try:
            with open(VERSION_CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)

            components = data.get("components", {})
            for name, cfg in components.items():
                self._configs[name] = ComponentVersionConfig(
                    repo_url=cfg.get("repo_url", ""),
                    tag=cfg.get("tag", ""),
                    install_dir=cfg.get("install_dir", ""),
                    env_dir=cfg.get("env_dir", ""),
                )
        except (json.JSONDecodeError, OSError) as e:
            Logger.print_error(f"Error loading version config: {e}")

    def get_config(self, component_name: str) -> Optional[ComponentVersionConfig]:
        """Get version config for a component by name."""
        return self._configs.get(component_name)

    def get_tag(self, component_name: str) -> str:
        """Get the target tag for a component. Returns empty string if not found."""
        cfg = self.get_config(component_name)
        return cfg.tag if cfg else ""

    def get_repo_url(self, component_name: str) -> str:
        """Get the repo URL for a component. Returns empty string if not found."""
        cfg = self.get_config(component_name)
        return cfg.repo_url if cfg else ""

    def get_install_dir(self, component_name: str) -> str:
        """Get the install directory name for a component."""
        cfg = self.get_config(component_name)
        return cfg.install_dir if cfg else ""

    def get_env_dir(self, component_name: str) -> str:
        """Get the env directory name for a component."""
        cfg = self.get_config(component_name)
        return cfg.env_dir if cfg else ""

    def get_all_components(self) -> Dict[str, ComponentVersionConfig]:
        """Get all component configs."""
        return dict(self._configs)

    def reload(self) -> None:
        """Force reload the configuration."""
        self._configs = {}
        self._load_config()
