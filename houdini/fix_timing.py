import hou,pathlib
r=pathlib.Path(__file__).resolve().parent
hou.hipFile.load(str(r/'Rainee-Volume-Lab.hip'),suppress_save_prompt=True)
n=hou.node('/obj/RAINEE/SOFT_MOTION/dopnet1/forces/FOLLOW_AUTHORED_REST_SHAPE')
n.parm('usetimestep').set(1)
hou.setFrame(1);hou.hipFile.save(str(r/'Rainee-Volume-Lab.hip'))
