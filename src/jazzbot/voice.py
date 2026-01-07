"""Voice channel validation and management utilities."""

from typing import Optional, Tuple

import discord
from discord import VoiceChannel, VoiceState

from jazzbot.embeds import error_embed


async def validate_voice_context(
    interaction: discord.Interaction,
) -> Tuple[bool, Optional[discord.Embed], Optional[VoiceChannel]]:
    """
    Validate user voice context for music commands.

    Checks in order:
    1. User is in a voice channel
    2. Bot can see the channel
    3. Bot can join the channel
    4. Bot can speak in the channel

    Args:
        interaction: The Discord interaction

    Returns:
        Tuple of (is_valid, error_embed, voice_channel)
        If valid, error_embed will be None
        If invalid, voice_channel will be None
    """
    user: discord.Member = interaction.user  # type: ignore

    # Check 1: User must be in a voice channel
    if not user.voice or not user.voice.channel:
        embed = error_embed(
            "Not in Voice Channel",
            "You must be in a voice channel to use this command.",
        )
        return False, embed, None

    voice_channel: VoiceChannel = user.voice.channel

    # Check 2: Bot must be able to see the channel
    if not voice_channel:
        embed = error_embed(
            "Channel Not Visible",
            "I cannot see the voice channel you're in.",
        )
        return False, embed, None

    # Check 3: Bot must be able to join the channel
    permissions = voice_channel.permissions_for(interaction.guild.me)  # type: ignore
    if not permissions.connect:
        embed = error_embed(
            "Cannot Join Channel",
            "I don't have permission to join your voice channel.",
        )
        return False, embed, None

    # Check 4: Bot must be able to speak in the channel
    if not permissions.speak:
        embed = error_embed(
            "Cannot Speak in Channel",
            "I don't have permission to speak in your voice channel.",
        )
        return False, embed, None

    return True, None, voice_channel


async def ensure_bot_voice_state(
    interaction: discord.Interaction,
    voice_channel: VoiceChannel,
    bot_voice_client: Optional[discord.VoiceClient],
) -> Tuple[bool, Optional[discord.Embed]]:
    """
    Ensure bot is in the correct voice channel.

    Args:
        interaction: The Discord interaction
        voice_channel: The target voice channel
        bot_voice_client: Current bot voice client (if any)

    Returns:
        Tuple of (is_valid, error_embed)
        If valid, error_embed will be None
    """
    # If bot is not connected, it will join automatically
    if bot_voice_client is None:
        return True, None

    # If bot is in a different channel, refuse to move
    if bot_voice_client.channel and bot_voice_client.channel != voice_channel:
        embed = error_embed(
            "Bot in Different Channel",
            f"I'm already connected to {bot_voice_client.channel.mention}. "
            "Please use that channel or disconnect me first.",
        )
        return False, embed

    return True, None

