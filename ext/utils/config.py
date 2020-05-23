import asyncio
import json
import os
import uuid
from os import environ, path
from pathlib import Path

_config_path = Path(environ.get("CONFIG_PATH", "config")).resolve()
_config_path.mkdir(parents=True, exist_ok=True)


class Config:
    def __init__(self, name):
        self.name = name
        self.loop = asyncio.get_event_loop()
        self.lock = asyncio.Lock()

        try:
            with (_config_path / self.name).open() as f:
                self._db = json.load(f)
        except FileNotFoundError:
            self._db = {}

    def _save(self):
        temp = _config_path / f"{uuid.uuid4()}.{self.name}.tmp"
        with temp.open("w", encoding="utf-8") as f:
            json.dump(
                self._db.copy(), f, ensure_ascii=True, separators=(",", ":"),
            )

        temp.replace(_config_path / self.name)

    def get(self, key, default=None):
        return self._db.get(str(key), default)

    def put(self, key, value):
        self._db[str(key)] = value
        self._save()

    def remove(self, key):
        del self._db[str(key)]
        self._save()

    def __contains__(self, item):
        return str(item) in self._db

    def __getitem__(self, item):
        return self._db[str(item)]

    def __len__(self):
        return len(self._db)
