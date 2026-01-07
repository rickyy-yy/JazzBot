"""Simple entry point for running JazzBot."""

import asyncio
import sys

from src.jazzbot.bot import main

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutting down JazzBot...")
        sys.exit(0)

