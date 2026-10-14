---
name: insta-reel-editor
description: Turn raw talking-head videos (phone or WhatsApp clips of someone speaking to camera) into Instagram-ready reels with burned-in word-highlight captions and small floating graphic cards, using any charts or images the user supplies. Use this whenever the user asks to edit videos for Instagram or reels, make videos "insta ready", add captions or subtitles to talking videos, sprinkle images or graphics into videos, or says to follow the reel editing skill for a folder of videos, including Urdu or Hindi clips that need Roman Urdu captions.
---

# Instagram reel editor

Takes a folder of talking-head videos, plus optional images, and produces finished reels: 1080x1920, 30 fps, audio at about -14 LUFS, captions burned in, graphics floating over the bottom of the frame.

The scripts in `scripts/` do the mechanical work. Your job is the judgement: correcting the transcript, choosing what each card says, and timing cards to the speech.

## The look the user wants

These came from direct corrections, so treat them as the brief unless the user says otherwise.

- **Full-screen video.** No split screen and no coloured panel behind the graphics.
- **No graphic during the intro.** Let the speaker greet and introduce the topic with only captions on screen. The first card arrives at the first real point, usually 5 to 12 seconds in.
- **Small floating cards** in the bottom area, with the video visible around them. After the first card there is always one on screen; each new card replaces the last.
- **Supplied images first.** Spread the user's images across the videos where they match what is being said, and reuse them across videos. Fill the gaps with your own cards.
- **Own cards must not look like AI filler.** Keep them typographic and plain: a statement, a short list, a few chips, a simple bar. Match the palette and font of the supplied images. Put only what the speaker says on a card; never invent figures or facts.
- **Captions on every video**, a few words at a time, with the spoken word highlighted. Urdu or Hindi speech gets **Roman Urdu** captions, not Urdu script.
- **Speed over polish.** The user wants results quickly. Make one video as an example, show it, then do the rest in the same style. Do not add extras nobody asked for.

## Workflow

Work in a job folder inside the scratchpad. Originals are never modified; outputs go to an `instagram` folder beside them.

Only `transcribe.py` needs the transcription environment. Its Python is at `%USERPROFILE%\.cache\insta-reel-editor\venv\Scripts\python.exe`. If that is missing, create it with `python -m venv` and `pip install faster-whisper` (slow, run it in the background). The other scripts run on any Python.

### 1. Set up and look

```
python scripts/init_job.py <job> "<folder with the videos>"
```

This extracts audio, makes a contact sheet per video in `<job>/frames/`, copies the images to `<job>/cards/img1..N`, and writes `<job>/job.json`. Read the contact sheets and the images.

Check for mirrored footage: if signs or text in the background read backwards, set `"hflip": true` in `job.json`.

Check for sideways footage: a portrait-sized file (480x854) whose speaker lies on their side was filmed landscape. Set `"transpose": 2` in `job.json` (head pointing right; use 1 if it points left). Such footage cannot fill a vertical frame, so ask the user; for long videos the usual answer is `"landscape": true`, a 1920x1080 YouTube video with the card on the right and captions at the bottom.

Check for one recording split into parts: Snapchat cuts at 120 s, so several clips of exactly 120.0 s plus one shorter clip are one video. Find the order from the speech at each seam (the save time in `creation_time` is a hint). Render each part as its own vid (start parts 2 onward with a card at 0), then join them without re-encoding: `ffmpeg -f concat -safe 0 -i parts.txt -c copy -movflags +faststart out.mp4`.

Crop stray artefacts off supplied images with ffmpeg before using them (a watermark blob in a corner, a stray line, a big empty margin).

### 2. Transcribe

```
<venv python> scripts/transcribe.py small <job>/tr <job>/audio/v1.wav <job>/audio/v2.wav ...
```

Use the `small` model. It is already downloaded, auto-detects the language and takes seconds per clip. The large model is too slow on this machine to be worth it.

Tell the user what each video is about once you have the transcripts.

### 3. Captions

Captions are burned in, so fix the transcript by hand: names, places, numbers, misheard words.

If the transcript has punctuation and is mostly right:

```
python scripts/captions.py dump <job>/tr/v1.json <job>/caps/v1.tsv
```

then edit the text column of the `.tsv` directly.

If it needs rewriting (no punctuation, many errors, or Urdu), write the corrected text to `<job>/caps/v1.txt` and run:

```
python scripts/captions.py align <job>/caps/v1.txt <job>/tr/v1.json <job>/tr_fix/v1.json
python scripts/captions.py dump  <job>/tr_fix/v1.json <job>/caps/v1.tsv
```

Punctuation in your text decides where captions break, so punctuate properly.

For **Roman Urdu**, transliterate word for word so your text has exactly as many tokens as the transcript; the timings then map one to one. Two markers keep the count equal:

- `_` drops a word (a stammer, a filler) and gives its time to the previous word.
- `~` joins two words in one slot, for example `add~hue` where the transcript merged them.

First run `dump` on the raw transcript to see it in short lines, then write your text with the same number of tokens on each line. `align` prints a warning if the counts differ.

Keep a list of words you were unsure of. You cannot hear the audio, so the user has to check those.

### 4. Cards

Copy `assets/cards-example.html` to `<job>/cards/v1.html` and replace its content. It shows every card type. Cards are numbered from 0 in page order.

Set the colours at the top of `<job>/cards/cards.css` to match the supplied images (sample them with ffmpeg).

For a list that builds as the speaker goes, repeat the card with one more row or chip shown each time and mark the rest with class `off`.

Keep card text short. A row holds about 26 characters at full size.

### 5. Timeline

In `job.json`, fill in each video:

```json
"v1": {
  "src": "clip.mp4",
  "out": "1 - Short title (English).mp4",
  "trim": [0.9, 89.9],
  "timeline": [[12.1, 1], [19.6, 2], [26.8, 3]]
}
```

- `trim` cuts dead air at the start and end, in seconds of the source.
- `timeline` is `[second, card number]`. Take the seconds from the caption `.tsv`: a card should appear as the speaker starts the point it shows. Each card stays until the next one.
- Leave the intro empty: the first entry is the first real point.

### 6. Render and check

Preview first, because a full render takes about three minutes per 85 seconds of video:

```
python scripts/render.py <job> v1 --preview 15
```

Look at a frame from the preview. Then render in the background:

```
python scripts/render.py <job> v1
```

Run at most two renders at once. Never start a second batch while one is still writing the same output files. If you must stop a batch, stop the shell that is looping over the videos as well as ffmpeg, otherwise the loop carries on to the next video and overwrites your new render.

Check every finished video:

```
python scripts/sheet.py "<output.mp4>" <job>/frames/check_v1.jpg
```

The first frame of the sheet is at 3 seconds and must show no card.

### 7. Report

Give the user the list of output files and the words you were unsure of in each video. Mention if the source is low resolution, since upscaled WhatsApp video stays soft.

Tell them how to get the files onto the phone and posted, because this is where it failed before:

- Send the file as a **Document** in WhatsApp, or by Drive or cable. A normal WhatsApp video gets re-compressed.
- Upload it as it is. If they want a title or label on the video (for example "Vlog 71"), ask where it should go and burn it in with the render, so they do not need the app's editor.
- From a computer, studio.youtube.com publishes a vertical video under 3 minutes as a Short.

## Things that go wrong

- **"Couldn't export video" in the YouTube or Instagram app:** that message is the app's own editor failing to re-render the file after the user adds text or effects; it is not an upload rejection. `render.py` now writes a plain encode (Main profile, no B-frames, a keyframe every second) to make that re-render easier. This was not confirmed to cure the error, so if it happens again, also suggest uploading without in-app edits, sending the file uncompressed, and checking the phone's free storage. Do not make a second "phone-safe" copy; the normal output already is one.

- **ffmpeg filter script flag:** this ffmpeg needs `-/filter_complex file`, not the removed `-filter_complex_script`. `render.py` already does this.
- **Windows paths in ffmpeg filters:** a drive-letter colon breaks the `subtitles` filter. `render.py` changes into the job folder and uses relative paths, so keep fonts and captions inside the job folder.
- **faster-whisper audio decoding:** it fails with the installed PyAV. `transcribe.py` reads the 16 kHz WAV itself, so always pass it the WAV from `init_job.py`, not the video.
- **Output file shows 0 MB:** it is still rendering. Wait for the ffmpeg process to exit before judging.
- **Faces under the caption:** captions sit at about y=1150 and the card at y=1180 to 1612. If the speaker stands far from the camera their face can fall there; adjust `CELL_Y` in `render.py` and the caption `MarginV` in `captions.py` together.
