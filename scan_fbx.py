"""Inspect binary FBX structure without loading mesh arrays into a DCC."""
import struct, json, pathlib
SOURCE=pathlib.Path(r'C:\Users\User\Downloads\Core Body (Template Only).fbx')
def scan(path=SOURCE):
    result=[]
    with open(path,'rb') as f:
        header=f.read(23)
        if not header.startswith(b'Kaydara FBX Binary'): raise ValueError('Binary FBX required')
        version=struct.unpack('<I',f.read(4))[0]
        wide=version>=7500
        fmt='<QQQB' if wide else '<IIIB'; size=25 if wide else 13
        def node(parent=''):
            start=f.tell(); data=f.read(size)
            if len(data)!=size:return False
            end,count,plen,nlen=struct.unpack(fmt,data)
            if not end:return False
            name=f.read(nlen).decode('utf8','replace'); props=[]
            for _ in range(count):
                t=f.read(1).decode()
                if t in 'fdilbc':
                    n,enc,length=struct.unpack('<III',f.read(12)); offset=f.tell()
                    props.append({'array':t,'count':n,'encoding':enc,'length':length,'offset':offset});f.seek(length,1)
                elif t in 'SR':
                    n=struct.unpack('<I',f.read(4))[0]
                    if t=='S' and n<4096: props.append(f.read(n).decode('utf8','replace'))
                    else:props.append({'blob':n}); f.seek(n,1)
                else:
                    typ={'Y':'h','C':'?','I':'i','F':'f','D':'d','L':'q'}[t]
                    props.append(struct.unpack('<'+typ,f.read(struct.calcsize(typ)))[0])
            route=parent+'/'+name
            result.append({'path':route,'start':start,'end':end,'props':props})
            while f.tell()<end-size:
                if not node(route):break
            f.seek(end);return True
        while node():pass
    return {'version':version,'nodes':result}
if __name__=='__main__':
    data=scan();pathlib.Path(__file__).with_name('fbx-structure.json').write_text(json.dumps(data,indent=2))
    for n in data['nodes']:
        if n['path'] in ['/Objects/Geometry','/Objects/Model'] or n['path'].endswith(('/Vertices','/PolygonVertexIndex')):print(n)
