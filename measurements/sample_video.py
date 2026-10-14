"""Save six uncropped reference frames and timing metadata; no motion inference."""
import argparse,json
from pathlib import Path
import cv2
from PIL import Image,ImageDraw

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("video");parser.add_argument("--out",required=True);args=parser.parse_args()
    source=Path(args.video);out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
    cap=cv2.VideoCapture(str(source));fps=cap.get(cv2.CAP_PROP_FPS);n=int(cap.get(cv2.CAP_PROP_FRAME_COUNT));source_width=int(cap.get(cv2.CAP_PROP_FRAME_WIDTH));source_height=int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    if fps<=0 or n<=0:raise ValueError("Could not decode video timing")
    indices=[round(i*(n-1)/5) for i in range(6)];images=[];samples=[]
    for i,frame in enumerate(indices):
        cap.set(cv2.CAP_PROP_POS_FRAMES,frame);ok,bgr=cap.read()
        if not ok:raise ValueError("Frame decode failed")
        im=Image.fromarray(cv2.cvtColor(bgr,cv2.COLOR_BGR2RGB));name=f"frame-{i}-{frame}.png";im.save(out/name)
        thumb=im.copy();thumb.thumbnail((480,640));images.append(thumb)
        samples.append({"source_frame":frame,"seconds":frame/fps,"file":name})
    cap.release();cw=max(x.width for x in images);ch=max(x.height for x in images)+28
    contact=Image.new("RGB",(cw*3,ch*2),(25,27,34));draw=ImageDraw.Draw(contact)
    for i,im in enumerate(images):
        x=(i%3)*cw+(cw-im.width)//2;y=(i//3)*ch+28
        contact.paste(im,(x,y));draw.text(((i%3)*cw+10,(i//3)*ch+8),f"{samples[i]['seconds']:.3f}s  frame {samples[i]['source_frame']}",fill="white")
    contact.save(out/"contact-sheet.png")
    (out/"video-info.json").write_text(json.dumps({"source":str(source.resolve()),"fps":fps,"frames":n,"duration_seconds":n/fps,
        "source_width":source_width,"source_height":source_height,"contact_sheet_tile_width":images[0].width,"contact_sheet_tile_height":images[0].height,"preview_sizes_are_resized_uncropped":True,"samples":samples,
        "scope":"Uniform time samples only. No camera calibration, physical motion reconstruction or shape-ratio measurements inferred."},indent=2),encoding="utf-8")
    print(f"Saved {len(samples)} uncropped frames; {n/fps:.3f} seconds at {fps:.3f} fps")
if __name__=="__main__":main()
