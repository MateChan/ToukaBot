# ToukaBot

「透過」を含むメンション投稿に対して，その投稿に添付してある画像を透過してリプライする Misskey bot

## Setup

```bash
uv vnev
source .venv/bin/activate
uv pip install -r requirements.txt
echo -e "MISSKEY_HOST=<your_misskey_host>\nMISSKEY_TOKEN=<your_misskey_api_token>" > .env
```

## Run

```bash
source .venv/bin/activate
python main.py
```
