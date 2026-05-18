#!/usr/bin/env python3
"""
Local development test script for the Flybox integration.

Usage:
    python test_connection.py <router_ip>

Example:
    python test_connection.py 192.168.2.1
"""

import asyncio
import json
import logging
import sys
from pathlib import Path

# Make the custom_components package importable from the repo root
sys.path.insert(0, str(Path(__file__).parent))

from custom_components.flybox.api import FlyboxApiClient, FlyboxApiError

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


async def main(host: str) -> None:
    print(f"\nConnecting to Flybox at {host} ...\n")
    client = FlyboxApiClient(host)
    try:
        data = await client.async_get_data()
        print("SUCCESS — data received:\n")
        print(json.dumps(data, indent=2))
    except FlyboxApiError as err:
        print(f"ERROR: {err}", file=sys.stderr)
        sys.exit(1)
    finally:
        await client.async_close()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python test_connection.py <router_ip>")
        sys.exit(1)

    asyncio.run(main(sys.argv[1]))
