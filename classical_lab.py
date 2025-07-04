import asyncio
import os
from flask.cli import load_dotenv
import sys

if not load_dotenv():
    print("Error loading .env file")
    sys.exit(-1)

from config import config
from lab.base_lab import QSimLab


class TeleportationLab(QSimLab):
    classical_hosts = {
        "alice": {},
        "bob": {},
    }
    classical_router = {"router1": {}}
    connections = [
        {"from_host": "alice", "to_host": "router1"},
        {"from_host": "router1", "to_host": "bob"},
    ]

    def execute(self):
        self.send_message('alice', 'bob', "Hello, Bob! This is Alice's message.")
        print('Executer called')

if __name__ == "__main__":
    lab = TeleportationLab()
    asyncio.run(lab._run())
    print("Lab execution completed.")
    os._exit(0)