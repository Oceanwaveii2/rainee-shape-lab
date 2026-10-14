from pathlib import Path
import cv2,json
from PIL import Image,ImageDraw
root=Path(__file__).resolve().parent/'research'
root.mkdir(exist_ok=True)
names=['VeniceAI_1rjp0ky.mp4','grok-video-69315bad-8ad2-4e94-9377-02314b2270d6_5.mp4','dreamina-2026-03-30-4632-_The_character_from_Image1_strictly_....mp4','dreamina-2026-03-30-5816-Image1_as_character_reference._Maintain....mp4','dreamina-2026-03-30-1713-Image1_is_the_character_reference._Pixa....mp4','dreamina-2026-03-30-8847-_Image1_is_the_character_reference._Pix....mp4']
rows=[]
for j,name in enumerate(names):
 path=Path('C:/Users/User/Downloads')/name
 cap=cv2.VideoCapture(str(path)); fps=cap.get(cv2.CAP_PROP_FPS);count=int(cap.get(cv2.CAP_PROP_FRAME_COUNT));duration=count/fps if fps else 0
 row={'file':str(path),'fps':fps,'frames':count,'duration':duration,'samples':[]}
 sheet=Image.new('RGB',(1500,530),'#15151a');draw=ImageDraw.Draw(sheet);draw.text((12,8),f'{j+1}: {name}',fill='white')
 for k,f in enumerate([.05,.25,.5,.75,.95]):
  frame=round(max(count-1,0)*f);cap.set(cv2.CAP_PROP_POS_FRAMES,frame);ok,a=cap.read()
  if not ok:continue
  img=Image.fromarray(cv2.cvtColor(a,cv2.COLOR_BGR2RGB));img.thumbnail((292,470));sheet.paste(img,(k*300+(300-img.width)//2,35+(470-img.height)//2));draw.text((k*300+12,508),f'{frame/fps:.2f}s',fill='white');row['samples'].append(frame/fps)
 cap.release();sheet.save(root/f'video-{j+1}-samples.jpg',quality=92);rows.append(row)
(root/'video-inventory.json').write_text(json.dumps(rows,indent=2))
print(json.dumps(rows,indent=2))
