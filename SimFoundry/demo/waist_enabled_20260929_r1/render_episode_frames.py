"""Extract requested RGB frames for actual review; does not approve data."""
from pathlib import Path
import json,sys,zipfile,hashlib
import numpy as np
from PIL import Image,ImageDraw
p=Path(sys.argv[1]);times=sorted(set(map(int,sys.argv[2:])));assert times and min(times)>=0
canvas=Image.new('RGB',(1280,270*((len(times)+3)//4)));draw=ImageDraw.Draw(canvas)
with zipfile.ZipFile(p/'raw.npz') as z,z.open('rgb.npy') as stream:
 version=np.lib.format.read_magic(stream);shape,order,dtype=np.lib.format.read_array_header_1_0(stream) if version==(1,0) else np.lib.format.read_array_header_2_0(stream)
 assert not order and dtype==np.dtype('uint8') and shape[1]==3 and max(times)<shape[0]
 count=int(np.prod(shape[1:]));prior=-1
 for i,t in enumerate(times):
  skip=(t-prior-1)*count
  while skip:
   data=stream.read(min(skip,8*1024*1024));assert data;skip-=len(data)
  data=stream.read(count);assert len(data)==count
  rgb=np.frombuffer(data,dtype=dtype).reshape(shape[1:]).transpose(1,2,0);canvas.paste(Image.fromarray(rgb).resize((320,240)),((i%4)*320,(i//4)*270));draw.text(((i%4)*320,(i//4)*270+242),str(t));prior=t
out=p/'REVIEW_EVENTS.jpg';canvas.save(out);(p/'EVENT_REVIEW.json').write_text(json.dumps(dict(frames=times,image_sha256=hashlib.sha256(out.read_bytes()).hexdigest(),actual_review='pending',training_ready=False),indent=2))
