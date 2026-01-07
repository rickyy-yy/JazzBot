"""Embed utilities for JazzBot responses."""

from typing import Optional

import discord
from discord import Embed

from .config import Config


def create_embed(
    title: str,
    description: Optional[str] = None,
    color: Optional[int] = None,
    footer: Optional[str] = None,
) -> Embed:
    """
    Create a standardized embed with JazzBot styling.

    Args:
        title: Embed title
        description: Embed description
        color: Embed color (defaults to primary color)
        footer: Footer text

    Returns:
        Formatted Discord embed
    """
    embed = Embed(
        title=title,
        description=description,
        color=color or Config.PRIMARY_COLOR,
    )
    if footer:
        embed.set_footer(text=footer)
    return embed


def success_embed(title: str, description: Optional[str] = None) -> Embed:
    """Create a success embed with muted green color."""
    return create_embed(title, description, color=Config.SUCCESS_COLOR)


def warning_embed(title: str, description: Optional[str] = None) -> Embed:
    """Create a warning embed with soft amber color."""
    return create_embed(title, description, color=Config.WARNING_COLOR)


def error_embed(title: str, description: Optional[str] = None) -> Embed:
    """Create an error embed with muted red color."""
    return create_embed(title, description, color=Config.ERROR_COLOR)


def info_embed(title: str, description: Optional[str] = None) -> Embed:
    """Create an info embed with neutral slate color."""
    return create_embed(title, description, color=Config.INFO_COLOR)

