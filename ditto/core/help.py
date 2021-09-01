from collections.abc import Sequence
from typing import Any, Generic, Optional, TypeVar

import discord
from discord.ext import commands, menus

from .context import Context

from ..utils.paginator import *

__all__ = ("EmbedHelpCommand",)


PagT = TypeVar("PagT", bound=EmbedPaginator)
EmbT = TypeVar("EmbT", bound=discord.Embed)


class EmbedHelpCommand(commands.DefaultHelpCommand, Generic[PagT]):
    paginator: PagT
    context: Context

    def __init__(self, paginator: PagT = EmbedPaginator[EmbT](max_fields=8), **options: Any) -> None:
        options.update({"paginator": paginator})

        super().__init__(**options)

    async def send_pages(self) -> None:
        destination = self.get_destination()

        me = self.context.me

        self.paginator.colour = me.colour
        self.paginator.set_author(name=f"{me} Help Manual", icon_url=me.avatar.url)

        self.paginator.set_footer(text=self.get_ending_note())

        try:
            menu = menus.MenuPages(
                self.paginator, clear_reactions_after=True, check_embeds=True, delete_message_after=True
            )
            await menu.start(self.context, channel=destination)
        except menus.MenuError:
            raise commands.UserInputError("I was not able to send command help.")

    def get_command_signature(self, command: commands.Command) -> str:
        signature = super().get_command_signature(command)
        return f"Syntax: `{signature}`"

    def add_indented_commands(
        self, commands: Sequence[commands.Command], *, heading: str, max_size: Optional[int] = None
    ) -> None:
        if not commands:
            return

        max_size = max_size or self.get_max_size(commands)

        lines = []
        for command in commands:
            name = command.name
            width = max_size - (discord.utils._string_width(name) - len(name))
            entry = "{0}**{1:<{width}}**: {2}".format(self.indent * " ", name, command.short_doc, width=width)
            lines.append(self.shorten_text(entry))

        self.paginator.add_field(name=heading, value="\n".join(lines))
