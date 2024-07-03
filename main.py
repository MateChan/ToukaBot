import asyncio
import json
import os
from io import BytesIO
from typing import List
from uuid import uuid4

import rembg
import requests
from dotenv import load_dotenv
from misskey import Misskey
from pydantic import BaseModel
from websockets.client import connect


class File(BaseModel):
    id: str
    url: str
    isSensitive: bool


class User(BaseModel):
    username: str
    host: str | None


class Note(BaseModel):
    text: str
    id: str
    files: List[File] = []
    user: User


class WebSocketBody(BaseModel):
    id: str
    type: str
    body: Note


class WebSocketEvent(BaseModel):
    type: str
    body: WebSocketBody


async def main():
    load_dotenv()
    MISSKEY_HOST = os.getenv("MISSKEY_HOST")
    MISSKEY_TOKEN = os.getenv("MISSKEY_TOKEN")
    assert type(MISSKEY_HOST) == str, "no misskey hostname"
    assert type(MISSKEY_TOKEN) == str, "no misskey token"

    mk = Misskey(MISSKEY_HOST, MISSKEY_TOKEN)

    async with connect(
        f"wss://{MISSKEY_HOST}/streaming?i={MISSKEY_TOKEN}"
    ) as websocket:

        channel = {
            "type": "connect",
            "body": {
                "id": str(uuid4()),
                "channel": "main",
            },
        }
        await websocket.send(json.dumps(channel))
        print(f"connected to {MISSKEY_HOST}")

        while True:
            received = await websocket.recv()

            event = None
            try:
                event = WebSocketEvent.model_validate_json(received)
            except:
                pass

            if event == None or event.body.type != "mention":
                continue

            note = event.body.body

            if not note.text.find("透過") + 1 or len(note.files) == 0:
                continue

            file_ids: List[str] = []
            for file in note.files:

                content = requests.get(file.url).content
                removed = rembg.remove(content)
                assert type(removed) == bytes

                upload_res = mk.drive_files_create(
                    BytesIO(removed),
                    name=str(uuid4()),
                    is_sensitive=file.isSensitive,
                )
                uploaded_file = File.model_validate(upload_res)
                file_ids.append(uploaded_file.id)

                username = note.user.username
                host = note.user.host
                if not host:
                    host = MISSKEY_HOST

                print(f"@{username}@{host}: \t{file.id} -> {uploaded_file.id}")

            if len(file_ids) > 0:
                mk.notes_create(reply_id=note.id, file_ids=file_ids)


if __name__ == "__main__":
    asyncio.run(main())
