import streamlit as st
from drg_data import (
    DIAGNOSIS_FAMILIES, VERIFICATION_NOTE, SECONDARY_DX,
    PRINCIPAL_LEVEL_CONDITIONS, group_case, MYTH_CHECKS, get_myth_check_rows,
)

st.set_page_config(page_title="CMI Trainer", page_icon="🩺", layout="wide")

# ---------- Styling: deep teal clinical theme ----------
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&display=swap" rel="stylesheet">
<style>
    html, body, .stApp, [class*="css"] { font-family: 'IBM Plex Sans', -apple-system, sans-serif; }
    .stApp { background-color: #0a1a1c; color: #eef7f7; }
    .block-container { max-width: 920px; padding-top: 2.5rem; }
    section[data-testid="stSidebar"] { background-color: #0e2124; }
    h1, h2, h3, h4 { color: #f2fafa !important; font-weight: 600 !important; letter-spacing: -0.01em; }
    p, span, label, .stMarkdown { color: #bdd4d4; }
    hr { border-color: #1d3b3e; }

    .cmi-card {
        background: #0f2226;
        border: 1px solid #1d3b3e;
        border-left: 3px solid #2e8a8a;
        border-radius: 6px;
        padding: 18px 22px;
        margin-bottom: 14px;
        color: #eef7f7;
    }
    .cmi-up { color: #4fbf8f; font-weight: 600; }
    .cmi-down { color: #d97f6f; font-weight: 600; }
    .cmi-flat { color: #8fa8a8; font-weight: 600; }
    .cmi-badge {
        display: inline-block; background: #123033; color: #5fc9c9;
        border-radius: 4px; padding: 3px 10px; font-size: 0.78rem; margin-right: 6px;
        border: 1px solid #1d4548; font-weight: 500; letter-spacing: 0.02em;
    }
    .verify-flag {
        background: #241f10; border-left: 3px solid #a8862f; color: #d9b872;
        border-radius: 6px; padding: 10px 14px; font-size: 0.87rem; margin-top: 8px;
        line-height: 1.55;
    }
    .confirmed-flag {
        background: #0d251e; border-left: 3px solid #3f9270; color: #7cd6ab;
        border-radius: 6px; padding: 10px 14px; font-size: 0.87rem; margin-top: 8px;
        line-height: 1.55;
    }
    .criteria-box {
        background: #0d1e21; border: 1px solid #1d3b3e; border-radius: 6px;
        padding: 12px 16px; margin-top: 6px; font-size: 0.88rem; color: #bdd4d4;
        line-height: 1.55;
    }

    /* ---- Native Streamlit widget theming ---- */
    .stCaption, [data-testid="stCaptionContainer"] { color: #6f9090 !important; }

    /* Expander */
    div[data-testid="stExpander"] {
        background: #0f2226; border: 1px solid #1d3b3e; border-radius: 6px;
    }
    div[data-testid="stExpander"] summary { color: #eef7f7 !important; font-weight: 500; }
    div[data-testid="stExpander"] summary:hover { color: #5fc9c9 !important; }

    /* Selectbox / dropdowns */
    div[data-baseweb="select"] > div {
        background-color: #0f2226 !important; border-color: #1d3b3e !important; color: #eef7f7 !important;
    }
    ul[role="listbox"] { background-color: #0f2226 !important; }
    li[role="option"] { color: #eef7f7 !important; }
    li[role="option"]:hover { background-color: #123033 !important; }

    /* Multiselect selected-item tags */
    span[data-baseweb="tag"] {
        background-color: #123033 !important; border: 1px solid #2e8a8a !important;
    }
    span[data-baseweb="tag"] span { color: #5fc9c9 !important; }
    span[data-baseweb="tag"] svg { fill: #5fc9c9 !important; }

    /* Radio buttons */
    div[role="radiogroup"] label { color: #bdd4d4 !important; }
    div[role="radiogroup"] label div:first-child {
        border-color: #2e8a8a !important;
    }
    div[role="radiogroup"] input:checked + div {
        background-color: #2e8a8a !important; border-color: #2e8a8a !important;
    }

    /* Buttons */
    .stButton button, .stDownloadButton button {
        background-color: #123033; color: #5fc9c9; border: 1px solid #2e8a8a;
    }
    .stButton button:hover, .stDownloadButton button:hover {
        background-color: #1d4548; color: #eef7f7; border-color: #4fbf8f;
    }
</style>
""", unsafe_allow_html=True)

st.title("🩺 CMI Trainer")
st.caption("Train your documentation eye: see how specifying a diagnosis moves the DRG weight — one case at a time.")

with st.expander("⚠️ How to read this tool (read once)"):
    st.markdown("""
- **This shows DRG *relative weight* per case, not hospital CMI.** CMI is the *average*
  relative weight across all of a hospital's discharges — a single case's weight is one
  input into that average, not the CMI itself.
- **Medical (non-procedural) admissions only**, v1. Surgical DRG partitions aren't modeled.
- **CC/MCC status depends on the whole code set**, not just one diagnosis in isolation —
  some conditions are excluded from counting as a CC when they're an integral part of the
  principal diagnosis (CMS's "CC exclusion list"). This tool illustrates common, clean
  examples — real cases can be more nuanced.
- **Weights update every federal fiscal year.** This build targets FY2026 (MS-DRG v43.1).
""")
    st.markdown(f'<div class="verify-flag">{VERIFICATION_NOTE}</div>', unsafe_allow_html=True)


def render_myth_check(family_key):
    if family_key not in MYTH_CHECKS:
        return
    base, organism_only, complication, mc = get_myth_check_rows(family_key)
    with st.expander("🔍 Myth Check — a common false lead in this family"):
        st.markdown(f"**Common belief:** {mc['myth']}")
        st.markdown(f"**Reality:** {mc['reality']}")
        st.write("")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**{mc['organism_only_note']}**")
            st.markdown(f"""
            <div class="cmi-card">
            DRG {organism_only['drg']} — {organism_only['title']}<br>
            Weight: <b>{organism_only['weight']:.4f}</b>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"**{mc['complication_note']}**")
            delta = complication['weight'] - organism_only['weight']
            pct = (delta / organism_only['weight']) * 100 if organism_only['weight'] else 0
            st.markdown(f"""
            <div class="cmi-card">
            DRG {complication['drg']} — {complication['title']}<br>
            Weight: <b>{complication['weight']:.4f}</b><br>
            <span class="cmi-up">▲ {delta:+.4f} ({pct:+.1f}%)</span>
            </div>
            """, unsafe_allow_html=True)
        st.caption("Same principal diagnosis both columns — the only difference is whether the complication itself was documented.")


def render_source_link(fam):
    url = fam.get("source_url")
    note = fam.get("source_note")
    if not note:
        return
    with st.expander("📎 Data source for this family"):
        st.markdown(note)
        if url:
            st.markdown(f"[Open the CMS source page]({url})")


st.divider()

mode = st.radio(
    "Mode",
    ["Simple: one added diagnosis", "Multi-diagnosis builder"],
    horizontal=True,
)
st.divider()

if mode == "Multi-diagnosis builder":
    family_keys = list(DIAGNOSIS_FAMILIES.keys())
    family_labels = [DIAGNOSIS_FAMILIES[k]["label"] for k in family_keys]

    st.markdown("#### Step 1 — Principal diagnosis")
    selected_label = st.selectbox("Choose the principal diagnosis family", family_labels, key="mb_family")
    selected_key = family_keys[family_labels.index(selected_label)]
    fam = DIAGNOSIS_FAMILIES[selected_key]
    st.markdown(f'<span class="cmi-badge">{fam["mdc"]}</span>', unsafe_allow_html=True)

    drgs_sorted = sorted(fam["drgs"], key=lambda d: d["weight"])
    base = drgs_sorted[0]

    with st.expander("⚠️ Sepsis / septic shock note"):
        for cond in PRINCIPAL_LEVEL_CONDITIONS.values():
            st.markdown(f"**{cond['label']}**")
            st.markdown(cond["note"])
            st.write("")

    render_myth_check(selected_key)
    render_source_link(fam)

    st.markdown("#### Step 2 — Add secondary diagnoses")
    st.caption("Pick every secondary condition that's actually documented for this case. The grouper applies CMS's real rule: the single HIGHEST-severity qualifying diagnosis sets the tier — additional CCs/MCCs beyond that one don't stack or add further weight.")

    dx_keys = list(SECONDARY_DX.keys())
    dx_labels = [f"{SECONDARY_DX[k]['label']} — {SECONDARY_DX[k]['tier']}" for k in dx_keys]
    chosen_labels = st.multiselect("Secondary diagnoses documented", dx_labels)
    chosen_keys = [dx_keys[dx_labels.index(l)] for l in chosen_labels]

    if chosen_keys:
        with st.expander("📋 Diagnostic criteria for what you selected"):
            for dx_key in chosen_keys:
                dx = SECONDARY_DX[dx_key]
                st.markdown(f"**{dx['label']}**")
                st.markdown(f'<div class="criteria-box">{dx["diagnostic_criteria"]}</div>', unsafe_allow_html=True)
                st.write("")

    with st.expander("📋 Browse all diagnostic criteria (reference)"):
        st.caption("General clinical reference criteria — not exhaustive, not a substitute for your institution's clinical judgment or documented criteria requirements.")
        for dx_key in dx_keys:
            dx = SECONDARY_DX[dx_key]
            st.markdown(f"**{dx['label']}** — *{dx['tier']}*")
            st.markdown(f'<div class="criteria-box">{dx["diagnostic_criteria"]}</div>', unsafe_allow_html=True)
            st.write("")

    st.markdown("#### Result")
    st.markdown(f"""
    <div class="cmi-card">
    <b>Base (principal dx alone):</b> DRG {base['drg']} — {base['title']}<br>
    Relative weight: {base['weight']:.4f}
    </div>
    """, unsafe_allow_html=True)

    if chosen_keys:
        winning_drg, contributions = group_case(selected_key, chosen_keys)
        delta = winning_drg["weight"] - base["weight"]
        pct = (delta / base["weight"]) * 100 if base["weight"] else 0
        arrow_class = "cmi-up" if delta > 0 else ("cmi-down" if delta < 0 else "cmi-flat")
        arrow = "▲" if delta > 0 else ("▼" if delta < 0 else "—")

        st.markdown(f"""
        <div class="cmi-card">
        <b>Resulting DRG:</b> {winning_drg['drg']} — {winning_drg['title']}<br>
        Relative weight: <span style="font-size:1.4rem; font-weight:700;">{winning_drg['weight']:.4f}</span>
        &nbsp;&nbsp;·&nbsp;&nbsp; GMLOS: {winning_drg['gmlos']} days
        <br><br>
        <span class="{arrow_class}" style="font-size:1.3rem;">{arrow} {delta:+.4f} ({pct:+.1f}%)</span>
        &nbsp;vs. the principal diagnosis alone
        </div>
        """, unsafe_allow_html=True)

        st.markdown("**Why:**")
        for dx_key, contributed_tier in contributions:
            dx = SECONDARY_DX[dx_key]
            if contributed_tier:
                st.markdown(f"- ✅ **{dx['label']}** contributed **{contributed_tier}** tier — {dx['note']}")
            elif selected_key in dx["excludes_families"]:
                st.markdown(f"- 🚫 **{dx['label']}** — excluded here: {dx['note']}")
            elif dx["tier"] == "None":
                st.markdown(f"- ⚪ **{dx['label']}** — documented, but not a CC/MCC by itself: {dx['note']}")
            else:
                st.markdown(f"- ➖ **{dx['label']}** ({dx['tier']}) — didn't change the outcome; a higher-tier condition was already present.")

        verify_html = (
            f'<div class="confirmed-flag">✓ Base weight pulled from a live FY2026 CMS-sourced figure.</div>'
            if fam["verification"] == "cms_confirmed" else
            f'<div class="verify-flag">⚠ Base weight is typical/approximate — verify against current CMS Table 5 before real use. Secondary-diagnosis CC/MCC status is grounded in current coding/CDI references but not independently verified against the live CMS CC/MCC list in this build.</div>'
        )
        st.markdown(verify_html, unsafe_allow_html=True)
    else:
        st.caption("Add at least one secondary diagnosis above to see the resulting DRG.")

    st.divider()
    st.caption("CMI Trainer v1 · Built for physician education · Not for coding, billing, or compliance sign-off.")
    st.stop()

family_keys = list(DIAGNOSIS_FAMILIES.keys())
family_labels = [DIAGNOSIS_FAMILIES[k]["label"] for k in family_keys]

selected_label = st.selectbox("Choose a diagnosis family", family_labels)
selected_key = family_keys[family_labels.index(selected_label)]
fam = DIAGNOSIS_FAMILIES[selected_key]

st.markdown(f'<span class="cmi-badge">{fam["mdc"]}</span>', unsafe_allow_html=True)
st.write("")

render_myth_check(selected_key)
render_source_link(fam)

# sort drgs from lowest to highest severity tier (None -> CC -> MCC / special)
drgs_sorted = sorted(fam["drgs"], key=lambda d: d["weight"])

st.markdown("#### Step 1 — Start with the base diagnosis")
st.markdown(f"**Example:** `{fam['base_dx_example']}`")
base = drgs_sorted[0]
st.markdown(f"""
<div class="cmi-card">
<b>DRG {base['drg']}</b> — {base['title']}<br>
Relative weight: <span style="font-size:1.4rem; font-weight:700;">{base['weight']:.4f}</span>
&nbsp;&nbsp;·&nbsp;&nbsp; GMLOS: {base['gmlos']} days
</div>
""", unsafe_allow_html=True)

st.markdown("#### Step 2 — Now specify further (add the CC/MCC-bearing diagnosis)")
st.markdown(f"**Example:** `{fam['cc_dx_example']}`")

target_options = [f"DRG {d['drg']} — {d['title']} (weight {d['weight']:.4f})" for d in drgs_sorted[1:]]
if target_options:
    target_choice = st.radio("Which tier does the added documentation support?", target_options, index=len(target_options) - 1)
    target = drgs_sorted[1:][target_options.index(target_choice)]

    delta = target["weight"] - base["weight"]
    pct = (delta / base["weight"]) * 100
    arrow_class = "cmi-up" if delta > 0 else ("cmi-down" if delta < 0 else "cmi-flat")
    arrow = "▲" if delta > 0 else ("▼" if delta < 0 else "—")

    st.markdown(f"""
    <div class="cmi-card">
    <b>DRG {target['drg']}</b> — {target['title']}<br>
    Relative weight: <span style="font-size:1.4rem; font-weight:700;">{target['weight']:.4f}</span>
    &nbsp;&nbsp;·&nbsp;&nbsp; GMLOS: {target['gmlos']} days
    <br><br>
    <span class="{arrow_class}" style="font-size:1.3rem;">{arrow} {delta:+.4f} ({pct:+.1f}%)</span>
    &nbsp;vs. the base diagnosis
    </div>
    """, unsafe_allow_html=True)

    verify_html = (
        f'<div class="confirmed-flag">✓ Weight pulled from a live FY2026 CMS-sourced figure.</div>'
        if fam["verification"] == "cms_confirmed" else
        f'<div class="verify-flag">⚠ Typical/approximate FY-vintage weight — verify against current CMS Table 5 before real use.</div>'
    )
    st.markdown(verify_html, unsafe_allow_html=True)

st.markdown("#### Why this happens")
st.info(fam["clinical_note"])

st.divider()
st.caption("CMI Trainer v1 · Built for physician education · Not for coding, billing, or compliance sign-off.")
