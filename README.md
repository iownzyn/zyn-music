# 𝐙𝐘𝐍 𝐌𝐔𝐒𝐈𝐂 🎧

Telegram voice-chat music bot, rebranded and maintained by 𝒁𝒂𝒚𝒏 𝑴𝒂𝒍𝒊𝒌, based on the Saya Music project with permission. Original project attribution and MIT license are preserved.

- Bot: [@ZynMusicBot](https://t.me/ZynMusicBot)
- Owner / Maintainer: 𝒁𝒂𝒚𝒏 𝑴𝒂𝒍𝒊𝒌
- Support: [@zynmusicupdates](https://t.me/zynmusicupdates)

## Branding asset
The original ZYN MUSIC logo is available at `SayaMusic/assets/zyn-logo.svg`.

## Run locally
1. Install dependencies: `pip install -r requirements.txt`.
2. Copy `sample.env` to `.env` and fill the required values privately.
3. Start the bot: `python -m SayaMusic`.

## Deploy on Render
Create a **Background Worker** from this repository, select the `main` branch and use the included `Dockerfile`. Add the environment variables below in Render's Environment tab. Do not deploy as a web service: this is a long-running Telegram worker and does not serve HTTP traffic.

## Required environment variables
`API_ID`, `API_HASH`, `BOT_TOKEN`, `MONGO_DB_URI`, `STRING_SESSION` and `LOGGER_ID`.

`STRING_SESSION` is the Pyrogram assistant/user session. The bot exits during startup when all assistant session slots are empty. Optional additional sessions are `STRING_SESSION2` through `STRING_SESSION5`.

Set secrets privately in your hosting dashboard. Never commit real tokens, session strings, cookies or database credentials. `sample.env` contains names and safe defaults only.

Defaults: OWNER_ID=9100108789, OWNER_USERNAME=shadowxtemp, OWNER_NAME=𝒁𝒂𝒚𝒏 𝑴𝒂𝒍𝒊𝒌, BOT_USERNAME=ZynMusicBot, BOT_NAME=𝐙𝐘𝐍 𝐌𝐔𝐒𝐈𝐂 🎧, LOGGER_ID=-1004420640566, SUPPORT_CHANNEL=https://t.me/zynmusicupdates, SUPPORT_CHAT=https://t.me/zynmusicupdates, UPSTREAM_REPO=https://github.com/iownzyn/zyn-music, UPSTREAM_BRANCH=main.

Original Saya Music attribution and license are retained in LICENSE.
