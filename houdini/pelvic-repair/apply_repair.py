"""NumPy-only application of the baked local structural repair to source states.

Compatible with Houdini's bundled Python: SciPy is needed only to regenerate
the bind recipe, never to cook this application function.
"""
from pathlib import Path
from functools import lru_cache
import numpy as np
ROOT=Path(__file__).resolve().parent

@lru_cache(maxsize=4)
def load_recipe(path=None):
    with np.load(path or ROOT/'implicit-repair-recipe.npz') as data:
        return {k:data[k] for k in data.files}

def apply(source_positions,recipe=None):
    r=recipe or load_recipe()
    source=np.asarray(source_positions,dtype='<f4')
    if source.shape!=(int(r['source_count']),3):
        raise ValueError('Repair expects the original proxy source point order')
    delta=source-r['baseline_source']
    offset=(delta[r['nearest_source']]*r['weights'][:,:,None]).sum(1)
    return np.vstack((source,r['new_baseline']+offset)).astype('<f4'),r['triangles']
