#!/bin/bash
# Usage : ./stills_long.sh 0 12 30 55 80 110 140   -> planche contact hsheet.png (version 16:9) pour vérifier
python3 anim_pixel.py still "$@"
python3 - "$@" <<'PY'
import sys
from PIL import Image
ts=sys.argv[1:]
ims=[Image.open(f'still_{t}.png').resize((640,360),Image.NEAREST) for t in ts]
cols=3; rows=(len(ims)+cols-1)//cols
s=Image.new('RGB',(650*cols,370*rows),'white')
for i,im in enumerate(ims): s.paste(im,((i%cols)*650,(i//cols)*370))
s.save('hsheet.png')
PY
rm -f still_*.png
