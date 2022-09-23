import logging
import pathlib
import typing as t

import toml

logger = logging.getLogger(__name__)


class ApplicationConfig:
    ERROR_FILE_MISSING = (
        "Path to configuration file missing. "
        "Either specify command line argument --app-config, or environment variable SECPI_APP_CONFIG"
    )

    def __init__(self, filepath: t.Optional[t.Union[pathlib.Path, str]] = None):
        self.filepath = filepath
        self.config = None

    def load(self):
        if self.filepath is None:
            raise FileNotFoundError(self.ERROR_FILE_MISSING)
        logger.info(f"Loading configuration from {self.filepath}")
        with open(self.filepath, "r") as config_file:
            self.config = toml.load(config_file)

    def save(self):
        if self.filepath is None:
            raise FileNotFoundError(self.ERROR_FILE_MISSING)
        if self.config.get("write_protected"):
            logger.info("Configuration is write protected, skip saving")
            return
        logger.info(f"Saving configuration to {self.filepath}")
        with open(self.filepath, "w") as config_file:
            toml.dump(self.config, f=config_file)

    def get(self, key, default=None):
        return self.config.get(key, default)

    def set(self, key, value):
        self.config[key] = value

    def update(self, new_config):
        self.config = new_config

    def asdict(self):
        return dict(self.config)
