#!/bin/bash
# Usage : ./build.sh sortie.mp4      (à lancer dans le dossier de l'histoire)
# Fabrique la vidéo verticale 1080x1920, 30 s, 30 i/s, avec musique et voix.
set -e
OUT=${1:-short.mp4}
seg() { python3 anim_vert.py run $2 $3 | ffmpeg -y -loglevel error -f rawvideo -pix_fmt rgb24 -s 1080x1920 -r 30 -i - -c:v libx264 -crf 18 -preset veryfast -pix_fmt yuv420p -r 30 tmp_v$1.mp4 && mv tmp_v$1.mp4 v$1.mp4; }
(seg 1 0 150; seg 3 360 600; seg 5 810 900) & (seg 2 150 360; seg 4 600 810) & wait
for i in 1 2 3 4 5; do [ -s v$i.mp4 ] || { echo "segment $i manquant"; exit 1; }; done
printf "file v1.mp4\nfile v2.mp4\nfile v3.mp4\nfile v4.mp4\nfile v5.mp4\n" > list_v.txt
ffmpeg -y -loglevel error -f concat -safe 0 -i list_v.txt -c copy video_v.mp4
python3 audio_mix.py
ffmpeg -y -loglevel error -i video_v.mp4 -i music_mix.wav -map 0:v -map 1:a -c:v copy -af volume=-3dB -c:a aac -b:a 160k -shortest tmp_out.mp4
mv tmp_out.mp4 "$OUT"
rm -f v?.mp4 list_v.txt video_v.mp4 music_mix.wav
ffprobe -v error -show_entries format=duration -show_entries stream=width,height -of compact "$OUT"
