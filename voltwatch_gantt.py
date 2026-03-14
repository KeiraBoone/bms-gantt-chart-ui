import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import date, timedelta
import json
import copy

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="VoltWatch BMS — Gantt",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@300;400;500;600&display=swap');
html, body, [class*="css"] { font-family: 'IBM Plex Sans', sans-serif; }
.stApp { background-color: #0d1117; color: #e6edf3; }
section[data-testid="stSidebar"] { background-color: #161b22; border-right: 1px solid #21262d; }
section[data-testid="stSidebar"] * { color: #e6edf3 !important; }
[data-testid="metric-container"] {
    background: #161b22; border: 1px solid #21262d;
    border-radius: 8px; padding: 12px 16px;
}
[data-testid="metric-container"] label {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 11px !important; text-transform: uppercase;
    letter-spacing: 0.08em; color: #8b949e !important;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 22px !important; color: #58a6ff !important;
}
h1 { font-family: 'IBM Plex Mono', monospace !important; color: #e6edf3 !important; }
h2 { font-family: 'IBM Plex Mono', monospace !important; color: #8b949e !important;
     font-size: 13px !important; text-transform: uppercase; letter-spacing: 0.1em; }
h3 { font-family: 'IBM Plex Mono', monospace !important; color: #c9d1d9 !important; }
hr { border-color: #21262d !important; }
.stTextInput input, .stNumberInput input, .stTextArea textarea {
    background: #161b22 !important; border-color: #30363d !important;
    color: #e6edf3 !important; font-family: 'IBM Plex Mono', monospace !important;
    font-size: 13px !important;
}
.stSelectbox > div > div, .stMultiSelect > div > div {
    background: #161b22 !important; border-color: #30363d !important;
    color: #e6edf3 !important; font-family: 'IBM Plex Mono', monospace !important;
    font-size: 13px !important;
}
.stMultiSelect [data-baseweb="tag"] { background: #1f3a5f !important; }
.stCheckbox label span { font-family: 'IBM Plex Mono', monospace !important; font-size: 13px !important; }
div[data-testid="stExpander"] {
    background: #161b22 !important; border: 1px solid #21262d !important;
    border-radius: 8px !important;
}
.stTabs [data-baseweb="tab-list"] { background: #161b22; border-radius: 8px; gap: 4px; }
.stTabs [data-baseweb="tab"] {
    font-family: 'IBM Plex Mono', monospace; font-size: 12px;
    color: #8b949e; background: transparent;
}
.stTabs [aria-selected="true"] { color: #e6edf3 !important; background: #21262d !important; border-radius: 6px; }
.avatar-row { display: flex; gap: 8px; flex-wrap: wrap; margin: 4px 0 12px; }
.avatar {
    width: 36px; height: 36px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-family: 'IBM Plex Mono', monospace; font-size: 11px; font-weight: 600;
    flex-shrink: 0; border: 2px solid rgba(255,255,255,0.15);
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# DEFAULT DATA
# ─────────────────────────────────────────────────────────────────────────────
DEFAULT_MEMBERS = [
    {"name": "Keira Boone", "initials": "KB", "role": "EIS",    "color": "#a78bfa"},
    {"name": "Member 2",    "initials": "M2", "role": "Thermal",        "color": "#fb923c"},
    {"name": "Member 3",    "initials": "M3", "role": "Motor / SW",     "color": "#60a5fa"},
]

DEFAULT_TRACKS = [
    {"name": "Hardware",          "color": "#2dd4bf"},
    {"name": "Layer 1 — EIS",     "color": "#a78bfa"},
    {"name": "Layer 2 — Thermal", "color": "#fb923c"},
    {"name": "Layer 3 — Motor",   "color": "#fbbf24"},
    {"name": "Software",          "color": "#60a5fa"},
]

DEFAULT_TASKS = [
    # Hardware
    dict(name="Order all components",       track="Hardware",          ws=1, we=1, cp=True,  owners=["Keira Boone","Member 2","Member 3"], desc="Place Amazon / Digi-Key orders. Confirm 2-day shipping on AD5933 and ACS712."),
    dict(name="CAD motor mount",            track="Hardware",          ws=1, we=2, cp=False, owners=["Member 3"],                          desc="Design 3D-printed motor mount in Fusion 360. Print at MIT Makerspace N51."),
    dict(name="Assemble all three layers",  track="Hardware",          ws=2, we=2, cp=False, owners=["Keira Boone","Member 2","Member 3"], desc="Wire Layer 1 (AD5933), Layer 2 (thermistors+ACS712), Layer 3 (motors+encoder)."),
    dict(name="Solder perma-proto board",   track="Hardware",          ws=3, we=3, cp=False, owners=["Member 2"],                          desc="Move stable Layer 2 circuits off breadboard. Strain-relief cables."),
    # EIS
    dict(name="AD5933 calibration",         track="Layer 1 — EIS",    ws=2, we=2, cp=True,  owners=["Keira Boone"],                       desc="Connect known RC. Verify Nyquist semicircle. CRITICAL — gates all EIS data."),
    dict(name="Cycle 0 EIS baseline",       track="Layer 1 — EIS",    ws=3, we=3, cp=True,  owners=["Keira Boone"],                       desc="Fresh CR2032 EIS sweep 100kHz to 1Hz. Log Nyquist CSV."),
    dict(name="Cycling experiment (50x)",   track="Layer 1 — EIS",    ws=4, we=5, cp=True,  owners=["Keira Boone"],                       desc="0.5C cycling across 3 conditions. Autonomous bench run."),
    dict(name="EIS snapshots every 10 cyc", track="Layer 1 — EIS",    ws=4, we=5, cp=False, owners=["Keira Boone"],                       desc="Pause cycling at cycles 10,20,30,40,50. Run full EIS sweep."),
    dict(name="Circuit fitting + stats",    track="Layer 1 — EIS",    ws=7, we=7, cp=False, owners=["Keira Boone"],                       desc="Fit Randles+SEI to all 15 spectra. Extract circuit parameters with 95% CI."),
    # Thermal
    dict(name="Thermistor calibration",     track="Layer 2 — Thermal",ws=2, we=2, cp=True,  owners=["Member 2"],                          desc="Ice-water bath and boiling water two-point calibration. Fit Steinhart-Hart B."),
    dict(name="ACS712 calibration",         track="Layer 2 — Thermal",ws=2, we=2, cp=False, owners=["Member 2"],                          desc="Pass known currents 0.1 to 2.0A. Confirm 185 mV/A linearity."),
    dict(name="Baseline thermal run",       track="Layer 2 — Thermal",ws=3, we=3, cp=False, owners=["Member 2"],                          desc="Charge cell at 0.2C. Record 4 thermistor channels + current at 10Hz."),
    dict(name="Abuse simulations x5",       track="Layer 2 — Thermal",ws=3, we=5, cp=False, owners=["Member 2"],                          desc="Apply nichrome heater at 500mW. Confirm Level 1 to 2 to 3 alert sequence."),
    dict(name="Thermal model fitting",      track="Layer 2 — Thermal",ws=7, we=7, cp=False, owners=["Member 2"],                          desc="Fit Newton cooling model. Compute early-warning lead time with 95% CI."),
    # Motor
    dict(name="Encoder calibration",        track="Layer 3 — Motor",  ws=2, we=2, cp=False, owners=["Member 3"],                          desc="Spin N20 at known voltages. Derive pulses-per-revolution."),
    dict(name="Baseline 20-pt map",         track="Layer 3 — Motor",  ws=3, we=3, cp=False, owners=["Member 3"],                          desc="Full 5x4 operating grid. 10s steady-state, 3 replicates per point."),
    dict(name="5-pt subset per 10 cycles",  track="Layer 3 — Motor",  ws=4, we=5, cp=False, owners=["Member 3"],                          desc="Re-run 5-point subset every 10 cycling checkpoints."),
    dict(name="Degraded-cell full map",     track="Layer 3 — Motor",  ws=6, we=6, cp=True,  owners=["Member 3"],                          desc="Full 20-point map on 50+ cycle-aged cell. CRITICAL — before capstone."),
    dict(name="Capstone coupling plot",     track="Layer 3 — Motor",  ws=7, we=7, cp=True,  owners=["Keira Boone","Member 2","Member 3"], desc="Scatter: motor efficiency vs R_SEI. Compute Pearson |r| > 0.8."),
    # Software
    dict(name="Repo + Python environment",  track="Software",          ws=1, we=1, cp=True,  owners=["Member 3"],                          desc="GitHub repo, feature branches. Install all Python dependencies."),
    dict(name="Arduino firmware",           track="Software",          ws=1, we=2, cp=False, owners=["Keira Boone","Member 2"],             desc="Serial packet format T1,T2,T3,T4,I,RPM,Vmotor at 115200 baud."),
    dict(name="Tab 1 — live monitor",       track="Software",          ws=3, we=5, cp=False, owners=["Member 2"],                           desc="pyserial to deque to Plotly live update 10Hz. Alert banner logic."),
    dict(name="Tab 2 — EIS + aging",        track="Software",          ws=4, we=5, cp=True,  owners=["Keira Boone"],                        desc="CSV upload to Nyquist plot to impedance.py fitting to aging trend."),
    dict(name="Tab 3+4 + integration",      track="Software",          ws=4, we=5, cp=False, owners=["Member 3"],                           desc="Motor efficiency heatmap. SoH gauge. Safety status. CSV export."),
    dict(name="Integration + polish",       track="Software",          ws=6, we=6, cp=False, owners=["Keira Boone","Member 2","Member 3"],  desc="Merge all branches. End-to-end live test. v1.0 release."),
    dict(name="Report + demo rehearsals",   track="Software",          ws=8, we=8, cp=False, owners=["Keira Boone","Member 2","Member 3"],  desc="Final report. Two full demo rehearsals (live + CSV playback fallback)."),
]

# ─────────────────────────────────────────────────────────────────────────────
# SESSION STATE INIT
# ─────────────────────────────────────────────────────────────────────────────
def init_state():
    defaults = {
        "members":        copy.deepcopy(DEFAULT_MEMBERS),
        "tracks":         copy.deepcopy(DEFAULT_TRACKS),
        "tasks":          copy.deepcopy(DEFAULT_TASKS),
        "num_weeks":      8,
        "project_name":   "VoltWatch BMS",
        "project_start":  date(2026, 3, 14),
        "show_parallel":  True,
        "parallel_start": 4,
        "parallel_end":   5,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def member_names():
    return [m["name"] for m in st.session_state.members]

def track_names():
    return [t["name"] for t in st.session_state.tracks]

def get_track_color(track_name):
    for t in st.session_state.tracks:
        if t["name"] == track_name:
            return t["color"]
    return "#888888"

def get_member(name):
    for m in st.session_state.members:
        if m["name"] == name:
            return m
    return {"name": name, "initials": name[:2].upper(), "color": "#888888", "role": ""}

def week_to_date(w, extra_days=0):
    return st.session_state.project_start + timedelta(weeks=int(w) - 1, days=extra_days)

def owners_label(owners):
    if not owners:
        return "—"
    return ", ".join(owners)

def owner_initials_html(owners):
    parts = []
    for o in owners:
        m = get_member(o)
        parts.append(
            f'<span class="avatar" style="background:{m["color"]}22;border-color:{m["color"]}44;'
            f'color:{m["color"]}">{m["initials"]}</span>'
        )
    return "".join(parts)

# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚡ Gantt Editor")
    st.markdown("---")

    # ── Team members ──────────────────────────────────────────────────────────
    with st.expander("👥 Team members", expanded=False):
        members_to_delete = []
        for i, m in enumerate(st.session_state.members):
            st.markdown(
                f'<div class="avatar" style="display:inline-flex;background:{m["color"]}22;'
                f'border-color:{m["color"]}44;color:{m["color"]};margin-bottom:6px">'
                f'{m["initials"]}</div>',
                unsafe_allow_html=True,
            )
            c1, c2 = st.columns([3, 1])
            m["name"]     = c1.text_input("Name",     value=m["name"],     key=f"m_name_{i}",     label_visibility="collapsed")
            m["initials"] = c2.text_input("Initials", value=m["initials"], key=f"m_init_{i}",     label_visibility="collapsed")
            c3, c4 = st.columns([3, 2])
            m["role"]  = c3.text_input("Role",  value=m.get("role",""),  key=f"m_role_{i}",  label_visibility="collapsed", placeholder="Role")
            m["color"] = c4.color_picker("Color", value=m["color"],      key=f"m_color_{i}", label_visibility="collapsed")
            if st.button("✕ Remove", key=f"m_del_{i}"):
                members_to_delete.append(i)
            st.markdown("<hr style='margin:6px 0;border-color:#21262d'>", unsafe_allow_html=True)

        for idx in sorted(members_to_delete, reverse=True):
            gone = st.session_state.members[idx]["name"]
            st.session_state.members.pop(idx)
            for task in st.session_state.tasks:
                task["owners"] = [o for o in task.get("owners", []) if o != gone]
        if members_to_delete:
            st.rerun()

        st.markdown("**Add member**")
        na1, na2 = st.columns([3, 1])
        nm_name = na1.text_input("Name",     key="nm_name",  label_visibility="collapsed", placeholder="Full name")
        nm_init = na2.text_input("Initials", key="nm_init",  label_visibility="collapsed", placeholder="AB")
        nb1, nb2 = st.columns([3, 2])
        nm_role  = nb1.text_input("Role",  key="nm_role",  label_visibility="collapsed", placeholder="Role")
        nm_color = nb2.color_picker("Color", value="#888888", key="nm_color", label_visibility="collapsed")
        if st.button("+ Add member", use_container_width=True, key="add_member_btn"):
            if nm_name.strip():
                st.session_state.members.append({
                    "name":     nm_name.strip(),
                    "initials": nm_init.strip().upper()[:3] or nm_name[:2].upper(),
                    "role":     nm_role.strip(),
                    "color":    nm_color,
                })
                st.rerun()

    # ── Project settings ──────────────────────────────────────────────────────
    with st.expander("⚙️ Project settings", expanded=False):
        st.session_state.project_name = st.text_input("Project name", value=st.session_state.project_name, key="proj_name_input")
        st.session_state.num_weeks    = int(st.number_input("Number of weeks", min_value=2, max_value=52, value=st.session_state.num_weeks, key="num_weeks_input"))
        st.session_state.project_start = st.date_input("Project start date", value=st.session_state.project_start, key="proj_start_input")
        st.session_state.show_parallel = st.checkbox("Show parallel window", value=st.session_state.show_parallel, key="show_parallel_cb")
        if st.session_state.show_parallel:
            ca, cb = st.columns(2)
            st.session_state.parallel_start = int(ca.number_input("From wk", min_value=1, max_value=st.session_state.num_weeks, value=int(st.session_state.parallel_start), key="par_s"))
            st.session_state.parallel_end   = int(cb.number_input("To wk",   min_value=1, max_value=st.session_state.num_weeks, value=int(st.session_state.parallel_end),   key="par_e"))

    # ── Manage tracks ─────────────────────────────────────────────────────────
    with st.expander("🎨 Manage tracks", expanded=False):
        tracks_to_delete = []
        for i, tr in enumerate(st.session_state.tracks):
            c1, c2, c3 = st.columns([3, 2, 1])
            st.session_state.tracks[i]["name"]  = c1.text_input("Name",  value=tr["name"],  key=f"tr_name_{i}",  label_visibility="collapsed")
            st.session_state.tracks[i]["color"] = c2.color_picker("Color", value=tr["color"], key=f"tr_color_{i}", label_visibility="collapsed")
            if c3.button("✕", key=f"tr_del_{i}"):
                tracks_to_delete.append(i)
        for idx in sorted(tracks_to_delete, reverse=True):
            gone = st.session_state.tracks[idx]["name"]
            st.session_state.tracks.pop(idx)
            fallback = st.session_state.tracks[0]["name"] if st.session_state.tracks else ""
            for task in st.session_state.tasks:
                if task["track"] == gone:
                    task["track"] = fallback
        if tracks_to_delete:
            st.rerun()
        st.markdown("**Add track**")
        tc1, tc2 = st.columns([3, 2])
        nt_name  = tc1.text_input("Track name", key="new_tr_name",  label_visibility="collapsed", placeholder="Track name")
        nt_color = tc2.color_picker("Color", value="#888888",        key="new_tr_color", label_visibility="collapsed")
        if st.button("+ Add track", use_container_width=True, key="add_track_btn"):
            if nt_name.strip():
                st.session_state.tracks.append({"name": nt_name.strip(), "color": nt_color})
                st.rerun()

    # ── Add new task ──────────────────────────────────────────────────────────
    with st.expander("➕ Add new task", expanded=False):
        nt_task_name = st.text_input("Task name", key="new_task_name")
        nt_track     = st.selectbox("Track", options=track_names(), key="new_task_track")
        c1, c2       = st.columns(2)
        nt_ws        = int(c1.number_input("Start week", min_value=1, max_value=st.session_state.num_weeks, value=1, key="new_task_ws"))
        nt_we        = int(c2.number_input("End week",   min_value=1, max_value=st.session_state.num_weeks, value=1, key="new_task_we"))
        nt_owners    = st.multiselect("Assign to", options=member_names(), key="new_task_owners")
        nt_cp        = st.checkbox("Critical path", key="new_task_cp")
        nt_desc      = st.text_area("Description", key="new_task_desc", height=70)
        if st.button("+ Add task", use_container_width=True, key="add_task_btn"):
            if nt_task_name.strip():
                st.session_state.tasks.append(dict(
                    name=nt_task_name.strip(), track=nt_track,
                    ws=nt_ws, we=nt_we,
                    cp=bool(nt_cp), owners=nt_owners, desc=nt_desc.strip()
                ))
                st.rerun()

    # ── Filters ───────────────────────────────────────────────────────────────
    with st.expander("🔍 Filters & display", expanded=True):
        selected_tracks  = st.multiselect("Tracks",  options=track_names(),  default=track_names(),  key="filter_tracks")
        selected_members = st.multiselect("People",  options=member_names(), default=member_names(), key="filter_members")
        show_cp_only     = st.checkbox("Critical path only",    value=False, key="filter_cp")
        show_owners_bar  = st.checkbox("Owner labels on bars",  value=True,  key="show_owners_cb")
        show_dates       = st.checkbox("Show real dates",        value=False, key="show_dates_cb")
        swimlane_mode    = st.checkbox("Swimlane view (by person)", value=False, key="swimlane_cb")

    # ── Reset / Export / Import ───────────────────────────────────────────────
    st.markdown("---")
    if st.button("↺ Reset to defaults", use_container_width=True, key="reset_btn"):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()

    export_data = json.dumps({
        "project_name":   st.session_state.project_name,
        "num_weeks":      st.session_state.num_weeks,
        "project_start":  st.session_state.project_start.isoformat(),
        "parallel_start": st.session_state.parallel_start,
        "parallel_end":   st.session_state.parallel_end,
        "members":        st.session_state.members,
        "tracks":         st.session_state.tracks,
        "tasks":          st.session_state.tasks,
    }, indent=2)
    st.download_button("⬇ Export JSON", data=export_data,
                       file_name="voltwatch_gantt.json", mime="application/json",
                       use_container_width=True, key="export_btn")
    uploaded = st.file_uploader("⬆ Import JSON", type="json", key="import_uploader")
    if uploaded:
        try:
            imp = json.load(uploaded)
            st.session_state.project_name   = imp.get("project_name", "Project")
            st.session_state.num_weeks      = int(imp.get("num_weeks", 8))
            st.session_state.project_start  = date.fromisoformat(imp.get("project_start", date.today().isoformat()))
            st.session_state.parallel_start = int(imp.get("parallel_start", 1))
            st.session_state.parallel_end   = int(imp.get("parallel_end", 2))
            st.session_state.members        = imp.get("members", [])
            st.session_state.tracks         = imp.get("tracks", [])
            st.session_state.tasks          = imp.get("tasks", [])
            st.rerun()
        except Exception as e:
            st.error(f"Import failed: {e}")

# ─────────────────────────────────────────────────────────────────────────────
# FILTER TASKS
# ─────────────────────────────────────────────────────────────────────────────
def task_matches_member_filter(task, selected):
    owners = task.get("owners", [])
    if not owners:
        return True
    return any(o in selected for o in owners)

filtered = [
    t for t in st.session_state.tasks
    if t["track"] in selected_tracks
    and task_matches_member_filter(t, selected_members)
]
if show_cp_only:
    filtered = [t for t in filtered if t["cp"]]

# ─────────────────────────────────────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(f"# {st.session_state.project_name} — Project Timeline")

# Team avatar strip
avatar_html = '<div class="avatar-row">'
for m in st.session_state.members:
    avatar_html += (
        f'<div style="display:flex;align-items:center;gap:6px;'
        f'background:#161b22;border:1px solid #21262d;border-radius:20px;'
        f'padding:4px 10px 4px 4px">'
        f'<span class="avatar" style="background:{m["color"]}22;border-color:{m["color"]}55;'
        f'color:{m["color"]};width:28px;height:28px;font-size:10px">{m["initials"]}</span>'
        f'<span style="font-family:\'IBM Plex Mono\',monospace;font-size:11px;color:#c9d1d9">'
        f'{m["name"]}</span>'
        f'<span style="font-family:\'IBM Plex Mono\',monospace;font-size:10px;color:#8b949e">'
        f'· {m.get("role","")}</span>'
        f'</div>'
    )
avatar_html += '</div>'
st.markdown(avatar_html, unsafe_allow_html=True)

# Metrics
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Tasks",         len(filtered))
c2.metric("Critical path", sum(1 for t in filtered if t["cp"]))
c3.metric("Weeks",         st.session_state.num_weeks)
c4.metric("Members",       len(st.session_state.members))
c5.metric("Tracks",        len(set(t["track"] for t in filtered)))
st.markdown("---")

# ─────────────────────────────────────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────────────────────────────────────
tab_gantt, tab_workload, tab_people, tab_edit = st.tabs([
    "📅  Gantt chart",
    "📊  Workload heatmap",
    "👥  People view",
    "✏️  Edit tasks",
])

# ═════════════════════════════════════════════════════════════════════════════
# TAB 1 — GANTT CHART
# ═════════════════════════════════════════════════════════════════════════════
with tab_gantt:

    NW = int(st.session_state.num_weeks)

    def build_gantt(tasks_list, group_by_person=False):
        fig = go.Figure()

        if group_by_person:
            # In swimlane mode, y-axis = "Person — Task"
            def y_label(t):
                if t.get("owners"):
                    return f"{t['owners'][0]}  ·  {t['name']}"
                return f"Unassigned  ·  {t['name']}"
        else:
            def y_label(t):
                return t["name"]

        for t in tasks_list:
            color  = get_track_color(t["track"])
            ws, we = int(t["ws"]), int(t["we"])
            cp     = bool(t["cp"])
            owners = t.get("owners", [])

            if show_dates:
                start_d  = week_to_date(ws)
                end_d    = week_to_date(we, extra_days=6)
                bar_x    = [(end_d - start_d).days + 1]
                bar_base = [start_d.isoformat()]
            else:
                bar_x    = [float(we - ws + 1)]
                bar_base = [float(ws) - 0.5]

            owner_str = owners_label(owners)
            hover = (
                f"<b style='color:{color}'>{t['name']}</b><br>"
                f"<span style='color:#8b949e'>Track:</span> {t['track']}<br>"
                f"<span style='color:#8b949e'>Assigned:</span> {owner_str}<br>"
                f"<span style='color:#8b949e'>Weeks:</span> {ws}–{we}<br>"
                + ("<span style='color:#f0a500'>◆ Critical path</span><br>" if cp else "")
                + (f"<br>{t['desc']}" if t.get("desc") else "")
            )

            # Avatar initials badge text for bar label
            if show_owners_bar and owners:
                initials_str = " ".join(get_member(o)["initials"] for o in owners)
                bar_text = f" {initials_str}"
            else:
                bar_text = ""

            fig.add_trace(go.Bar(
                x=bar_x,
                y=[y_label(t)],
                base=bar_base,
                orientation="h",
                marker=dict(
                    color=color,
                    opacity=1.0 if cp else 0.8,
                    line=dict(color="#f0a500" if cp else "rgba(0,0,0,0)", width=2 if cp else 0),
                ),
                text=bar_text,
                textposition="inside",
                textfont=dict(family="IBM Plex Mono", size=10, color="#0d1117"),
                hovertemplate=hover + "<extra></extra>",
                showlegend=False,
                width=0.6,
            ))

        # Parallel window
        if st.session_state.show_parallel and tasks_list:
            ps = int(st.session_state.parallel_start)
            pe = int(st.session_state.parallel_end)
            if show_dates:
                sx0  = week_to_date(ps).isoformat()
                sx1  = week_to_date(pe, extra_days=6).isoformat()
                mid_ord = (week_to_date(ps).toordinal() + week_to_date(pe, extra_days=6).toordinal()) // 2
                ax   = date.fromordinal(mid_ord).isoformat()
            else:
                sx0  = float(ps) - 0.5
                sx1  = float(pe) + 0.5
                ax   = (float(ps) + float(pe)) / 2.0

            fig.add_shape(type="rect", x0=sx0, x1=sx1, y0=0, y1=1,
                          xref="x", yref="paper",
                          fillcolor="rgba(96,165,250,0.07)",
                          line=dict(color="rgba(96,165,250,0.35)", width=1, dash="dot"))
            fig.add_annotation(x=ax, y=1.02, xref="x", yref="paper",
                               text="⟵ peak parallel window ⟶", showarrow=False,
                               font=dict(family="IBM Plex Mono", size=10, color="#60a5fa"),
                               yanchor="bottom", xanchor="center")

        # Week grid
        if show_dates:
            for w in range(1, NW + 1):
                fig.add_vline(x=week_to_date(w).isoformat(),
                              line=dict(color="rgba(255,255,255,0.05)", width=1))

        # x-axis
        if show_dates:
            xax = dict(type="date",
                       range=[week_to_date(1).isoformat(), week_to_date(NW, 7).isoformat()])
        else:
            xax = dict(type="linear", range=[0.5, float(NW) + 0.5],
                       tickvals=list(range(1, NW + 1)),
                       ticktext=[f"Wk {w}" for w in range(1, NW + 1)])

        xax.update(gridcolor="#21262d", gridwidth=0.5, showline=False, zeroline=False,
                   tickfont=dict(family="IBM Plex Mono", size=10, color="#8b949e"))

        n = max(len(tasks_list), 1)
        fig.update_layout(
            paper_bgcolor="#0d1117", plot_bgcolor="#0d1117",
            height=max(420, n * 34 + 120),
            margin=dict(l=0, r=24, t=40, b=40),
            barmode="overlay",
            xaxis=xax,
            yaxis=dict(autorange="reversed", tickfont=dict(family="IBM Plex Mono", size=11, color="#c9d1d9"),
                       gridcolor="#21262d", gridwidth=0.5, showline=False, zeroline=False),
            hoverlabel=dict(bgcolor="#161b22", bordercolor="#30363d",
                            font=dict(family="IBM Plex Sans", size=13, color="#e6edf3")),
            font=dict(family="IBM Plex Mono", color="#e6edf3"),
            dragmode="pan",
        )
        return fig

    if swimlane_mode:
        # Sort by first owner then task name
        sorted_tasks = sorted(filtered,
                              key=lambda t: (t.get("owners", ["~"])[0], t["name"]))
        fig_gantt = build_gantt(sorted_tasks, group_by_person=True)
    else:
        fig_gantt = build_gantt(filtered, group_by_person=False)

    st.plotly_chart(fig_gantt, use_container_width=True,
                    config=dict(displayModeBar=True,
                                modeBarButtonsToRemove=["lasso2d", "select2d"],
                                displaylogo=False))

    # Legend row
    active_tracks = [tr for tr in st.session_state.tracks if tr["name"] in selected_tracks]
    if active_tracks:
        leg_cols = st.columns(len(active_tracks) + 1)
        for i, tr in enumerate(active_tracks):
            c = tr["color"]
            leg_cols[i].markdown(
                f'<div style="font-family:\'IBM Plex Mono\',monospace;font-size:11px;color:{c};'
                f'display:flex;align-items:center;gap:6px">'
                f'<span style="display:inline-block;width:12px;height:12px;border-radius:2px;background:{c}"></span>'
                f'{tr["name"]}</div>', unsafe_allow_html=True)
        leg_cols[-1].markdown(
            '<div style="font-family:\'IBM Plex Mono\',monospace;font-size:11px;color:#f0a500">◆ Critical path</div>',
            unsafe_allow_html=True)

# ═════════════════════════════════════════════════════════════════════════════
# TAB 2 — WORKLOAD HEATMAP
# ═════════════════════════════════════════════════════════════════════════════
with tab_workload:
    st.markdown("### Workload heatmap — tasks per person per week")
    st.caption("Each cell = number of tasks assigned to that person that are active in that week.")

    NW = int(st.session_state.num_weeks)
    members = st.session_state.members
    weeks   = list(range(1, NW + 1))

    if not members:
        st.info("Add team members in the sidebar to see the workload heatmap.")
    else:
        # Build matrix: rows = members, cols = weeks
        matrix = np.zeros((len(members), NW), dtype=int)
        task_names_matrix = [[[] for _ in range(NW)] for _ in range(len(members))]

        for task in st.session_state.tasks:
            ws = int(task["ws"])
            we = int(task["we"])
            for owner in task.get("owners", []):
                if owner in member_names():
                    mi = member_names().index(owner)
                    for w in range(ws, we + 1):
                        if 1 <= w <= NW:
                            matrix[mi][w - 1] += 1
                            task_names_matrix[mi][w - 1].append(task["name"])

        # Hover text
        hover_text = []
        for mi, m in enumerate(members):
            row = []
            for wi in range(NW):
                names = task_names_matrix[mi][wi]
                if names:
                    cell = f"<b>{m['name']}</b> · Wk {wi+1}<br>" + "<br>".join(f"• {n}" for n in names)
                else:
                    cell = f"<b>{m['name']}</b> · Wk {wi+1}<br>No tasks"
                row.append(cell)
            hover_text.append(row)

        # Color scale using member colors (use first member color as accent)
        fig_heat = go.Figure(data=go.Heatmap(
            z=matrix,
            x=[f"Wk {w}" for w in weeks],
            y=[m["name"] for m in members],
            text=[[str(v) if v > 0 else "" for v in row] for row in matrix],
            texttemplate="%{text}",
            textfont=dict(family="IBM Plex Mono", size=13, color="#e6edf3"),
            hovertext=hover_text,
            hovertemplate="%{hovertext}<extra></extra>",
            colorscale=[
                [0.0,  "#161b22"],
                [0.01, "#0d2040"],
                [0.4,  "#185fa5"],
                [0.7,  "#378add"],
                [1.0,  "#60a5fa"],
            ],
            showscale=True,
            colorbar=dict(
                title=dict(text="Tasks", font=dict(family="IBM Plex Mono", size=11, color="#8b949e")),
                tickfont=dict(family="IBM Plex Mono", size=10, color="#8b949e"),
                thickness=12,
            ),
            xgap=3, ygap=3,
        ))

        # Parallel window band
        if st.session_state.show_parallel:
            ps = int(st.session_state.parallel_start)
            pe = int(st.session_state.parallel_end)
            # x indices are 0-based week labels
            fig_heat.add_shape(
                type="rect",
                x0=ps - 1.5, x1=pe - 0.5,
                y0=-0.5, y1=len(members) - 0.5,
                xref="x", yref="y",
                fillcolor="rgba(96,165,250,0.06)",
                line=dict(color="rgba(96,165,250,0.4)", width=1, dash="dot"),
            )

        fig_heat.update_layout(
            paper_bgcolor="#0d1117",
            plot_bgcolor="#0d1117",
            height=max(260, len(members) * 64 + 100),
            margin=dict(l=0, r=60, t=20, b=40),
            xaxis=dict(tickfont=dict(family="IBM Plex Mono", size=11, color="#8b949e"),
                       gridcolor="#0d1117", showline=False, side="top"),
            yaxis=dict(tickfont=dict(family="IBM Plex Mono", size=12, color="#c9d1d9"),
                       showline=False, autorange="reversed"),
            hoverlabel=dict(bgcolor="#161b22", bordercolor="#30363d",
                            font=dict(family="IBM Plex Sans", size=13, color="#e6edf3")),
        )
        st.plotly_chart(fig_heat, use_container_width=True,
                        config=dict(displayModeBar=False, displaylogo=False))

        # Per-person totals
        st.markdown("### Total tasks per person")
        total_cols = st.columns(len(members))
        for i, m in enumerate(members):
            total = int(matrix[i].sum())
            cp_count = sum(
                1 for task in st.session_state.tasks
                if m["name"] in task.get("owners", []) and task.get("cp")
            )
            total_cols[i].markdown(
                f'<div style="background:#161b22;border:1px solid {m["color"]}33;border-radius:8px;'
                f'padding:12px;text-align:center">'
                f'<div class="avatar" style="background:{m["color"]}22;border-color:{m["color"]}55;'
                f'color:{m["color"]};margin:0 auto 8px;width:36px;height:36px">{m["initials"]}</div>'
                f'<div style="font-family:\'IBM Plex Mono\',monospace;font-size:18px;color:{m["color"]};font-weight:600">{total}</div>'
                f'<div style="font-family:\'IBM Plex Mono\',monospace;font-size:10px;color:#8b949e">tasks assigned</div>'
                f'<div style="font-family:\'IBM Plex Mono\',monospace;font-size:10px;color:#f0a500;margin-top:4px">◆ {cp_count} critical</div>'
                f'<div style="font-family:\'IBM Plex Mono\',monospace;font-size:10px;color:#8b949e;margin-top:2px">{m.get("role","")}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

# ═════════════════════════════════════════════════════════════════════════════
# TAB 3 — PEOPLE VIEW
# ═════════════════════════════════════════════════════════════════════════════
with tab_people:
    st.markdown("### Tasks by person")

    if not st.session_state.members:
        st.info("Add team members in the sidebar.")
    else:
        person_cols = st.columns(min(len(st.session_state.members), 3))
        for i, m in enumerate(st.session_state.members):
            col = person_cols[i % 3]
            person_tasks = [
                t for t in st.session_state.tasks
                if m["name"] in t.get("owners", [])
            ]
            person_tasks.sort(key=lambda t: int(t["ws"]))

            with col:
                st.markdown(
                    f'<div style="border:1px solid {m["color"]}33;border-radius:10px;'
                    f'padding:14px;margin-bottom:12px">'
                    f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:12px">'
                    f'<span class="avatar" style="background:{m["color"]}22;border-color:{m["color"]}55;'
                    f'color:{m["color"]};width:40px;height:40px;font-size:13px">{m["initials"]}</span>'
                    f'<div><div style="font-family:\'IBM Plex Mono\',monospace;font-size:13px;color:#e6edf3;font-weight:500">'
                    f'{m["name"]}</div>'
                    f'<div style="font-family:\'IBM Plex Mono\',monospace;font-size:10px;color:#8b949e">'
                    f'{m.get("role","")} · {len(person_tasks)} tasks</div></div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

                if not person_tasks:
                    st.markdown(
                        '<div style="font-family:\'IBM Plex Mono\',monospace;font-size:11px;'
                        'color:#484f58;padding:8px 0">No tasks assigned.</div>',
                        unsafe_allow_html=True,
                    )
                else:
                    for t in person_tasks:
                        track_color = get_track_color(t["track"])
                        cp_badge = '<span style="color:#f0a500;font-size:10px"> ◆</span>' if t.get("cp") else ""
                        st.markdown(
                            f'<div style="border-left:3px solid {track_color};padding:6px 8px;'
                            f'margin-bottom:6px;background:#0d1117;border-radius:0 4px 4px 0">'
                            f'<div style="font-family:\'IBM Plex Mono\',monospace;font-size:11px;'
                            f'color:#c9d1d9;font-weight:500">{t["name"]}{cp_badge}</div>'
                            f'<div style="font-family:\'IBM Plex Mono\',monospace;font-size:10px;'
                            f'color:#8b949e">Wk {t["ws"]}–{t["we"]} · {t["track"]}</div>'
                            f'</div>',
                            unsafe_allow_html=True,
                        )

                st.markdown("</div>", unsafe_allow_html=True)

# ═════════════════════════════════════════════════════════════════════════════
# TAB 4 — EDIT TASKS
# ═════════════════════════════════════════════════════════════════════════════
with tab_edit:
    st.markdown("### Edit tasks")
    st.caption("Expand any task to edit it. Changes reflect immediately on the Gantt chart.")

    if not st.session_state.tasks:
        st.info("No tasks yet. Use '➕ Add new task' in the sidebar.")

    tasks_to_delete = []
    for i, t in enumerate(st.session_state.tasks):
        cp_marker = "◆ " if t.get("cp") else ""
        owners_str = owners_label(t.get("owners", []))
        label = f"{cp_marker}[{t['track']}]  {t['name']}  —  Wk {t['ws']}–{t['we']}  ({owners_str})"

        with st.expander(label, expanded=False):
            c1, c2 = st.columns([3, 1])
            t["name"]   = c1.text_input("Task name", value=t["name"], key=f"e_name_{i}")

            # Owner assignment — multiselect from member roster
            current_owners = [o for o in t.get("owners", []) if o in member_names()]
            t["owners"] = st.multiselect(
                "Assigned to", options=member_names(),
                default=current_owners, key=f"e_owners_{i}"
            )

            # Show avatars for current owners
            if t["owners"]:
                st.markdown(
                    '<div class="avatar-row">' + owner_initials_html(t["owners"]) + '</div>',
                    unsafe_allow_html=True,
                )

            c3, c4, c5 = st.columns([2, 1, 1])
            cur_track = t["track"] if t["track"] in track_names() else (track_names()[0] if track_names() else "")
            t["track"] = c3.selectbox("Track", options=track_names(),
                                       index=track_names().index(cur_track) if cur_track in track_names() else 0,
                                       key=f"e_track_{i}")
            t["ws"] = int(c4.number_input("Start wk", min_value=1, max_value=st.session_state.num_weeks,
                                           value=int(t["ws"]), key=f"e_ws_{i}"))
            t["we"] = int(c5.number_input("End wk",   min_value=1, max_value=st.session_state.num_weeks,
                                           value=int(t["we"]), key=f"e_we_{i}"))
            t["cp"]   = st.checkbox("Critical path", value=bool(t.get("cp", False)), key=f"e_cp_{i}")
            t["desc"] = st.text_area("Description",  value=t.get("desc", ""),        key=f"e_desc_{i}", height=70)

            if st.button("🗑 Delete this task", key=f"e_del_{i}"):
                tasks_to_delete.append(i)

    for idx in sorted(tasks_to_delete, reverse=True):
        st.session_state.tasks.pop(idx)
    if tasks_to_delete:
        st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    f'<div style="font-family:\'IBM Plex Mono\',monospace;font-size:10px;color:#484f58;text-align:center">'
    f'{st.session_state.project_name} · {len(st.session_state.members)} members · '
    f'{len(st.session_state.tasks)} tasks · {st.session_state.num_weeks} weeks'
    f'</div>',
    unsafe_allow_html=True,
)