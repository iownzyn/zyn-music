# ZYN MUSIC — Project State & Continuation Notes

Last reviewed: 2026-11-26
Repository: https://github.com/iownzyn/zyn-music
Branch: main
Bot: 𝐙𝐘𝐍 𝐌𝐔𝐒𝐈𝐂 🎧 (@ZynMusicBot)

## Purpose
Preserve the full project requirements and exact continuation point across chats. Keep the original Saya Music feature set; do not remove existing commands/features without explicit approval. Work step by step and do not claim deploy-ready until code, CI, Telegram runtime, voice-chat and Render checks are verified.

## User requirements recovered from the 2026-11-26 screen recording
1. `/play`: fast audio-only playback; reduce search/download wait and cache repeated tracks.
2. `/vplay`: separate HD video playback in the Telegram voice chat.
3. Playback UI: Pause, Resume, Next/Skip, Stop, Speed and Volume.
4. Every playback should have a fresh, stylish, watermark-free anime/Pinterest-inspired visual, branded with stylish `Zayn × Alfiya` / `zayn.alfiya`; avoid reusing one identical image for every track.
5. Per-group security: only actual admins of the group where the stream is running may use playback controls, including buttons and commands.
6. Volume boost: 50%–200%, with a warning that amplification can cause clipping/distortion and cannot guarantee a particular loudness.
7. Private `/start`: cute Zayn × Alfiya couple welcome video, Korean/anime-inspired, soft romantic visual treatment, original/suitable background music. The user previously described an edited video as 22.36 seconds, but the uploaded 2026-11-26 MP4 in chat was a screen recording, not that welcome-video asset.
8. Group welcome: new member's own profile photo with welcome message.
9. Group goodbye: leaving/removed member's own profile photo with goodbye message; fall back to text if the photo cannot be retrieved.
10. Show total users and monthly active users.
11. Render health endpoint ping every five minutes. This does not guarantee that Render Free instances will stay awake.
12. Start assistants in parallel and join configured groups concurrently to reduce startup delay; actual voice-chat join time still needs runtime testing.
13. Start menu: remove Source button; Support should point to https://t.me/zynchatgc; Channel should remain https://t.me/zynmusicupdates.

## Confirmed code / CI observations
- Downloader includes a local cache lookup and in-flight request deduplication; playback speed benefit still needs live timing verification.
- `/vplay` is routed through the video flag and the call layer requests HD 720p video; live Telegram video playback remains unverified.
- Volume options 50, 75, 100, 125, 150, 175, 200 exist. Runtime loudness and assistant compatibility remain unverified.
- Five-minute Render workflow exists at `.github/workflows/render-keepalive.yml`; successful workflow ping is not proof that Render Free sleep is bypassed.
- Assistant startup and configured-group joins use concurrent tasks.
- Welcome image generation uses the joining member's photo with a fallback.
- Goodbye handler now downloads the leaving member's profile photo before sending it, with text fallback.
- Monthly active-user count is based on user `last_seen` timestamps and is displayed in /start; database/runtime count still needs verification.
- Start menu support/channel links are set through config; Source was removed in prior commits.
- Existing track artwork in `SayaMusic/utils/thumbnails.py` is a stylized panel around the source video thumbnail. It is NOT yet the requested unique Zayn × Alfiya anime artwork per track.
- `config.START_VIDS` still points to the existing generic Catbox video. The 22.36-second Zayn × Alfiya welcome video has NOT been integrated into /start in the checked repository state.

## Changes made during 2026-11-26 continuation
- `535b2c1e`: playback button callbacks now verify the real administrator/owner status in the exact group and reject mismatched/forged group controls.
- `a8bce703`: added `SayaMusic/utils/group_admin.py` for live group-admin verification.
- `ad5b8c38`, `9230a390`, `65c9e739`, `272162ee`, `416aae5e`, `ba7a8448`: added live group-admin checks to pause, resume, skip, stop, speed and volume commands.
- `f499fa95`: goodbye notifications download and send the member's profile photo, with text fallback.
- GitHub Code Quality and Syntax Check succeeded for the above commits, including latest checked commit `ba7a8448`. This is syntax/quality CI only, not runtime validation.
- Earlier verified repository head before these new changes: `7b229b6d`.

## Exact continuation point / still pending
Do NOT declare deploy-ready or deploy a final release yet.
1. Test `/play` end-to-end and measure search-to-audio start time; verify repeat-track cache hits.
2. Test `/vplay` end-to-end in an active Telegram video-capable group call; verify actual HD video.
3. Verify volume 50–200% against the real assistant/PyTgCalls version and listen for clipping.
4. Verify pause/resume/skip/stop/speed/volume command and button authorization with both a real group admin and a normal member.
5. Create/integrate original varied Zayn × Alfiya anime track artwork; current thumbnail panel is not sufficient.
6. Obtain the actual 22.36-second welcome-video asset and integrate it into private /start; preserve only audio that is owned/licensed/appropriate.
7. Test join photo welcome and leave/remove photo goodbye in Telegram.
8. Verify total and monthly active-user statistics against MongoDB/runtime data.
9. Test assistant startup, configured group joining and actual voice-chat joining latency.
10. Verify the deployed Render service, health endpoint, logs and live bot after all above pass.

## Working rules
- Preserve Saya Music functionality and existing commands.
- Do not change session strings, API credentials or production environment variables while diagnosing playback unless evidence requires it.
- Never invent test results or say CI success means live playback works.
- Keep secrets out of commits and project notes.

## Additional work after the first 2026-11-26 checkpoint
- `e2d08e79`: separated audio and video download caches into media-specific folders so cached audio is not reused for `/vplay`; hardened concurrent download deduplication and provider fallback error handling.
- `91c51bae`: added `START_VIDEO_URL` / comma-separated `START_VIDS` Render environment override. The final Zayn × Alfiya video URL is not configured because the actual 22.36-second asset was not present in the supplied 78-second screen recording.
- `411fe14f`: moved welcome-media cleanup into module scope so goodbye photo cleanup can call it safely.
- `e613a037`: music commands now update user `last_seen`, improving monthly active-user counting beyond /start-only visits.
- Fresh source audit confirmed `change_volume_call(chat_id, volume)` is used, `/vplay` requests HD 720p, and assistant startup/group joins are concurrent.
- Fresh audit found the current start video is still the generic configured Catbox asset and the current track card is a designed YouTube thumbnail, not the requested Zayn × Alfiya anime artwork.

## Latest CI snapshot
- Syntax/quality checks passed for `e2d08e79`, `91c51bae`, and earlier admin/security commits.
- `411fe14f` was still in progress at last check; `e613a037` had not yet appeared in the latest workflow list.
- Check the live Actions page before relying on the final status.

- `245dfd96`: refreshed project state after the latest source audit and follow-up changes.
- Latest checked Code Quality and Syntax Check for `245dfd96` completed successfully: https://github.com/iownzyn/zyn-music/actions/runs/45700622223
- Despite CI success, the remaining external-asset and live-runtime items above still block the deploy-ready declaration.

## Welcome video asset supplied on 2026-11-26
- User supplied the original Zayn × Alfiya welcome video and approved a clean premium edit with one correctly placed Zayn name, one Alfiya name, and a heart-shaped music/pause visual between them.
- Edited deliverable in the current ChatGPT runtime: `/mnt/data/Zayn_Alfiya_Welcome_Clean_Premium.mp4` (22.476 seconds, 960x720, approx. 8.2 MB). This is a session-local file and is not yet hosted at a stable public HTTPS URL or committed as a binary repo asset.
- `START_VIDEO_URL` / `START_VIDS` config override is already present. Once the edited MP4 is hosted at a stable HTTPS URL, set Render environment variable `START_VIDEO_URL` to that URL; do not replace the current production URL until the new URL is verified.
- `0880dd93`: private and group `/start` now fall back to a text welcome with the same caption/buttons if video hosting fails, instead of silently failing or breaking /start.
- The welcome-video asset is approved visually by the user, but integration and live Telegram delivery remain pending until stable hosting and runtime verification.

## Further continuation on 2026-11-26 (after approved premium welcome edit)
- User approved the premium Zayn × Alfiya welcome-video edit. The final approved ChatGPT file is session-local; it is not yet hosted or committed as a repo binary.
- `8570100d`: added a subtle ZAYN + heart + ALFIYA premium signature to each track card while retaining each track's own source thumbnail; cache version bumped to v5 so cards regenerate.
- `14dc578e`: added a warning that playback above 100% can cause clipping/distortion.
- `f5004518`: API media downloads now write to a temporary .part file and atomically replace the cache target only after a non-empty complete transfer.
- `7d898a6a`: added MongoDB-backed custom start-video file_id storage helpers.
- `c0afb121`: added owner-only `/setstartvideo` and `/resetstartvideo` commands; private/group /start and bot-added group welcome use the saved Telegram file_id when configured, with URL fallback when none is saved.
- `bdeaadd7`: made custom welcome-video lookup resilient to database read errors and allowed video documents as well as native video uploads.
- Code Quality and Syntax Check for `bdeaadd7` passed all steps (Python compile and JSON validation): https://github.com/iownzyn/zyn-music/actions/runs/45703215267
- To integrate the approved video without needing a public hosting site: send the approved MP4 to @ZynMusicBot as a video, then reply to that video with `/setstartvideo`. The command is owner-ID restricted. Test /start afterwards. Use `/resetstartvideo` to revert to the configured URL.
- Current approved local MP4 in the ChatGPT runtime: `/mnt/data/Zayn_Alfiya_Premium_Welcome.mp4` (22.362 sec, H.264 960x720, AAC audio, 7.57 MB). It is not automatically accessible to the Render service until the Telegram file_id is saved via the bot command.

- `73a1873b`: unified private/group/bot-added welcome video sending; if a saved Telegram file_id is unavailable, /start retries the configured HTTPS video before falling back to text.
- The premium track card now includes a branded ZAYN-heart-ALFIYA header over each track's own thumbnail. This is a track-specific thumbnail treatment, not AI-generated anime art per track; a true per-track generated anime pipeline remains unimplemented.
- The final welcome-video asset can be installed without external hosting using the owner-only Telegram workflow documented above. It still requires the owner to send the approved MP4 to @ZynMusicBot and reply `/setstartvideo`; ChatGPT cannot directly inject a Telegram file_id into the bot's database.
