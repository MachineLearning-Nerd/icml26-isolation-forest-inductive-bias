# Branch audit and migration map

## Repository rename

The repository started as
icml26-repro-J0y3sNbo9G-isolation-forest and is normalized to
icml26-isolation-forest-inductive-bias. The old repository name is historical
metadata only; the final public URL is documented in README.md and
SOURCE_MANIFEST.md.

## Why main is based on the cumulative branch

The old main tip 890c5019f046dcbf2adff3dda0aaea071678bed8 mirrored the older
three-claim publication surface. The cumulative evidence tip
0489d74e968f34723efd96f69ef8bca893271f55 contains the later Claim 2, Claim 4,
Claim 5, and Claim 6 artifacts and is therefore the source base for the final
main documentation surface.

## Legacy-to-final branch map

| Final branch | Legacy branch | Source tip before migration | Role |
|---|---|---|---|
| main | cumulative release source | 0489d74e968f34723efd96f69ef8bca893271f55 | Canonical six-claim collection plus repository documentation. |
| release/cumulative-evidence | orx/final-cumulative-regression-and-release-candidat | 0489d74e968f34723efd96f69ef8bca893271f55 | Release-oriented cumulative evidence view. |
| baseline/judged-4-of-12 | orx/frozen-baseline-judged-4-12-reproduction | 1898d469a34353e52958064261b317cbe724b6f2 | Historical frozen evaluator baseline; recorded score 4/12. |
| audit/claim-2-falsification | orx/claim-2-promoted-exact-plus-randomized-confirmat | 38305bacf3d11fd1046680bf7684bf156072a4bd | Promoted exact and randomized Claim 2 evidence. |
| audit/claim-2-exact-route | orx/claim-2-route-a-exact-adversarial-thresholds | ae73beaebc1bfa106d83aca89d5ca705b174d240 | Exact marginal threshold route. |
| experiment/claim-2-randomized-route | orx/claim-2-route-b-randomized-tree-thresholds | fb97205e0823fb1f71ae322553b4401941d9c5f7 | Randomized-tree Claim 2 route. |
| audit/claim-4-falsification | orx/claim-4-promoted-falsification-plus-scaling-audi | 3f4fb43782c0d3c150b02c0830473ba2468c5fca | Promoted Claim 4 route comparison. |
| experiment/claim-4-asymptotic-route | orx/claim-4-route-a-asymptotic-clustered-thresholds | fcbee8906dc0d7e2c133992ed53333b91bd9496a | Primary asymptotic route, explicitly blocked. |
| audit/claim-4-counterexample | orx/claim-4-route-b-finite-varied-clusters | 56d5f8ebdea099b11367354c9999974099707e30 | Decisive exact counterexample family. |
| experiment/claim-5-concentration | orx/claim-5-geometric-tree-concentration | 191c6df20132a5febcdf72b1dc5315bbf70d897f | Proposition 3.1 concentration sweep. |
| audit/claim-6-openml-protocol | orx/claim-6-openml-protocol-identifiability-audit | d91137d9aa7e652f64002ddc9acaa596f4baca97 | OpenML protocol and historical-input audit. |

The legacy branch names are retained here to make the migration reversible and
the source history inspectable. They are not intended to remain as public
branches after normalization.

## Final branch invariants

- The final public inventory contains exactly the 11 descriptive branches in
  the table above.
- main and release/cumulative-evidence expose the cumulative six-claim package.
- baseline/judged-4-of-12 remains a historical comparison point and is not
  presented as the current verdict.
- Claim 4 route A remains visible as a blocked experiment; it is not erased
  merely because route B supplies a terminal counterexample.
- No legacy OpenResearch-style branch name is used as a current branch.
- All reachable commits are rewritten to the canonical MachineLearning-Nerd
  author and committer identity with no co-author trailers.
