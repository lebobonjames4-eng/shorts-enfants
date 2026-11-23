#!/bin/bash
# Installe la voix off (Piper, voix anglaise « lessac », hors ligne) dans ~/.cache/tts si elle n'y est pas.
# Téléchargements depuis les « releases » GitHub officielles de Piper (≈ 85 Mo, quelques secondes).
set -e
D=${TTS_DIR:-$HOME/.cache/tts}
mkdir -p "$D"
cd "$D"
if [ ! -x piper/piper ]; then
  curl -sSfL -o piper.tgz https://github.com/rhasspy/piper/releases/download/2023.11.14-2/piper_linux_x86_64.tar.gz
  tar xzf piper.tgz && rm piper.tgz
fi
if [ ! -s en-us-lessac-medium.onnx ]; then
  curl -sSfL -o lessac.tgz https://github.com/rhasspy/piper/releases/download/v0.0.2/voice-en-us-lessac-medium.tar.gz
  tar xzf lessac.tgz && rm lessac.tgz
fi
echo "Voix off prête : $D"
