"""Serve a lossless lean review bundle, restoring virtual binary asset URLs.
The map contains only explicit relative routes. Bind loopback only.
"""
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from pathlib import Path,PurePosixPath
from functools import lru_cache,partial
from urllib.parse import urlsplit,unquote
import argparse, json, gzip, hashlib, struct, webbrowser,sys
from array import array

def unshuffle32(raw):
 if len(raw)%4:raise ValueError('Shuffle payload alignment failure')
 n=len(raw)//4;out=bytearray(len(raw))
 for k in range(4):out[k::4]=raw[k*n:(k+1)*n]
 return bytes(out)

def decode(root,entry,entries,cache=None):
 storage=(root/entry['storage']).resolve()
 if not storage.is_relative_to(root.resolve()):raise ValueError('Storage path outside bundle')
 raw=storage.read_bytes()
 if hashlib.sha256(raw).hexdigest()!=entry['stored_sha256']:raise ValueError('Compressed asset integrity failure')
 if entry['codec']=='file':out=raw
 else:
  raw=gzip.decompress(raw)
  encoding=entry.get('encoding','bytes')
  if encoding in ['shuffle32','delta-zigzag-shuffle32']:raw=unshuffle32(raw)
  if encoding=='delta-zigzag-shuffle32':
   values=array('I');values.frombytes(raw)
   if sys.byteorder!='little':values.byteswap()
   accumulator=0
   for i,v in enumerate(values):
    accumulator+=(v>>1)^-(v&1)
    if not 0<=accumulator<=0xffffffff:raise ValueError('Index-delta overflow')
    values[i]=accumulator
   if sys.byteorder!='little':values.byteswap()
   raw=values.tobytes()
  if entry['codec']=='gzip':out=raw
  elif entry['codec']=='sparse-point-f32':
   magic,n,count=struct.unpack_from('<4sII',raw)
   if magic!=b'RSP1' or len(raw)!=12+count*16:raise ValueError('Sparse payload header/length mismatch')
   base=cache(entry['base']) if cache else decode(root,entries[entry['base']],entries)
   if len(base)!=n*12:raise ValueError('Sparse base length mismatch')
   out=bytearray(base);offset=12+count*4
   for j in range(count):
    i=struct.unpack_from('<I',raw,12+j*4)[0]
    if i>=n:raise ValueError('Sparse vertex index outside base')
    if entry.get('point_values_encoding')=='xor-baseline-uint32':
     for axis in range(3):
      at=i*12+axis*4;value=struct.unpack_from('<I',base,at)[0]^struct.unpack_from('<I',raw,offset+j*12+axis*4)[0];struct.pack_into('<I',out,at,value)
    elif entry.get('point_values_encoding') is None:out[i*12:i*12+12]=raw[offset+j*12:offset+j*12+12]
    else:raise ValueError('Unknown sparse point encoding')
   out=bytes(out)
  else:raise ValueError('Unknown asset codec')
 if len(out)!=entry['decoded_bytes'] or hashlib.sha256(out).hexdigest()!=entry['decoded_sha256']:raise ValueError('Restored asset integrity failure')
 return out

def make_handler(root,quiet=False):
 entries=json.loads((root/'data/asset-map.json').read_text(encoding='utf-8'))['assets']
 @lru_cache(maxsize=5)
 def load(route):return decode(root,entries[route],entries,load)
 class Handler(SimpleHTTPRequestHandler):
  def __init__(self,*args,**kwargs):super().__init__(*args,directory=str(root),**kwargs)
  def asset(self,head=False):
   route=unquote(urlsplit(self.path).path).lstrip('/')
   if route not in entries:return False
   try:raw=load(route)
   except (OSError,ValueError) as e:self.send_error(500,str(e));return True
   self.send_response(200);self.send_header('Content-Type',entries[route].get('content_type',self.guess_type(route)));self.send_header('Content-Length',str(len(raw)));self.send_header('Cache-Control','no-cache');self.send_header('X-Rainee-Asset-SHA256',entries[route]['decoded_sha256']);self.end_headers()
   if not head:self.wfile.write(raw)
   return True
  def do_GET(self):
   if not self.asset():super().do_GET()
  def do_HEAD(self):
   if not self.asset(head=True):super().do_HEAD()
  def log_message(self,*args):
   if not quiet:super().log_message(*args)
 return Handler
def main():
 p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=5197);p.add_argument('--open',action='store_true');args=p.parse_args();root=Path(__file__).resolve().parent
 server=ThreadingHTTPServer(('127.0.0.1',args.port),make_handler(root))
 print(f'Rainee lean review: http://127.0.0.1:{args.port}',flush=True)
 if args.open:webbrowser.open(f'http://127.0.0.1:{args.port}/')
 server.serve_forever()
if __name__=='__main__':main()
