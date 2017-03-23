# coding=utf-8
import asyncio
import logging
import re

from discord import Channel
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

    def message_has_jar(self, message: Message):
        if re.match(r".*://[^\s/]+/[^\s/]+\.jar.*", message.clean_content, (re.IGNORECASE | re.MULTILINE)):
            return "URL"
        if re.match(r"www\.[^\s/]+\.[^\s/]+/[^\s/]+\.jar.*", message.clean_content, (re.IGNORECASE | re.MULTILINE)):
            return "URL"

        for attachment in message.attachments:
            if re.match(r".*\.jar", attachment["filename"], re.IGNORECASE):
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

        has_jar = self.message_has_jar(message)

        if not self.is_allowed(message.author, message.channel):
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


