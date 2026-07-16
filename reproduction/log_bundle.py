#!/usr/bin/env python3
from pathlib import Path
import json,trackio
ROOT=Path(__file__).resolve().parents[1]
trackio.init(project="isolation-forest-inductive-bias-repro",name="cpu-three-claim-reproduction",
 config={"openreview_id":"J0y3sNbo9G","claims":3,"device":"cpu","trees":180000},embed=False,auto_log_gpu=False,auto_log_cpu=False)
a=trackio.Artifact("isolation-forest-cpu-reproduction",type="dataset",description="Exact expected depths, 180k randomized trees, anomaly thresholds, boundary controls, tests, and provenance.")
a.add_dir(ROOT/"reproduction",name="reproduction");a.add_dir(ROOT/"outputs",name="outputs")
for n in ("paper.pdf","claims.md","SOURCE_AUDIT.md","ENVIRONMENT.md","README.md"):a.add_file(ROOT/n,name=n)
l=trackio.log_artifact(a,aliases=["challenge","cpu","complete"]);trackio.finish();print(json.dumps({"artifact":l.qualified_name,"files":len(l.manifest or []),"size":l.size},sort_keys=True))

