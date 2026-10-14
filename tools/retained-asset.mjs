/** Read a retained review asset without expanding the repository on disk. */
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {gunzipSync} from 'node:zlib';
import {fileURLToPath} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const mapPath=path.join(root,'data/asset-map.json');
const entries=fs.existsSync(mapPath)?JSON.parse(fs.readFileSync(mapPath,'utf8')).assets:{};
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
export function readRetainedAsset(filename){
  const absolute=filename instanceof URL?fileURLToPath(filename):path.resolve(filename);
  const route=path.relative(root,absolute).split(path.sep).join('/');
  const entry=entries[route];
  if(!entry)return fs.readFileSync(absolute);
  const stored=fs.readFileSync(path.join(root,entry.storage));
  if(sha(stored)!==entry.stored_sha256)throw Error('Stored asset checksum mismatch: '+route);
  let raw=entry.codec==='file'?stored:gunzipSync(stored);
  if(['shuffle32','delta-zigzag-shuffle32'].includes(entry.encoding)){
    if(raw.length%4)throw Error('Invalid shuffle alignment');
    const out=Buffer.alloc(raw.length),n=raw.length/4;
    for(let k=0;k<4;k++)for(let i=0;i<n;i++)out[4*i+k]=raw[k*n+i];
    raw=out;
  }
  if(entry.encoding==='delta-zigzag-shuffle32'){
    let accumulator=0;
    for(let i=0;i<raw.length;i+=4){const v=raw.readUInt32LE(i);accumulator+=(v>>>1)^-(v&1);if(accumulator<0||accumulator>0xffffffff)throw Error('Index delta overflow');raw.writeUInt32LE(accumulator,i);}
  }
  if(entry.codec==='sparse-point-f32'){
    if(raw.toString('ascii',0,4)!=='RSP1')throw Error('Invalid sparse payload');
    const n=raw.readUInt32LE(4),count=raw.readUInt32LE(8);
    if(raw.length!==12+count*16)throw Error('Invalid sparse payload size');
    const out=Buffer.from(readRetainedAsset(path.join(root,entry.base)));
    if(out.length!==n*12)throw Error('Sparse base size mismatch');
    for(let j=0;j<count;j++){const i=raw.readUInt32LE(12+4*j);if(i>=n)throw Error('Invalid sparse index');if(entry.point_values_encoding==='xor-baseline-uint32'){for(let axis=0;axis<3;axis++){const at=i*12+axis*4;out.writeUInt32LE((out.readUInt32LE(at)^raw.readUInt32LE(12+4*count+12*j+axis*4))>>>0,at)}}else if(entry.point_values_encoding===undefined)raw.copy(out,i*12,12+4*count+12*j,12+4*count+12*(j+1));else throw Error('Unknown sparse point encoding');}
    raw=out;
  }else if(!['file','gzip'].includes(entry.codec))throw Error('Unknown retained asset codec');
  if(raw.length!==entry.decoded_bytes||sha(raw)!==entry.decoded_sha256)throw Error('Decoded asset checksum mismatch: '+route);
  return raw;
}
