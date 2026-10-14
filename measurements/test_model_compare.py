"""Geometric checks independent of the donor model and implementation shapes."""
import importlib.util
import json
import tempfile
from pathlib import Path
import numpy as np

spec=importlib.util.spec_from_file_location("model_compare",Path(__file__).with_name("model_compare.py"))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

def box(x,z):
    p=np.array([[-x,0,-z],[x,0,-z],[x,1,-z],[-x,1,-z],[-x,0,z],[x,0,z],[x,1,z],[-x,1,z]])
    f=np.array([[0,1,2],[0,2,3],[4,6,5],[4,7,6],[0,4,5],[0,5,1],
        [3,2,6],[3,6,7],[0,3,7],[0,7,4],[1,5,6],[1,6,2]])
    return p,f

def main():
    p,f=box(.3,.2)
    # Subdivide every triangle: topology differs, but triangle-plane extents must agree.
    mids=p[f].mean(1);p2=np.concatenate([p,mids]);f2=[]
    for i,(a,b,c) in enumerate(f):f2.extend([[a,b,len(p)+i],[b,c,len(p)+i],[c,a,len(p)+i]])
    a=m.cross_sections(p,f,[.13,.5,.87]);b=m.cross_sections(p2,np.array(f2),[.13,.5,.87])
    for sa,sb in zip(a,b):
        assert abs(sa["width"]-.6)<1e-10 and abs(sa["depth"]-.4)<1e-10
        assert abs(sa["width"]-sb["width"])<1e-10 and abs(sa["depth"]-sb["depth"])<1e-10
    config={"right_axis":"z","up_axis":"y","front_axis":"x","landmarks":{}}
    _,cal=m.calibrated(p,config);assert cal["status"]=="needs_calibration"
    config.update({"midline_origin":[0,0,0],"landmarks":{"head_top":[0,1,0],"feet_bottom":[0,0,0]}})
    transformed,cal=m.calibrated(p,config)
    assert cal["height_source_units"]==1
    section=m.cross_sections(transformed,f,[.5])[0]
    assert abs(section["width"]-.4)<1e-10 and abs(section["depth"]-.6)<1e-10
    section=m.cross_sections(p,f,[.5],{"lateral_range":[-.05,.05]})[0]
    assert abs(section["width"]-.1)<1e-10 and abs(section["depth"]-.4)<1e-10
    ids,cc=m.components(np.concatenate([p,p+[3,0,0]]),np.concatenate([f,f+len(p)]))
    assert len(cc)==2 and sorted(c["vertices"] for c in cc)==[8,8]
    result={"passed":True,"checks":["different topology preserves cross-section descriptors",
        "source-axis calibration swaps lateral/depth correctly","missing landmarks withhold normalization",
        "narrow ROI clips crossing section segments exactly","disconnected props remain separate topology components"]}
    Path(__file__).with_name("verification.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
    print(json.dumps(result))

if __name__=="__main__":main()
