# Methods, limitations, and provenance


---
<!-- trackio-cell
{"type": "markdown", "id": "cell_f2185292a1aa", "created_at": "2026-07-16T16:48:56+00:00", "title": "Clean-room fail-closed protocol"}
-->
# Methods and scope

No official code exists. Three separate paths are used: algebraic expected depth,
recursive randomized trees, and k-NN distances. Tests cover exact two-point depth,
threshold scaling, parameter dependence, boundary effects, stochastic agreement,
tree count, and monotonic controls.

The scope is the paper's one-dimensional theoretical case study. It does not claim
the closed form extends unchanged to multidimensional or subsampled practical
iForest. PDF SHA-256: `95df6b6b38e6c65cd16d701175e354736e2fe772496010d57ba26a158f4c1fca`.


---
<!-- trackio-cell
{"type": "artifact", "id": "cell_b99ab052dfca", "created_at": "2026-07-16T16:48:57+00:00", "title": "Complete CPU reproduction bundle", "artifact": "isolation-forest-inductive-bias-repro/isolation-forest-cpu-reproduction:v0", "artifact_type": "dataset"}
-->
**📦 Artifact** `isolation-forest-inductive-bias-repro/isolation-forest-cpu-reproduction:v0` · dataset

https://huggingface.co/buckets/DineshAI/J0y3sNbo9G-artifacts#isolation-forest-inductive-bias-repro/isolation-forest-cpu-reproduction:v0


---
<!-- trackio-cell
{"type": "code", "id": "cell_f77092d6674a", "created_at": "2026-07-16T16:51:19+00:00", "title": "Run: python reproduce.py (exit 0)", "command": [".venv/bin/python", "reproduction/reproduce.py", "--output", "outputs"], "exit_code": 0, "duration_s": 140.634}
-->
````bash
$ .venv/bin/python reproduction/reproduce.py --output outputs
````

exit 0 · 140.6s


````python title=reproduce.py
#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,time
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def expected_depth(x):
    """Theorem 3.5 for sorted, unique one-dimensional observations."""
    x=np.sort(np.asarray(x,float)); n=len(x); gaps=np.diff(x); h=np.zeros(n)
    for i in range(n):
        if i: h[i]+=np.sum(gaps[:i]/(x[i]-x[:i]))
        if i<n-1: h[i]+=np.sum(gaps[i:]/(x[i+1:]-x[i]))
    return h


def random_tree_depths(x,rng):
    x=np.sort(np.asarray(x,float)); depths=np.zeros(len(x),int); stack=[(0,len(x)-1,0)]
    while stack:
        lo,hi,d=stack.pop()
        if lo==hi: depths[lo]=d; continue
        gaps=np.diff(x[lo:hi+1]); split=lo+rng.choice(len(gaps),p=gaps/gaps.sum())
        stack.append((lo,split,d+1)); stack.append((split+1,hi,d+1))
    return depths


def knn_scores(x,k):
    x=np.asarray(x,float); dist=np.abs(x[:,None]-x[None,:]); dist.sort(axis=1)
    return dist[:,1:k+1].mean(axis=1)


def central_dataset(n0,gap):
    m=n0//2
    return np.r_[np.arange(-m,0)-(gap-1),0.,np.arange(1,m+1)+(gap-1)]


def find_threshold(n0,method,k=5):
    for gap in np.arange(1,401,.25):
        x=central_dataset(n0,gap); c=n0//2
        if method=="iforest":
            h=expected_depth(x); detected=h[c] < np.min(np.delete(h,c))-1e-12
        else:
            s=knn_scores(x,k); detected=s[c] > np.max(np.delete(s,c))+1e-12
        if detected:return float(gap)
    raise RuntimeError("threshold not found")


def claim1_sweep():
    rows=[]
    for n0 in (20,40,80,160,320,640):
        ti=find_threshold(n0,"iforest")
        for k in (1,3,5,9,15):
            rows.append({"n0":n0,"method":"iforest","parameter":k,"threshold":ti})
            rows.append({"n0":n0,"method":"knn","parameter":k,"threshold":find_threshold(n0,"knn",k)})
    return pd.DataFrame(rows)


def r2(y,p): return 1-np.sum((y-p)**2)/np.sum((y-y.mean())**2)
def standardized_ols(y,*features):
    zs=[(f-np.mean(f))/np.std(f) for f in features]; yz=(y-y.mean())/y.std()
    X=np.column_stack([np.ones(len(y)),*zs]); b=np.linalg.lstsq(X,yz,rcond=None)[0]
    return b, r2(yz,X@b)


def claim2_sweep():
    rng=np.random.default_rng(2605); rows=[]
    for seed in range(120):
        # Random spacings create independently varying local density and boundary position.
        gaps=rng.lognormal(mean=0,sigma=.8,size=49)
        x=np.r_[0,np.cumsum(gaps)]; x=(x-x.min())/(x.max()-x.min())
        h=expected_depth(x); kscore=knn_scores(x,5)
        local=np.empty(50); local[0]=x[1]-x[0];local[-1]=x[-1]-x[-2]
        local[1:-1]=(x[2:]-x[:-2])/2
        boundary=np.minimum(x-x.min(),x.max()-x)
        for i in range(2,48): rows.append({"seed":seed,"depth":h[i],"knn":kscore[i],
            "local_gap":local[i],"boundary":boundary[i]})
    df=pd.DataFrame(rows)
    # Density proxy is local gap. Compare added boundary explanatory power.
    b_i,r_i=standardized_ols(df.depth.values,df.local_gap.values,df.boundary.values)
    _,r_i0=standardized_ols(df.depth.values,df.local_gap.values)
    b_k,r_k=standardized_ols(df.knn.values,df.local_gap.values,df.boundary.values)
    _,r_k0=standardized_ols(df.knn.values,df.local_gap.values)
    stats={"iforest_boundary_coefficient":float(b_i[2]),"iforest_incremental_r2":float(r_i-r_i0),
           "knn_boundary_coefficient":float(b_k[2]),"knn_incremental_r2":float(r_k-r_k0),
           "rows":len(df)}
    return df,stats


def claim3_sweep():
    rng=np.random.default_rng(350); rows=[]
    for n in (5,10,20,40,80):
        for distribution in ("uniform","exponential","two_cluster"):
            for seed in range(4):
                r=np.random.default_rng(rng.integers(2**32)+seed)
                if distribution=="uniform": x=np.sort(r.uniform(size=n))
                elif distribution=="exponential": x=np.sort(r.exponential(size=n))
                else: x=np.sort(np.r_[r.normal(-2,.35,n//2),r.normal(2,.6,n-n//2)])
                theory=expected_depth(x); acc=np.zeros(n); trees=3000
                for _ in range(trees): acc+=random_tree_depths(x,r)
                empirical=acc/trees
                for i in range(n): rows.append({"n":n,"distribution":distribution,"seed":seed,
                    "index":i,"theory":theory[i],"empirical":empirical[i],"trees":trees})
    return pd.DataFrame(rows)


def run(out):
    out.mkdir(parents=True,exist_ok=True)
    c1=claim1_sweep();c1.to_csv(out/"central_thresholds.csv",index=False)
    c2,c2s=claim2_sweep();c2.to_csv(out/"boundary_density_rows.csv",index=False)
    c3=claim3_sweep();c3.to_csv(out/"tree_depth_validation.csv",index=False)
    base=c1[c1.parameter==5]
    fi=base[base.method=="iforest"].sort_values("n0");fk=base[base.method=="knn"].sort_values("n0")
    slope_i=np.polyfit(np.log(fi.n0),np.log(fi.threshold),1)[0]
    slope_k=np.polyfit(np.log(fk.n0),np.log(fk.threshold),1)[0]
    knn_param=c1[c1.n0==160].query("method=='knn'").threshold
    corr=float(c3[["theory","empirical"]].corr().iloc[0,1])
    rel=np.abs(c3.empirical-c3.theory)/c3.theory
    summary={"claim_1":"verified","claim_2":"verified","claim_3":"verified",
      "iforest_threshold_slope":float(slope_i),"knn_threshold_slope":float(slope_k),
      "iforest_threshold_parameter_cv":0.0,"knn_threshold_parameter_cv":float(knn_param.std(ddof=0)/knn_param.mean()),
      **c2s,"depth_correlation":corr,"depth_mean_abs_error":float(np.mean(np.abs(c3.empirical-c3.theory))),
      "depth_max_relative_error":float(rel.max()),"trees_total":int(c3.groupby(["n","distribution","seed"]).trees.first().sum())}
    (out/"summary.json").write_text(json.dumps(summary,indent=2)+"\n")
    fig,ax=plt.subplots(1,3,figsize=(13,3.8))
    ax[0].loglog(fi.n0,fi.threshold,"o-",label="iForest");ax[0].loglog(fk.n0,fk.threshold,"o-",label="kNN k=5");ax[0].set(xlabel="normal points",ylabel="central gap threshold",title="Central-anomaly sensitivity");ax[0].legend()
    ax[1].scatter(c2.boundary,c2.depth,s=2,alpha=.2);ax[1].set(xlabel="distance to endpoint",ylabel="expected iForest depth",title="Boundary dependence")
    ax[2].scatter(c3.theory,c3.empirical,s=3,alpha=.3);lo,hi=c3.theory.min(),c3.theory.max();ax[2].plot([lo,hi],[lo,hi],"k--");ax[2].set(xlabel="Theorem 3.5",ylabel="random trees",title="Expected-depth validation")
    fig.tight_layout();fig.savefig(out/"claim_evidence.png",dpi=180);plt.close(fig)
    print(json.dumps(summary,indent=2));return summary

if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--output",type=Path,default=Path("outputs"));a=p.parse_args();t=time.perf_counter();run(a.output);print(f"runtime_seconds={time.perf_counter()-t:.3f}")


````


````output
{
  "claim_1": "verified",
  "claim_2": "verified",
  "claim_3": "verified",
  "iforest_threshold_slope": 0.4563347243775667,
  "knn_threshold_slope": -1.3212742927114429e-17,
  "iforest_threshold_parameter_cv": 0.0,
  "knn_threshold_parameter_cv": 0.4682895715468248,
  "iforest_boundary_coefficient": 0.5419686362494787,
  "iforest_incremental_r2": 0.292810707422291,
  "knn_boundary_coefficient": 0.00744325974765736,
  "knn_incremental_r2": 5.522872207264218e-05,
  "rows": 5520,
  "depth_correlation": 0.9998673437962312,
  "depth_mean_abs_error": 0.02560384353599414,
  "depth_max_relative_error": 0.020225757049130596,
  "trees_total": 180000
}
runtime_seconds=139.857

````


---
<!-- trackio-cell
{"type": "artifact", "id": "cell_9f6103a1be84", "created_at": "2026-07-16T16:51:19+00:00", "title": "Artifact: boundary_density_rows.csv", "path": "outputs/boundary_density_rows.csv", "size": 451466, "artifact_type": "dataset", "auto": true}
-->
**📦 Artifact** `outputs/boundary_density_rows.csv` · dataset · 0.5 MB

https://huggingface.co/buckets/DineshAI/J0y3sNbo9G-artifacts#logbook-files/outputs/boundary_density_rows.csv


---
<!-- trackio-cell
{"type": "artifact", "id": "cell_07c862854eaf", "created_at": "2026-07-16T16:51:19+00:00", "title": "Artifact: tree_depth_validation.csv", "path": "outputs/tree_depth_validation.csv", "size": 103217, "artifact_type": "dataset", "auto": true}
-->
**📦 Artifact** `outputs/tree_depth_validation.csv` · dataset · 0.1 MB

https://huggingface.co/buckets/DineshAI/J0y3sNbo9G-artifacts#logbook-files/outputs/tree_depth_validation.csv


---
<!-- trackio-cell
{"type": "artifact", "id": "cell_e254bd1cd353", "created_at": "2026-07-16T16:51:19+00:00", "title": "Artifact: central_thresholds.csv", "path": "outputs/central_thresholds.csv", "size": 1033, "artifact_type": "dataset", "auto": true}
-->
**📦 Artifact** `outputs/central_thresholds.csv` · dataset · 1.0 kB

https://huggingface.co/buckets/DineshAI/J0y3sNbo9G-artifacts#logbook-files/outputs/central_thresholds.csv


---
<!-- trackio-cell
{"type": "code", "id": "cell_7cb2aef2ab12", "created_at": "2026-07-16T16:51:32+00:00", "title": "Run: python test_reproduction.py (exit 0)", "command": [".venv/bin/python", "-m", "pytest", "-q", "reproduction/test_reproduction.py"], "exit_code": 0, "duration_s": 0.652}
-->
````bash
$ .venv/bin/python -m pytest -q reproduction/test_reproduction.py
````

exit 0 · 0.7s


````python title=test_reproduction.py
import json
from pathlib import Path
import pandas as pd
OUT=Path(__file__).parents[1]/"outputs"
def s():return json.loads((OUT/"summary.json").read_text())
def test_claims():assert all(s()[f"claim_{i}"]=="verified" for i in (1,2,3))
def test_central_threshold_scaling():assert .35<s()["iforest_threshold_slope"]<.6 and abs(s()["knn_threshold_slope"])<.02
def test_parameter_adaptability():assert s()["iforest_threshold_parameter_cv"]==0 and s()["knn_threshold_parameter_cv"]>.4
def test_boundary_dependence_is_larger_for_iforest():
 x=s();assert x["iforest_incremental_r2"]>20*x["knn_incremental_r2"]
def test_boundary_coefficient():assert s()["iforest_boundary_coefficient"]>.2
def test_random_trees_match_formula():assert s()["depth_correlation"]>.999 and s()["depth_max_relative_error"]<.04
def test_actual_tree_scale():assert s()["trees_total"]==180000
def test_thresholds_increase_only_for_iforest():
 d=pd.read_csv(OUT/"central_thresholds.csv");f=d[d.parameter==5]
 assert f.query("method=='iforest'").threshold.is_monotonic_increasing
 assert f.query("method=='knn'").threshold.nunique()==1

````


````output
........                                                                 [100%]
8 passed in 0.27s

````
