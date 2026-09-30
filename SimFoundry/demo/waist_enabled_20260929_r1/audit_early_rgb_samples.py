"""Prepare early RGB evidence by streaming only first121 frames; no approval."""
from pathlib import Path
import sys,json,zipfile,hashlib
import numpy as np
from PIL import Image,ImageDraw
run=Path(sys.argv[1]);times=[0,15,30,45,60,75,90,120];records=[]
for ep in sorted(run.glob('case_*/layout_*')):
 p=ep/'raw.npz'
 if not p.exists():continue
 canvas=Image.new('RGB',(1280,540));draw=ImageDraw.Draw(canvas)
 with zipfile.ZipFile(p) as z,z.open('rgb.npy') as stream:
  version=np.lib.format.read_magic(stream);shape,fortran,dtype=(np.lib.format.read_array_header_1_0(stream) if version==(1,0) else np.lib.format.read_array_header_2_0(stream))
  assert not fortran and shape[1]==3 and dtype==np.dtype('uint8'),(shape,dtype)
  frame_bytes=int(np.prod(shape[1:]));previous=-1
  for i,t in enumerate(times):
   to_skip=(t-previous-1)*frame_bytes
   while to_skip:
    data=stream.read(min(to_skip,8*1024*1024));assert data;to_skip-=len(data)
   data=stream.read(frame_bytes);assert len(data)==frame_bytes
   rgb=np.frombuffer(data,dtype=dtype).reshape(shape[1:]).transpose(1,2,0)
   canvas.paste(Image.fromarray(rgb).resize((320,240)),((i%4)*320,(i//4)*270));draw.text(((i%4)*320,(i//4)*270+242),f'{ep.name} / {t}')
   previous=t
 path=ep/'REVIEW_EARLY.jpg';canvas.save(path)
 records.append(dict(episode=ep.name,frames=times,image_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),actual_review='pending'))
 print(ep.name,flush=True)
(run/'EARLY_RGB_REVIEW.json').write_text(json.dumps(dict(rows=records,actual_review='pending',training_ready=False),indent=2))
