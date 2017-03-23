# coding=utf-8
import asyncio
import logging
import os
import yaml

from logging.handlers import TimedRotatingFileHandler
from time import sleep

from app.bot import Bot


__author__ = "Gareth Coles"
config = {}


if not os.path.exists("logs"):
    os.mkdir("logs")

logging.basicConfig(
    format="%(asctime)s | %(name)s | [%(levelname)s] %(message)s",
    level=logging.INFO
)


def setup_logger(name):
    if not os.path.exists("logs/{}".format(name)):
        os.mkdir("logs/{}".format(name))

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    handler = TimedRotatingFileHandler(
        filename="logs/{0}/{0}.log".format(name), encoding="utf-8",
        when="midnight", backupCount=30
    )
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s | %(name)s | [%(levelname)s] %(message)s")
    )

    logger.addHandler(handler)

    return logger

setup_logger("discord").setLevel(logging.WARN)
setup_logger("bot")


if not os.path.exists("config.yml"):
    print(
        "Unable to find config.yml - please copy config.yml.example "
        "and edit it!"
    )
    exit(1)

try:
    fh = open("config.yml", "r")
    config.update(yaml.load(fh))
    fh.close()
except Exception as e:
    print(
        "Unable to read config.yml: {}".format(e)
    )


def run():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    bot = Bot(config, loop=asyncio.get_event_loop())
    bot.run(config["discord"]["token"], bot=True)


if config["auto_reconnect"]:
    print("Running in auto-reconnect mode.")

    while True:
        run()
        print("Reconnecting...")
        sleep(5)
else:
    print("Running without auto-reconnect.")
    run()
