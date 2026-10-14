# Large files split for GitHub

GitHub rejects any single file over 100 MB. On 2026-10-15 a push failed because of one rendered reel:

- `instagram/5 - DAMAC Sorrento and DAMAC Islands 2 townhouses.mp4` (233,815,092 bytes)

That file is not in git. It sits in `.gitignore`, and the repo holds it as three raw byte chunks made with `split -b 90M`:

```
instagram/5 - DAMAC Sorrento and DAMAC Islands 2 townhouses.mp4.part00   (90 MB)
instagram/5 - DAMAC Sorrento and DAMAC Islands 2 townhouses.mp4.part01   (90 MB)
instagram/5 - DAMAC Sorrento and DAMAC Islands 2 townhouses.mp4.part02   (43 MB)
```

The parts are plain binary slices, not playable videos on their own. Joining them in order gives back the original byte for byte (checked with `cmp` before the push).

## Rebuild the video

Git Bash, macOS or Linux:

```bash
cd instagram
cat "5 - DAMAC Sorrento and DAMAC Islands 2 townhouses.mp4".part* > "5 - DAMAC Sorrento and DAMAC Islands 2 townhouses.mp4"
```

Windows cmd:

```bat
cd instagram
copy /b "5 - DAMAC Sorrento and DAMAC Islands 2 townhouses.mp4.part00"+"5 - DAMAC Sorrento and DAMAC Islands 2 townhouses.mp4.part01"+"5 - DAMAC Sorrento and DAMAC Islands 2 townhouses.mp4.part02" "5 - DAMAC Sorrento and DAMAC Islands 2 townhouses.mp4"
```

## For the next agent

- Check sizes before committing new renders: `find . -name '*.mp4' -size +95M -not -path './.git/*'`.
- Anything over 100 MB gets the same treatment. Split with `split -b 90M -d -a 2 "<file>" "<file>.part"`, verify with `cat "<file>".part* | cmp - "<file>"`, add the original to `.gitignore`, and list it in this file.
- If you re-render video 5, delete the old parts and split the new file again. Stale parts will rebuild the old video.
- Git LFS was considered and skipped. The free tier caps at 1 GB of storage and bandwidth a month, and this repo already holds more video than that.
