from pathlib import Path
import logging
import logging.config
import subprocess
from subprocess import Popen

from infi.systray import SysTrayIcon
import yaml


__version__ = "0.3.0"

logger = logging.getLogger("idasen-tray")

server: Popen


def setup_logging(debug: bool, quiet: bool) -> None:
    try:
        with Path("idasen_tray/logging.yaml").open() as logging_file:
            logging_yaml = yaml.safe_load(logging_file)

            logging_level = "INFO"
            if debug:
                logging_level = "DEBUG"
            if quiet:
                logging_level = "WARNING"

            logging_yaml["root"]["level"] = logging_level

            logging.config.dictConfig(logging_yaml)
    except FileNotFoundError:
        logger.warn("missing logging config file")


def find_presets() -> dict[str, int]:
    with Path("idasen_tray/config.yaml").open() as file:
        config = yaml.safe_load(file)

        return config["favourites"]


def start_server() -> None:
    global server
    server = Popen(f"idasen-controller --server --config idasen_tray/config.yaml", creationflags=subprocess.CREATE_NO_WINDOW)


def trigger_desk(tray: SysTrayIcon, height: int):
    logger.info(f"moving desk to {height/10}cm")

    Popen(f"idasen-controller --forward --move-to {height}", creationflags=subprocess.CREATE_NO_WINDOW)


def cleanup(tray: SysTrayIcon) -> None:
    global server
    server.kill()


if __name__ == "__main__":
    setup_logging(True, False)
    logger.info(f"starting idasen-tray v{__version__}")

    presets = find_presets()
    logger.debug(presets)

    menu = (("STOP", f"resources/stop.ico", lambda tray: trigger_desk(tray, 0)), )
    for preset, height in presets.items():
        menu += ((f"{preset} ({height / 10}cm)", f"resources/{preset}.ico", lambda tray, height=height: trigger_desk(tray, height)), )

    with SysTrayIcon("resources/idasen-tray.ico", "Idasen Tray", menu_options=menu, on_quit=cleanup) as tray:
        start_server()
