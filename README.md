# CMI Trainer

Physician training tool: see how specifying a diagnosis (adding a CC/MCC-bearing
condition) changes the assigned MS-DRG and its relative weight.

## Run locally
```
pip install -r requirements.txt
streamlit run app.py
```

## Deploy (free, hosted) — Streamlit Community Cloud
1. Push this folder to a GitHub repo (e.g. `cmi-trainer`).
2. Go to https://share.streamlit.io → "New app" → point it at the repo, branch `main`,
   file `app.py`.
3. Deploy. You'll get a shareable URL like `cmi-trainer.streamlit.app`.

## Scope (v1)
- 11 diagnosis families, medical (non-surgical) DRGs only.
- Sepsis family (DRG 870/871/872) uses a weight pulled from a live FY2026 CMS-sourced
  figure. All other families use well-established approximate weights — **verify against
  the current CMS Table 5 (MS-DRG Relative Weighting Factors) before treating any number
  here as authoritative.**
- No dollar/payment figures — CMI/weight numbers only, by design.

## Next steps (not yet built)
- Verify every non-sepsis family's exact FY2026 weight against CMS Table 5 directly.
- Add more diagnosis families beyond the initial 11.
- Consider surgical DRG partitions (out of scope for v1).
