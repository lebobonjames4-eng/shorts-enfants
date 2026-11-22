#!/bin/bash
# Compilation horizontale (16:9, 1920x1080) de plusieurs histoires, pour une vidéo YouTube longue.
# Usage (depuis la racine du dépôt) :
#   ./compile.sh videos/compil-AAAA-MM-JJ.mp4 histoires/2026-11-18-* histoires/2026-11-19-* ...
set -e
OUT=$1; shift
ROOT=$(pwd)
TMP=$(mktemp -d)
i=0
for DIR in "$@"; do
  i=$((i+1))
  (
    cd "$DIR"
    N=$(python3 -c "import story; print(int(story.DURATION*30))")
    python3 anim_pixel.py run 0 $N | ffmpeg -y -loglevel error -f rawvideo -pix_fmt rgb24 -s 1280x720 -r 30 -i - \
      -vf "scale=1920:1080:flags=neighbor" -c:v libx264 -crf 18 -preset veryfast -pix_fmt yuv420p "$TMP/v$i.mp4"
    python3 audio_mix.py && mv music_mix.wav "$TMP/a$i.wav"
    ffmpeg -y -loglevel error -i "$TMP/v$i.mp4" -i "$TMP/a$i.wav" -map 0:v -map 1:a -c:v copy -af volume=-3dB \
      -c:a aac -b:a 160k -ar 44100 -shortest "$TMP/p$i.mp4"
    rm -rf __pycache__
  ) &
  [ $((i % 3)) -eq 0 ] && wait
done
wait
: > "$TMP/list.txt"
for k in $(seq 1 $i); do
  [ -s "$TMP/p$k.mp4" ] || { echo "histoire $k manquante"; exit 1; }
  echo "file '$TMP/p$k.mp4'" >> "$TMP/list.txt"
done
ffmpeg -y -loglevel error -f concat -safe 0 -i "$TMP/list.txt" -c copy "$ROOT/$OUT"
rm -rf "$TMP"
ffprobe -v error -show_entries format=duration -show_entries stream=width,height -of compact "$ROOT/$OUT"
