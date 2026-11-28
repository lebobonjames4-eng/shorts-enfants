#!/bin/bash
# Usage : ./build_long.sh sortie.mp4      (à lancer dans le dossier de l'histoire)
# Fabrique la vidéo LONGUE horizontale 16:9 1920x1080, durée = story.DURATION, 30 i/s, avec musique et voix.
# Le rendu est découpé en segments calculés en parallèle (un par cœur).
set -e
OUT=${1:-long.mp4}
N=$(python3 -c "import story; print(int(story.DURATION*30))")
J=${JOBS:-$(nproc)}
B=( $(python3 -c "n=$N; j=$J; print(*[round(n*k/j) for k in range(j+1)])") )
rm -f s_*.mp4
for ((k=0; k<J; k++)); do
  ( python3 anim_pixel.py run ${B[$k]} ${B[$((k+1))]} | ffmpeg -y -loglevel error -f rawvideo -pix_fmt rgb24 \
      -s 1280x720 -r 30 -i - -vf "scale=1920:1080:flags=neighbor" -c:v libx264 -crf 18 -preset veryfast \
      -pix_fmt yuv420p -r 30 tmp_s$k.mp4 && mv tmp_s$k.mp4 s_$(printf %03d $k).mp4 ) &
done
wait
: > list_s.txt
for ((k=0; k<J; k++)); do
  f=s_$(printf %03d $k).mp4
  [ -s $f ] || { echo "segment $k manquant"; exit 1; }
  echo "file $f" >> list_s.txt
done
ffmpeg -y -loglevel error -f concat -safe 0 -i list_s.txt -c copy video_h.mp4
python3 audio_mix.py
ffmpeg -y -loglevel error -i video_h.mp4 -i music_mix.wav -map 0:v -map 1:a -c:v copy -af volume=-3dB -c:a aac -b:a 160k -shortest tmp_out.mp4
mv tmp_out.mp4 "$OUT"
rm -f s_*.mp4 list_s.txt video_h.mp4 music_mix.wav
ffprobe -v error -show_entries format=duration -show_entries stream=width,height -of compact "$OUT"
