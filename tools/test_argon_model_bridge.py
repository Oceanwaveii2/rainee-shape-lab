"""Meaningful bridge contract regressions; full source arrays verified separately."""
from pathlib import Path
import importlib.util, tempfile, hashlib, json, lzma, struct
import numpy as np
import argon_model_bridge as bridge

def packed_fixture(raw,encoding,width,**extra):
 packed=np.frombuffer(raw,dtype='u1').reshape(-1,width).T.copy().tobytes();compressed=lzma.compress(packed);temp=tempfile.NamedTemporaryFile(dir=bridge.ROOT,delete=False,suffix='.xz');temp.write(compressed);temp.close();p=Path(temp.name)
 return p,{'path':p.relative_to(bridge.ROOT).as_posix(),'compression':'xz','encoding':encoding,'shuffle_word':width,'stored_sha256':hashlib.sha256(compressed).hexdigest(),**extra}

def check_exact_decimal_negative_zero():
 q=np.array([0,-123456,1234567],dtype='<i4');expected=np.array([-0.,-.123456,1.234567],dtype='<f8').tobytes();p,d=packed_fixture(q.tobytes(),'decimal-i32-f64-exact',4,scale=1000000,negative_zero_indices=[0],decoded_bytes=len(expected),decoded_sha256=hashlib.sha256(expected).hexdigest())
 try:
  assert bridge.read_geometry_buffer(d)==expected;bad={**d,'negative_zero_indices':[]}
  try:bridge.read_geometry_buffer(bad);raise AssertionError('Lost sign bit accepted')
  except ValueError:pass
  bad={**d,'stored_sha256':'0'*64}
  try:bridge.read_geometry_buffer(bad);raise AssertionError('Bad blob accepted')
  except ValueError:pass
 finally:p.unlink()

def check_exact_f32_widening():
 values=np.array([-0.,-.3,1.25],dtype='<f4');expected=values.astype('<f8').tobytes();p,d=packed_fixture(values.tobytes(),'f32-to-f64-exact',4,decoded_bytes=len(expected),decoded_sha256=hashlib.sha256(expected).hexdigest())
 try:assert bridge.read_geometry_buffer(d)==expected
 finally:p.unlink()

def check_triangles_and_adapters():
 for mid in ['R05-new-obj','R06-new-fbx']:
  m,p,t=bridge.read_model(mid);assert len(p)==m['geometry']['positions']['vertices']*24;assert len(t)==m['geometry']['triangles']['triangles']*12
 for mid in ['C00-working-body','N0000','N0010','N0018','N0026']:
  report=bridge.inspect(mid);assert abs(report['canonical_rest_referenced_bounds']['span'][1]-1)<1e-12;assert report['anatomical_volume']is None;assert report['physical_unit_calibration']is None
 try:bridge.entry('../../outside');raise AssertionError('Unknown model accepted')
 except ValueError:pass
 with tempfile.TemporaryDirectory()as temp:
  target=Path(temp)/'source.obj';target.write_text('existing')
  try:bridge.export_obj('T00-inspection-proxy',target);raise AssertionError('Existing export overwritten')
  except ValueError:pass
  assert target.read_text()=='existing'

if __name__=='__main__':
 check_exact_decimal_negative_zero();check_exact_f32_widening();check_triangles_and_adapters();print(json.dumps({'passed':True,'groups':3,'scope':'Exact float64 reconstruction/sign bits, blob checksums, new full-model counts, original stature adapters, unknown-ID rejection and no export overwrite'}))
