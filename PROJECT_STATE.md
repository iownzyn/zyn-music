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

## 2026-11-26 continuation — /vplay priority
- `b9cb2763`: isolated yt-dlp and API downloads into provider-specific directories under separate audio/video caches. This prevents concurrent API and yt-dlp jobs from writing the same filename while racing for the first valid result. Cache lookup checks provider-specific paths first, then the previous media-specific cache and safe legacy cache paths.
- End-to-end source audit for `/vplay`:
  - `/vplay` is registered in the group command handler and `PlayWrapper` sets the video flag from the command prefix.
  - YouTube video requests call `YouTube.download(..., video=True)`; downloaded video is queued with stream type `video`.
  - `dynamic_media_stream` uses required video and audio tracks, `VideoQuality.HD_720p`, and high audio quality.
  - Queue-next/skip playback preserves the video stream flag when queue metadata says `video`.
  - Video download uses yt-dlp with MP4 best-video up to 720p plus best audio, merged to MP4; API video fallback is also available when configured.
- CI for `b9cb2763` completed successfully: https://github.com/iownzyn/zyn-music/actions/runs/45703615244
- This is source/CI verification only. Real Telegram voice-chat video playback, API credentials/provider availability, and Render runtime have not been tested from this session. Do not mark /vplay runtime-tested or deploy-ready until those checks pass.

## 2026-11-26 — normal /play artwork and repeat-cache hardening
- `42c8a1e8`: playback artwork cache version bumped to v6; the card uses a clean, muted ivory/rose ZAYN × ALFIYA pill instead of the previous more prominent lettering.
- `e17b25e3`: normal `/play` search-result selection cards now call the existing per-track `get_thumb(video_id)` renderer instead of showing the raw YouTube thumbnail. Each song keeps its own source thumbnail and track title/duration.
- `262a049b`: artwork fallback no longer relies on an optional config logger attribute.
- `1ea5ebed`: added a small muted couple-avatar mark to the Zayn × Alfiya label; no neon/glow styling.
- `9536807a`: yt-dlp final-path resolver now ignores .part/.ytdl/.temp and zero-byte files so partial downloads cannot be returned as playable cache entries.
- CI passed for `1ea5ebed`; CI for `9536807a` was queued at the time this note was added.
- The user reiterated the visual direction: /vplay remains an HD video stream; normal /play gets the Zayn × Alfiya brand treatment with a clean Pinterest/anime-couple feel, no neon. Current implementation preserves unique per-track source thumbnails and adds the muted couple mark/brand label. A bespoke generated anime couple image has been created as a visual reference but has NOT yet been committed as a repo asset or wired into the playback card.
- Do not claim a live Telegram voice-chat test or Render deployment. Those still require runtime access.

- Latest CI for `fbb0aae9` completed successfully: https://github.com/iownzyn/zyn-music/actions/runs/45704676397
- `speed.py` source audit: speed command checks actual group-admin status; callback checks that the button belongs to the same group, validates allowed speeds, checks active playback, then verifies actual admin/owner membership before changing speed.
- `volume.py` source audit: volume command and callback both verify actual group-admin status; volume range is 50, 75, 100, 125, 150, 175, 200 percent; callback is tied to the originating group.
- Main playback controls source audit: callback verifies original group and actual admin/owner status before Pause/Resume/Stop/End/Loop/Shuffle/Skip/Replay/seek.
- These are code-level audits only. Actual Telegram group permission behavior and stream volume/speed still need runtime tests.

## 2026-11-26 continuation — normal-play artwork, group control mode, help audit
- `be4bd219` and `d6b27695`: replaced the old YouTube thumbnail overlay with fresh, locally generated clean storybook/anime-inspired couple artwork for each normal-play track card. Each generated frame uses muted Pinterest-like palettes, varied hair/skin/clothing combinations, soft botanical accents, no neon/glow, and a readable `ZAYN × ALFIYA` plaque. Per-request images use unique cache names; generated art older than 24 hours is expired. This is procedural original artwork, not external Pinterest downloads.
- `c0218050`: ensured the normal URL/search track card also uses the new couple artwork (not only slider search results). HD `/vplay` remains a separate video stream.
- `80830dfd`, `fad836a4`, `a64a1d91`, `e79ba1da`, `c0103986`, `0e0d3cea`, `6929f456`, `87dcc8cd`, `bda4de42`, `213e2a12`, `7c19802b`, `5445658f`: added persistent per-group playback-control mode and applied it to command and inline controls. Actual group admins can enable/disable/status with `/groupmode on|off|status`. When enabled, regular members can pause/resume/skip/loop/shuffle/seek/volume/speed. Stop/End (including player Stop button) remain restricted to actual current group admins. The command itself verifies the actual admin role; the mode is stored in MongoDB.
- `b26cc34c`, `c903dc21`, `c41916ea`, `4c47d9f3`, `b697e07c`: updated Help category 11 from the non-working ChatGPT placeholder to Group Mode; corrected /welcome command help; documented /groupmode; corrected /play and /vplay descriptions; removed unregistered /carbon, /downloadrepo and /code references; documented verified /encode and /decode; added the correct /setdescription alias for the existing misspelled handler.
- Existing group member welcome/goodbye handlers and photo fallbacks remain intact. They are not being replaced by the bot's /start welcome video.
- CI on latest help cleanup commit `b697e07c` was still in progress at time of this note: https://github.com/iownzyn/zyn-music/actions/runs/45705695525
- Not yet live-tested: random art rendering in Telegram, /groupmode permissions with real non-admin/admin accounts, voice-chat Stop/End behavior, and Render production. Do not deploy yet.

- Additional permission hardening: `ea4c7c46` and `fceb5c06` make every shared playback command verify the actual current group admin or the saved group-mode setting before any legacy non-admin/vote bypass can apply. This prevents a legacy non-admin toggle from defeating the new /groupmode OFF admin-only default.
- `c95226c6`: improved the callback denial text so members are told to ask an admin to enable /groupmode; Stop/End denial explicitly says only real group admins can use it.
- Help audit against actual plugin handlers: /encode and /decode replace the unsupported carbon entry; /repo replaces the unsupported downloadrepo entry; /code was removed; /setdescription was fixed with a correctly spelled alias; /deleteall was confirmed present; /logs, /update, /restart, /maintenance and /logger were confirmed present. The non-working ChatGPT placeholder was replaced by the real Group Mode topic.
- Removed several adult-oriented percentage/media commands from the fun plugin and removed those names from Help; the remaining lighthearted commands are retained.
- CI for `fceb5c06` passed Python compilation and JSON validation. CI for `c95226c6` had completed both validation steps successfully and was finishing the job at the time of this note.

## 2026-11-26 additional audit/fix
- `b2e1a39c`: fixed a real /start welcome-video bug: the `resetstartvideo` decorator had accidentally been attached to the internal `get_welcome_video()` helper (wrong handler signature), leaving the actual reset command unregistered. The decorator is now attached to `reset_start_video_command(client, message)`, and the helper is a normal internal function.
- Reused the resilient `get_welcome_video()` resolver for private /start, group /start, and bot-added-to-group welcome flows. All three now share the saved Telegram video + configured fallback behavior through `send_welcome_video`.
- Confirmed /vplay routes through the video flag in PlayWrapper, the downloader prefers MP4 video up to 720p (1280px wide) with a compatible fallback, and the PyTgCalls media stream uses `VideoQuality.HD_720p`. This is source-level verification, not a live call test.
- Confirmed volume API validates 50–200 and uses PyTgCalls `change_volume_call`; group-mode admin-only Stop/End is enforced in both the inline player callback and /end command path.
- CI for `b2e1a39c` passed: Python compileall and JSON config validation. Run: https://github.com/iownzyn/zyn-music/actions/runs/45706654432
- Remaining external runtime tests: real Telegram playback (/play, /vplay, audio/video switching), volume audibility, actual admin/member group-mode matrix, Stop/End denial, start-video upload/reset and fallback, random couple art delivery, welcome/goodbye delivery, and Render service health/readiness. No deployment has been performed.

- Welcome video activation asset confirmed available in the current workspace: `/mnt/data/Zayn_Alfiya_Premium_Welcome.mp4` (22.36 seconds, 960×720, ~7.3 MB). This is the approved edited couple video from the 25 Nov session. It is not committed as a binary repo file and has not yet been uploaded to Telegram; activate it by sending the MP4 to `@ZynMusicBot` and replying to it with `/setstartvideo`. Verify with `/start`; owner can revert using `/resetstartvideo`.
- The Render `/health` and `/ready` endpoints could not be independently reached from the current web inspection session. The keep-alive workflow is configured to ping `/health` every five minutes, but current production health/readiness is unverified.
