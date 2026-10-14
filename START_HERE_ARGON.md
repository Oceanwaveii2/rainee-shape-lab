# Argon full-body processing packet

Read [the complete handoff](documentation/ARGON_FULL_BODY_HANDOFF.md) first. It contains the full-body scope, model bridge, verified lessons, research boundaries, proposed processing contracts and acceptance gates.

- [Model registry](models/full-body-bridge/registry.json): 16 retained representations with explicit roles and coordinates.
- [Model bridge verification](documentation/full-body-bridge-verification.json): exact decoded geometry, finite coordinates, index validity, bounds and geometric area.
- [App and source data guide](README.md): server launch and visual tools.
- [Local original lookup](documentation/LOCAL_DATA.md): complete dense FBX, original donors, textures, videos and Gaussian scenes.

```sh
python tools/argon_model_bridge.py list
python tools/argon_model_bridge.py verify --out expanded/verification.json
python tools/argon_model_bridge.py export --id R05-new-obj --out expanded/R05.obj
python tools/argon_model_bridge.py export --id R06-new-fbx --out expanded/R06.obj
python serve.py --port 5199
```

Python standard library suffices for reading/exporting; inspection requires NumPy. The app remains a regional studio with a full-body data bridge; anatomical fitting/registration/rigging are future work. Original dense template geometry is local-only; its inspection proxy is labeled lossy. Complete geometry of both new donors is included. The verified transfer ZIP stays under 100,000,000 bytes; expanded data is larger.
