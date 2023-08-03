from pathlib import Path
import logging
import logging.config
import subprocess
from subprocess import Popen
import sys
import time

from infi.systray import SysTrayIcon
import yaml


__version__ = "0.2.0"

logger = logging.getLogger("idasen-tray")

running: bool
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


def read_presets() -> dict[str, int]:
    logger.info("reading configuration file")

    with Path("idasen_tray/config.yaml").open() as file:
        config = yaml.safe_load(file)

        return config["favourites"]


def start_server() -> None:
    logger.info("starting idasen controller server")

    global server
    server = Popen(f"idasen-controller --server --config idasen_tray/config.yaml", creationflags=subprocess.CREATE_NO_WINDOW)


def trigger_desk(tray: SysTrayIcon, height: int):
    if height != 0:
        logger.info(f"moving desk to {height/10}cm")
    else:
        logger.info(f"stopping desk")

    Popen(f"idasen-controller --forward --move-to {height}", creationflags=subprocess.CREATE_NO_WINDOW)


def quit(tray: SysTrayIcon) -> None:
    logger.info("quitting")

    global server
    server.kill()

    global running
    running = False


if __name__ == "__main__":
    setup_logging(True, False)
    logger.info(f"starting idasen-tray v{__version__}")

    presets = read_presets()
    logger.debug(presets)

    menu = (("STOP", f"resources/stop.ico", lambda tray: trigger_desk(tray, 0)), )
    for preset, height in presets.items():
        menu += ((f"{preset} ({height / 10}cm)", f"resources/{preset}.ico", lambda tray, height=height: trigger_desk(tray, height)), )

    with SysTrayIcon("resources/idasen-tray.ico", "Idasen Tray", menu_options=menu, on_quit=quit) as tray:
        start_server()

        logger.debug("waiting for tray exit")
        running = True
        while running:
            time.sleep(4)
