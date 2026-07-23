import json
from pathlib import Path
import pandas as pd
from verify_claim_2_randomized import verify as verify_claim_2_randomized
OUT=Path(__file__).parents[1]/"outputs"
def s():return json.loads((OUT/"summary.json").read_text())
def test_claims_1_and_3_remain_verified():assert all(s()[f"claim_{i}"]=="verified" for i in (1,3))
def test_claim_2_has_rigorous_terminal_verdict():assert s()["claim_2"] in ("verified","falsified")
def test_claim_2_randomized_evidence():verify_claim_2_randomized(OUT/"claim2_randomized_summary.json")
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
