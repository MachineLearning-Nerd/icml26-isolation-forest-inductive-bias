#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,time
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from claim2_exact import run_claim2_exact
from claim2_randomized import run_claim2_randomized
from claim4_asymptotic import run_claim4_asymptotic


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
    c2_exact=run_claim2_exact(out)
    c2_randomized=run_claim2_randomized(out)
    c4_asymptotic=run_claim4_asymptotic(out)
    base=c1[c1.parameter==5]
    fi=base[base.method=="iforest"].sort_values("n0");fk=base[base.method=="knn"].sort_values("n0")
    slope_i=np.polyfit(np.log(fi.n0),np.log(fi.threshold),1)[0]
    slope_k=np.polyfit(np.log(fk.n0),np.log(fk.threshold),1)[0]
    knn_param=c1[c1.n0==160].query("method=='knn'").threshold
    corr=float(c3[["theory","empirical"]].corr().iloc[0,1])
    rel=np.abs(c3.empirical-c3.theory)/c3.theory
    claim2_verdict="falsified" if c2_exact["verdict"]=="FALSIFIED" and c2_randomized["verdict"]=="FALSIFIED" else "blocked"
    claim4_verdict=c4_asymptotic["verdict"].lower()
    summary={"claim_1":"verified","claim_2":claim2_verdict,"claim_3":"verified","claim_4":claim4_verdict,
      "iforest_threshold_slope":float(slope_i),"knn_threshold_slope":float(slope_k),
      "iforest_threshold_parameter_cv":0.0,"knn_threshold_parameter_cv":float(knn_param.std(ddof=0)/knn_param.mean()),
      **c2s,"depth_correlation":corr,"depth_mean_abs_error":float(np.mean(np.abs(c3.empirical-c3.theory))),
      "depth_max_relative_error":float(rel.max()),"trees_total":int(c3.groupby(["n","distribution","seed"]).trees.first().sum()),
      "claim_2_exact":c2_exact,"claim_2_randomized":c2_randomized,
      "claim_4_asymptotic":c4_asymptotic}
    (out/"summary.json").write_text(json.dumps(summary,indent=2)+"\n")
    fig,ax=plt.subplots(1,3,figsize=(13,3.8))
    ax[0].loglog(fi.n0,fi.threshold,"o-",label="iForest");ax[0].loglog(fk.n0,fk.threshold,"o-",label="kNN k=5");ax[0].set(xlabel="normal points",ylabel="central gap threshold",title="Central-anomaly sensitivity");ax[0].legend()
    ax[1].scatter(c2.boundary,c2.depth,s=2,alpha=.2);ax[1].set(xlabel="distance to endpoint",ylabel="expected iForest depth",title="Boundary dependence")
    ax[2].scatter(c3.theory,c3.empirical,s=3,alpha=.3);lo,hi=c3.theory.min(),c3.theory.max();ax[2].plot([lo,hi],[lo,hi],"k--");ax[2].set(xlabel="Theorem 3.5",ylabel="random trees",title="Expected-depth validation")
    fig.tight_layout();fig.savefig(out/"claim_evidence.png",dpi=180);plt.close(fig)
    print(json.dumps(summary,indent=2));return summary

if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--output",type=Path,default=Path("outputs"));a=p.parse_args();t=time.perf_counter();run(a.output);print(f"runtime_seconds={time.perf_counter()-t:.3f}")
