import streamlit as st
from drg_data import (
    DIAGNOSIS_FAMILIES, VERIFICATION_NOTE, SECONDARY_DX,
    PRINCIPAL_LEVEL_CONDITIONS, group_case, MYTH_CHECKS, get_myth_check_rows,
)

st.set_page_config(page_title="CMI Trainer", page_icon="🩺", layout="wide")

# ---------- Styling: light clinical theme (matches BFMC PDF dashboard) ----------
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
    html, body, .stApp, [class*="css"] { font-family: 'IBM Plex Sans', -apple-system, sans-serif; }
    .stApp { background-color: #ffffff; color: #12242a; }
    .block-container { max-width: 880px; padding-top: 3.2rem; padding-bottom: 3rem; }
    section[data-testid="stSidebar"] { background-color: #f4f9f9; }
    h1, h2, h3, h4 { color: #12242a !important; font-weight: 600 !important; letter-spacing: -0.01em; }
    h4 { margin-top: 0.3rem !important; margin-bottom: 0.6rem !important; }
    p, span, label, .stMarkdown { color: #45575a; }
    hr { border-color: #e4ebeb; margin: 1.6rem 0 !important; }
    ::selection { background-color: #c7dede; }

    /* ---- App header ---- */
    .app-header { display: flex; align-items: center; gap: 14px; margin-bottom: 4px; padding-top: 4px; }
    .app-icon {
        width: 44px; height: 44px; border-radius: 10px; background: #1d6e6e;
        display: flex; align-items: center; justify-content: center; font-size: 22px;
        flex-shrink: 0;
    }
    .app-title { font-size: 1.9rem; font-weight: 700; color: #12242a; line-height: 1.1; margin: 0; letter-spacing: -0.015em; }
    .app-subtitle { color: #7a8a8d; font-size: 0.95rem; margin: 6px 0 0 0; }

    /* ---- Step headers with numbered badge ---- */
    .step-header { display: flex; align-items: center; gap: 10px; margin: 1.6rem 0 0.5rem 0; }
    .step-num {
        width: 26px; height: 26px; border-radius: 50%; background: #1d6e6e; color: #ffffff;
        font-size: 0.85rem; font-weight: 600; display: flex; align-items: center;
        justify-content: center; flex-shrink: 0;
    }
    .step-title { font-size: 1.15rem; font-weight: 600; color: #12242a; }

    /* ---- Diagnosis code chip (replaces jarring default markdown code spans) ---- */
    .dx-code {
        display: inline-block; background: #f4f9f9; color: #1d6e6e; border: 1px solid #c7dede;
        border-radius: 5px; padding: 3px 9px; font-family: 'SFMono-Regular', Consolas, monospace;
        font-size: 0.85rem; font-weight: 500;
    }
    .example-label { color: #7a8a8d; font-size: 0.85rem; font-weight: 500; text-transform: uppercase; letter-spacing: 0.04em; margin-bottom: 4px; }

    /* ---- Result / info cards ---- */
    .cmi-card {
        background: #f8fbfb;
        border: 1px solid #e4ebeb;
        border-left: 3px solid #1d6e6e;
        border-radius: 8px;
        padding: 18px 22px;
        margin-bottom: 14px;
        color: #12242a;
        box-shadow: 0 1px 3px rgba(18, 36, 42, 0.04);
    }
    .cmi-card.result-hero { border-left-width: 4px; background: #f4f9f9; }
    .cmi-weight { font-size: 1.6rem; font-weight: 700; color: #12242a; }
    .cmi-meta { color: #7a8a8d; font-size: 0.88rem; }
    .cmi-up { color: #3f9270; font-weight: 600; }
    .cmi-down { color: #c25b4a; font-weight: 600; }
    .cmi-flat { color: #7a8a8d; font-weight: 600; }
    .cmi-badge {
        display: inline-block; background: #e9f2f2; color: #1d6e6e;
        border-radius: 4px; padding: 3px 10px; font-size: 0.78rem; margin-right: 6px;
        border: 1px solid #c7dede; font-weight: 500; letter-spacing: 0.02em;
    }
    .cmi-note {
        background: #f4f9f9; border-left: 3px solid #1d6e6e; color: #354649;
        border-radius: 6px; padding: 14px 18px; font-size: 0.92rem; line-height: 1.6;
        margin-top: 4px;
    }
    .verify-flag {
        background: #fbf3e7; border-left: 3px solid #c98a2f; color: #8a5e1f;
        border-radius: 6px; padding: 10px 14px; font-size: 0.87rem; margin-top: 8px;
        line-height: 1.55;
    }
    .confirmed-flag {
        background: #edf6f1; border-left: 3px solid #3f9270; color: #2a6b4c;
        border-radius: 6px; padding: 10px 14px; font-size: 0.87rem; margin-top: 8px;
        line-height: 1.55;
    }
    .criteria-box {
        background: #f8fafa; border: 1px solid #e4ebeb; border-radius: 6px;
        padding: 12px 16px; margin-top: 6px; font-size: 0.88rem; color: #5a6b6e;
        line-height: 1.55;
    }
    .footer-note { color: #a3b0b2; font-size: 0.82rem; text-align: center; margin-top: 0.5rem; }

    /* ---- Native Streamlit widget theming ---- */
    .stCaption, [data-testid="stCaptionContainer"] p { color: #8a9699 !important; }

    /* Alerts (st.info etc.) — override default blue to match palette */
    div[data-testid="stAlert"] {
        background-color: #f4f9f9 !important; border: 1px solid #c7dede !important;
        border-left: 3px solid #1d6e6e !important; border-radius: 6px !important;
        color: #354649 !important;
    }
    div[data-testid="stAlert"] p { color: #354649 !important; }
    div[data-testid="stAlert"] svg { fill: #1d6e6e !important; }

    /* Expander */
    div[data-testid="stExpander"] {
        background: #fbfdfd; border: 1px solid #e4ebeb; border-radius: 8px;
        box-shadow: 0 1px 2px rgba(18, 36, 42, 0.03);
    }
    div[data-testid="stExpander"] summary { color: #12242a !important; font-weight: 500; padding: 0.7rem 1rem; }
    div[data-testid="stExpander"] summary:hover { color: #1d6e6e !important; }
    div[data-testid="stExpander"] summary svg { fill: #7a8a8d !important; }

    /* Selectbox / dropdowns */
    div[data-baseweb="select"] > div {
        background-color: #ffffff !important; border-color: #c7dede !important; color: #12242a !important;
        border-radius: 6px !important;
    }
    div[data-baseweb="select"] > div:hover { border-color: #1d6e6e !important; }
    ul[role="listbox"] { background-color: #ffffff !important; }
    li[role="option"] { color: #12242a !important; }
    li[role="option"]:hover { background-color: #e9f2f2 !important; }

    /* Multiselect selected-item tags */
    span[data-baseweb="tag"] {
        background-color: #e9f2f2 !important; border: 1px solid #1d6e6e !important; border-radius: 5px !important;
    }
    span[data-baseweb="tag"] span { color: #1d6e6e !important; }
    span[data-baseweb="tag"] svg { fill: #1d6e6e !important; }

    /* Radio buttons — color now comes correctly from theme primaryColor via config.toml;
       this just tightens spacing and label color. */
    div[role="radiogroup"] label { color: #45575a !important; }
    div[role="radiogroup"] { gap: 0.4rem; }

    /* Buttons */
    .stButton button, .stDownloadButton button {
        background-color: #e9f2f2; color: #1d6e6e; border: 1px solid #1d6e6e; border-radius: 6px;
    }
    .stButton button:hover, .stDownloadButton button:hover {
        background-color: #1d6e6e; color: #ffffff; border-color: #3f9270;
    }

    /* Section divider spacing tightened via hr rule above; hide Streamlit's default
       top padding/anchor link clutter on headers */
    [data-testid="stHeaderActionElements"] { display: none; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="app-header">
    <div class="app-icon">🩺</div>
    <div>
        <p class="app-title">CMI Trainer</p>
        <p class="app-subtitle">Train your documentation eye: see how specifying a diagnosis moves the DRG weight — one case at a time.</p>
    </div>
</div>
""", unsafe_allow_html=True)

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


def step_header(num, title):
    st.markdown(f"""
    <div class="step-header">
        <div class="step-num">{num}</div>
        <div class="step-title">{title}</div>
    </div>
    """, unsafe_allow_html=True)


def dx_example(label, code_text):
    st.markdown(f"""
    <div class="example-label">{label}</div>
    <span class="dx-code">{code_text}</span>
    """, unsafe_allow_html=True)


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

    step_header(1, "Principal diagnosis")
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

    step_header(2, "Add secondary diagnoses")
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

    step_header(3, "Result")
    st.markdown(f"""
    <div class="cmi-card">
    <div class="cmi-meta">Base (principal dx alone) — DRG {base['drg']} — {base['title']}</div>
    <span class="cmi-weight" style="font-size:1.3rem;">{base['weight']:.4f}</span>
    </div>
    """, unsafe_allow_html=True)

    if chosen_keys:
        winning_drg, contributions = group_case(selected_key, chosen_keys)
        delta = winning_drg["weight"] - base["weight"]
        pct = (delta / base["weight"]) * 100 if base["weight"] else 0
        arrow_class = "cmi-up" if delta > 0 else ("cmi-down" if delta < 0 else "cmi-flat")
        arrow = "▲" if delta > 0 else ("▼" if delta < 0 else "—")

        st.markdown(f"""
        <div class="cmi-card result-hero">
        <div class="cmi-meta">Resulting DRG {winning_drg['drg']} — {winning_drg['title']}</div>
        <span class="cmi-weight">{winning_drg['weight']:.4f}</span>
        <span class="cmi-meta">&nbsp;&nbsp;·&nbsp;&nbsp; GMLOS: {winning_drg['gmlos']} days</span>
        <br><br>
        <span class="{arrow_class}" style="font-size:1.25rem;">{arrow} {delta:+.4f} ({pct:+.1f}%)</span>
        <span class="cmi-meta">&nbsp;vs. the principal diagnosis alone</span>
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

step_header(1, "Start with the base diagnosis")
dx_example("Example", fam['base_dx_example'])
base = drgs_sorted[0]
st.markdown(f"""
<div class="cmi-card">
<div class="cmi-meta">DRG {base['drg']} — {base['title']}</div>
<span class="cmi-weight">{base['weight']:.4f}</span>
<span class="cmi-meta">&nbsp;&nbsp;·&nbsp;&nbsp; GMLOS: {base['gmlos']} days</span>
</div>
""", unsafe_allow_html=True)

step_header(2, "Now specify further (add the CC/MCC-bearing diagnosis)")
dx_example("Example", fam['cc_dx_example'])

target_options = [f"DRG {d['drg']} — {d['title']} (weight {d['weight']:.4f})" for d in drgs_sorted[1:]]
if target_options:
    target_choice = st.radio("Which tier does the added documentation support?", target_options, index=len(target_options) - 1)
    target = drgs_sorted[1:][target_options.index(target_choice)]

    delta = target["weight"] - base["weight"]
    pct = (delta / base["weight"]) * 100
    arrow_class = "cmi-up" if delta > 0 else ("cmi-down" if delta < 0 else "cmi-flat")
    arrow = "▲" if delta > 0 else ("▼" if delta < 0 else "—")

    st.markdown(f"""
    <div class="cmi-card result-hero">
    <div class="cmi-meta">DRG {target['drg']} — {target['title']}</div>
    <span class="cmi-weight">{target['weight']:.4f}</span>
    <span class="cmi-meta">&nbsp;&nbsp;·&nbsp;&nbsp; GMLOS: {target['gmlos']} days</span>
    <br><br>
    <span class="{arrow_class}" style="font-size:1.25rem;">{arrow} {delta:+.4f} ({pct:+.1f}%)</span>
    <span class="cmi-meta">&nbsp;vs. the base diagnosis</span>
    </div>
    """, unsafe_allow_html=True)

    verify_html = (
        f'<div class="confirmed-flag">✓ Weight pulled from a live FY2026 CMS-sourced figure.</div>'
        if fam["verification"] == "cms_confirmed" else
        f'<div class="verify-flag">⚠ Typical/approximate FY-vintage weight — verify against current CMS Table 5 before real use.</div>'
    )
    st.markdown(verify_html, unsafe_allow_html=True)

st.markdown("#### Why this happens")
st.markdown(f'<div class="cmi-note">{fam["clinical_note"]}</div>', unsafe_allow_html=True)

st.divider()
st.caption("CMI Trainer v1 · Built for physician education · Not for coding, billing, or compliance sign-off.")
