import json
from pathlib import Path
import pandas as pd
from verify_claim_2 import verify as verify_claim_2
from verify_claim_2_randomized import verify as verify_claim_2_randomized
from verify_claim_4_varied import verify as verify_claim_4_varied
from verify_claim_5 import verify as verify_claim_5
OUT=Path(__file__).parents[1]/"outputs"
def s():return json.loads((OUT/"summary.json").read_text())
def test_claims_1_and_3_remain_verified():assert all(s()[f"claim_{i}"]=="verified" for i in (1,3))
def test_claim_2_has_rigorous_terminal_verdict():assert s()["claim_2"] in ("verified","falsified")
def test_claim_2_evidence_package():verify_claim_2(OUT/"claim2_exact_summary.json")
def test_claim_2_randomized_evidence():verify_claim_2_randomized(OUT/"claim2_randomized_summary.json")
def test_claim_4_varied_evidence():verify_claim_4_varied(OUT/"claim4_varied_summary.json")
def test_claim_4_scaling_route_remains_honestly_blocked():assert s()["claim_4_asymptotic"]["verdict"]=="BLOCKED"
def test_claim_5_concentration_evidence():verify_claim_5(OUT/"claim5_summary.json")
def test_claim_6_is_honestly_blocked():
 x=s()["claim_6_openml_audit"]
 assert x["verdict"]=="BLOCKED"
 assert not x["exact_historical_manifest_present"]
 assert not x["kappa_recomputed_for_historical_dimensions"]
 assert x["threshold_mutation_control"]["count_changed"]
def test_claim_6_positive_verifier_rejects_blocked_evidence():
 x=json.loads((Path(__file__).parents[1]/".openresearch/artifacts/claim_6/verifier_expected_failure.json").read_text())
 assert x["failed_as_intended"] and x["actual_exit_code"]!=0
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
