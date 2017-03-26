# coding=utf-8
import os

from typing import Dict

import aiohttp
import asyncio
import logging
import re

from discord import Channel, Object
from discord import Client
from discord import Member
from discord import Message

from operator import attrgetter

__author__ = "Gareth Coles"


class Bot(Client):
    _has_printed_roles = False

    def __init__(self, config, *, loop=None, **options):
        super().__init__(loop=loop, **options)

        self._config = config

        self.logger = logging.getLogger("bot")
        self.rcon_logger = logging.getLogger("rcon")

    async def notify_admin(self, message: str, filename: str = None):
        admin_channel = self._config["discord"]["admin_channel"]

        if admin_channel:
            if not filename:
                await self.send_message(Object(admin_channel), message)
            else:
                try:
                    await self.send_file(Object(admin_channel), filename, content=message)
                except Exception as e:
                    self.send_message(
                        Object(admin_channel),
                        "An exception occurred while trying to upload {}:\n\n```{}```\n\nAttached message: {}".format(filename, e, message)
                    )

    async def download_attachment(self, attachment: Dict[str, str], user: Member):
        url = attachment["url"]
        filename = attachment["filename"]

        path = "tmp/{}-{}-{}".format(user.display_name, "", filename)

        session = aiohttp.ClientSession()

        async with session.get(url) as response:
            data = await response.read()

            with open(path, "wb") as fh:
                fh.write(data)
                fh.flush()

        return path

    def is_allowed(self, user: Member, channel: Channel):
        if not isinstance(user, Member):
            return False

        if self._config["discord"]["use_roles"]:
            roles = self._config["discord"]["roles"]

            for role in roles:
                has_role = False

                for user_role in user.roles:
                    if str(user_role.id) == role:
                        has_role = True

                if not has_role:
                    return False
            return True
        else:
            permissions = self._config["discord"]["permissions"]
            user_permissions = user.permissions_in(channel)

            for perm in permissions:
                if hasattr(user_permissions, perm):
                    if not getattr(user_permissions, perm):
                        return False
                else:
                    self.logger.warn("Unknown permission: {}".format(perm))
                    return False
            return True

    def is_correct_server(self, server: str):
        return server == self._config["discord"]["server"]

    async def check_jar_and_download(self, message: Message):
        if re.match(r".*://[^\s/]+/[^\s/]+\.jar.*", message.clean_content, (re.IGNORECASE | re.MULTILINE)):
            await self.notify_admin(
                "{} sent the following message containing suspicious URLs:"
                "\n\n```{}```".format(message.author.mention, message.content)
            )

            return "URL"
        if re.match(r"www\.[^\s/]+\.[^\s/]+/[^\s/]+\.jar.*", message.clean_content, (re.IGNORECASE | re.MULTILINE)):
            await self.notify_admin(
                "{} sent the following message containing suspicious URLs:"
                "\n\n```{}```".format(message.author.mention, message.content)
            )

            return "URL"

        for attachment in message.attachments:
            if re.match(r".*\.jar", attachment["filename"], re.IGNORECASE):
                try:
                    result = await self.download_attachment(attachment, message.author)
                    if message.content:
                        await self.notify_admin(
                            "{} attempted to upload this file. Message text:"
                            "\n\n```{}```".format(message.author.mention, message.content),
                            result
                        )
                    else:
                        await self.notify_admin(
                            "{} attempted to upload this file.".format(message.author.mention),
                            result
                        )

                    os.remove(result)
                except Exception as e:
                    await self.notify_admin(
                        "Failed to download suspicious file `{}` posted by {}:"
                        "\n\n```{}```".format(attachment["filename"], message.author.mention, e)
                    )
                return "EMBED"

    def log_message(self, message: Message):
        for line in message.clean_content.split("\n"):
            self.logger.info(
                "{message.server.name} #{message.channel.name} / "
                "<{message.author.name}#{message.author.discriminator}> "
                "{line}".format(message=message, line=line)
            )

    async def on_message(self, message: Message):
        if not message.server:
            return  # We don't handle DMs

        if message.author.id == self.user.id:
            return  # It me!

        if not self.is_correct_server(message.server.id):
            return  # Not a server we care about

        if not self._has_printed_roles:
            for role in sorted(message.server.roles, key=attrgetter("name")):
                self.logger.info("Role: {} -> {}".format(role.name, role.id))

            self._has_printed_roles = True

        self.log_message(message)

        if not self.is_allowed(message.author, message.channel):
            has_jar = await self.check_jar_and_download(message)

            if has_jar == "URL":
                self.logger.info("Message contains a URL ending in .jar")

                await self.delete_message(message)
                sent_message = await self.send_message(
                    message.channel,
                    "{}: Please do not link to JAR files on this server.".format(message.author.mention)
                )

                await asyncio.sleep(10)
                await self.delete_message(sent_message)
            elif has_jar == "EMBED":
                self.logger.info("Message contains an embedded .jar")

                await self.delete_message(message)
                sent_message = await self.send_message(
                    message.channel,
                    "{}: Please do not send attached JAR files on this server.".format(message.author.mention)
                )

                await asyncio.sleep(10)
                await self.delete_message(sent_message)


