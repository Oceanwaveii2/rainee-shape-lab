"""Independent checks for safe paths, signed SPZ decoding and gzip-only variants."""
import gzip,hashlib,json,struct
from pathlib import Path
import numpy as np
from import_worldgen import safe_name,spz_header,decode_positions

def main():
    fixed=np.array([[-1024,2048,-4096],[4096,-8192,18432]],dtype=np.int32)
    xyz=bytearray()
    for v in fixed.ravel():
        v=int(v)&0xffffff;xyz.extend((v&255,(v>>8)&255,(v>>16)&255))
    raw=struct.pack('<III4B',0x5053474e,3,2,0,12,0,0)+bytes(xyz)+bytes([64,255])+bytes([128]*6)+bytes([160]*6)+bytes([0]*8)
    a=gzip.compress(raw,mtime=0);b=gzip.compress(raw,mtime=1)
    ha,ra=spz_header(a);hb,rb=spz_header(b)
    assert hashlib.sha256(a).digest()!=hashlib.sha256(b).digest()
    assert ha['raw_payload_sha256']==hb['raw_payload_sha256']
    p,alpha,color,scale=decode_positions(ra,ha)
    assert np.allclose(p,fixed/4096.)
    assert alpha.tolist()==[64,255] and scale.shape==(2,3)
    rejected=[]
    for name in ('../outside.spz','C:/outside.spz','/outside.spz','folder/../../outside.glb'):
        try:safe_name(name)
        except ValueError:rejected.append(name)
    assert len(rejected)==4
    assert safe_name('pack\\gaussian_splatting\\full_res.spz')=='pack/gaussian_splatting/full_res.spz'
    try:spz_header(gzip.compress(raw[:-5]))
    except ValueError:pass
    else:raise AssertionError('Truncated attributes accepted')
    result={'passed':True,'checks':['signed 24-bit fixed-point positions match known values',
        'gzip timestamp variants deduplicate by raw payload hash','unsafe archive paths rejected',
        'truncated SPZ attributes rejected'],
        'scope':'importer correctness only; no anatomical volume or renderer fidelity claim'}
    Path(__file__).with_name('verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result))
if __name__=='__main__':main()
