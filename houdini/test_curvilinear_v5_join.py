"""Independent C1 join and invalid-input regression for v5's regional base map.

This tests the join that fails with high width and low separation. It does not
certify a global injective map, anatomical fit or continuous growth simulation.
"""
import json
from pathlib import Path
import sys
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
from curvilinear_rear_v5 import deform_v5_base, deform_v5, jacobian_screen_v5, fix_vdb_triangle_winding


def raises(fn):
    try:fn()
    except (ValueError,TypeError):return
    raise AssertionError('Invalid numerical input was accepted')


def main():
    cx=.073;eps=1e-7;max_jump=0.0;cases=0
    # All points lie inside the flat regional support, so this isolates the
    # inner/outer branch join rather than a shrinking ROI transition.
    for amp in (.1,.5,1.,1.5):
        for lateral in (.4,1.08,1.6):
            for separation in (0.,.26,.6):
                controls={'cleft_x_offset':0.,'lateral':lateral,'separation':separation,'hip_flare':1.5,'roundness':0.}
                x=cx+eps*np.arange(-2,3)
                points=np.column_stack((x,np.full(5,.605),np.full(5,-.08)))
                out=deform_v5_base(points,amp,controls)[:,0]
                left=(3*out[2]-4*out[1]+out[0])/(2*eps)
                right=(-3*out[2]+4*out[3]-out[4])/(2*eps)
                jump=abs(left-right);max_jump=max(jump,max_jump)
                assert jump<1e-5, f'Join derivative jump={jump}, controls={controls}, amp={amp}'
                assert left>0 and right>0
                grid=np.linspace(0,.115,1001)
                mapped=deform_v5_base(np.column_stack((grid,np.full(len(grid),.605),np.full(len(grid),-.08))),amp,controls)[:,0]
                assert np.all(np.diff(mapped)>=-1e-12),'Inner/outer local map ceased to be monotone'
                cases+=1
    points=np.array([[.08,.605,-.08]])
    for control in ({'lateral':float('nan')},{'roundness':-1},{'cleft_hold':2},{'separation':-.1}):
        raises(lambda:deform_v5(points,.5,control))
    for steps in (0,-1,2.5,True,513):raises(lambda:deform_v5(points,.5,steps=steps))
    raises(lambda:deform_v5(points,float('nan')))
    raises(lambda:deform_v5(np.full((1,3),np.nan),.5))
    raises(lambda:jacobian_screen_v5(points,.5,epsilon=0))
    assert np.array_equal(deform_v5(points,0),points)
    source=np.array([[0,1,2]],dtype=np.uint32)
    positions=np.array([[0,0,0],[1,0,0],[0,1,0]],dtype=float)
    candidate,count=fix_vdb_triangle_winding(positions,source,vdb_vertex_start=0)
    assert np.array_equal(source,[[0,1,2]]) and not np.shares_memory(source,candidate)
    print(json.dumps({'passed':True,'join_cases':cases,'max_one_sided_derivative_difference':max_jump,
        'checks':['C1 inner/outer join under high lateral expansion and zero separation',
            'local branch monotonicity across bounded sampled controls','nonfinite controls and invalid RK4 steps rejected',
            'zero amplitude preserves source points','winding proposals do not mutate source indices'],
        'scope':'Regional base-map join and synthetic input validation, not global foldover, topology or likeness certification'}))


if __name__=='__main__':main()
