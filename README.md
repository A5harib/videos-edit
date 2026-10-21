# videos-edit

A Claude Code harness for turning raw talking-head clips into Instagram reels and YouTube videos, with burned-in word-highlight captions (Roman Urdu for Urdu speech) and floating info cards.

Everything lives in [insta-reel-editor](insta-reel-editor). `SKILL.md` is the workflow Claude follows and `scripts/` does the mechanical work: audio extraction, transcription with faster-whisper, caption alignment, card rendering and the ffmpeg render.

Raw clips, job folders and finished videos are kept locally and are not in this repo.
