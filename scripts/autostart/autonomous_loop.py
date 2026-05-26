# This script specifically triggers the autonomous logic if needed separately
from scripts.autostart.start_daemon import start
import asyncio

if __name__ == "__main__":
    asyncio.run(start())
