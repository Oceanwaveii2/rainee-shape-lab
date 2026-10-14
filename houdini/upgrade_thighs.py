"""Create v2 from the verified v1 without changing the upstream simulation."""
import hou,pathlib,json
from thigh_setup import install
r=pathlib.Path(__file__).resolve().parent
hou.hipFile.load(str(r/'Rainee-Volume-Lab.hip'),suppress_save_prompt=True)
geo=hou.node('/obj/RAINEE');install(geo,r);hou.setFrame(1)
hou.hipFile.save(str(r/'Rainee-Volume-Lab-v2.hip'))
geo.node('OUT_NORMALIZED').cook(force=True)
assert not geo.node('INDEPENDENT_THIGHS').errors()
print(json.dumps({'scene':str(r/'Rainee-Volume-Lab-v2.hip'),'thigh_default':geo.node('CONTROLS').evalParm('thigh_fullness'),'errors':geo.node('INDEPENDENT_THIGHS').errors()}),flush=True)
