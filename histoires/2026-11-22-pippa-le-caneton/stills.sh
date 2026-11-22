#!/bin/bash
# Usage : ./stills.sh 3.5 10 16 22 28   -> planche contact vsheet.png pour vérifier
python3 anim_vert.py still "$@"
python3 - "$@" <<'PY'
import sys
from PIL import Image
ts=sys.argv[1:]
ims=[Image.open(f'vstill_{t}.png').resize((270,480),Image.NEAREST) for t in ts]
s=Image.new('RGB',(280*len(ims),480),'white')
for i,im in enumerate(ims): s.paste(im,(i*280,0))
s.save('vsheet.png')
PY
rm -f vstill_*.png
