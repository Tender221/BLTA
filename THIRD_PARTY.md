# Third-party sources and attribution

This repository contains the BLTA implementation and portable research artifacts.
Project licensing does not replace upstream licensing or extend to base-model
weights. No base-model checkpoint is distributed here.

The original BLTA implementation is distributed under MIT. The two simulator/
payload sources below retain their MIT notices. The pinned PIGuard model card
declares MIT; Wolf and ProtectAI v2 declare Apache-2.0. Their original cards are
retained in `third_party/model_cards/` with the exact pinned revisions below.

| Material | Pinned upstream source | License / notice |
|---|---|---|
| Business simulator records | [sierra-research/tau2-bench](https://github.com/sierra-research/tau2-bench/tree/dd8757d4c8791dad7b3cdaf02a105a3d5f9d86bd), release describing itself as tau3-bench | MIT text retained in `third_party/tau3-LICENSE.txt` |
| Prompt-injection payloads | [uiuc-kang-lab/InjecAgent](https://github.com/uiuc-kang-lab/InjecAgent/tree/f19c9f2c79a41046eb13c03c51a24c567a8ffa07) | MIT text retained in `third_party/InjecAgent-LICENCE.txt` |
| Frozen guard features | Pinned PIGuard, Wolf and ProtectAI v2 encoders | Identifiers and revisions in `third_party/model_revisions.json`; feature-cache provenance in `input_manifest.json` |
| Recorded victim executions | Pinned Qwen2.5-3B-Instruct and Qwen2.5-1.5B-Instruct | Identifiers in `third_party/model_revisions.json`; cached outcomes, not model weights |

`third_party/guard_model_provenance.json` retains the original saved model-file
hashes; `model_revisions.json` supplies the complete three-guard/two-victim map.
`corpus_provenance.json` records generated corpus counts and the upstream commits.

The release's figures and summaries describe this study. The overview is an
AI-assisted conceptual illustration, and its score densities are schematic.
