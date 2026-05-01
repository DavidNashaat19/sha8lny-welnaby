"""
=============================================================================
 Sha8lny Welnaby — Freelance Market Explorer
 File   : eda_app.py
 Stack  : Streamlit · Pandas · Plotly
 Input  : freelance_data.json  (produced by scraper.py)
=============================================================================
"""

import json
import re
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
FILE_PATH = "freelance_data.json"

# ---------------------------------------------------------------------------
# Page Setup
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Sha8lny Welnaby — Freelance Market Explorer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------------------------
# CSS — dark premium theme
# ---------------------------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Space+Grotesk:wght@400;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background-color: #080b14;
    color: #d4d8e8;
}
h1, h2, h3, h4 { font-family: 'Space Grotesk', sans-serif !important; }
.stApp { background-color: #080b14; }
.stTabs [data-baseweb="tab-list"] {
    background: #0f1322;
    border-radius: 12px;
    padding: 4px;
    gap: 4px;
    border: 1px solid #1e2540;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px;
    color: #6b7399;
    font-weight: 500;
    font-size: 0.85rem;
    padding: 8px 20px;
    letter-spacing: 0.03em;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, #1e3a8a, #1d4ed8) !important;
    color: #fff !important;
}
.kpi-card {
    background: linear-gradient(135deg, #0f1322 0%, #0a0d1a 100%);
    border: 1px solid #1e2540;
    border-radius: 14px;
    padding: 22px 20px;
    text-align: center;
    transition: border-color 0.25s, transform 0.2s;
}
.kpi-card:hover { border-color: #3b82f6; transform: translateY(-2px); }
.kpi-value {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 2rem;
    font-weight: 700;
    color: #60a5fa;
    line-height: 1;
}
.kpi-label {
    font-size: 0.72rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #4b5680;
    margin-top: 8px;
}
.section-badge {
    display: inline-block;
    background: rgba(59,130,246,0.12);
    border: 1px solid rgba(59,130,246,0.3);
    color: #60a5fa;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    padding: 4px 12px;
    border-radius: 20px;
    margin-bottom: 14px;
}
.chart-wrap {
    background: #0f1322;
    border: 1px solid #1e2540;
    border-radius: 14px;
    padding: 8px;
}
[data-testid="stDataFrame"] { border-radius: 10px; overflow: hidden; }
#MainMenu, footer { visibility: hidden; }
.stSelectbox > div > div { background: #0f1322 !important; border-color: #1e2540 !important; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Plotly base layout (NO yaxis key here — applied per-chart)
# ---------------------------------------------------------------------------
CHART_BG    = "#080b14"
GRID_COLOR  = "#131828"
TEXT_COLOR  = "#8b93b8"
FONT_FAMILY = "Inter, sans-serif"

BASE_LAYOUT = dict(
    paper_bgcolor=CHART_BG,
    plot_bgcolor=CHART_BG,
    font=dict(family=FONT_FAMILY, color=TEXT_COLOR, size=12),
    margin=dict(t=48, b=36, l=36, r=16),
    title_font=dict(size=15, family="Space Grotesk, sans-serif", color="#d4d8e8"),
    hoverlabel=dict(
        bgcolor="#0f1322",
        bordercolor="#1e2540",
        font_family=FONT_FAMILY,
        font_color="#d4d8e8",
    ),
    xaxis=dict(showgrid=False, zeroline=False, color=TEXT_COLOR, tickfont_color=TEXT_COLOR),
    yaxis=dict(showgrid=False, zeroline=False, color=TEXT_COLOR, tickfont_color=TEXT_COLOR),
)

PLOTLY_CONFIG = {"displayModeBar": False, "responsive": True}

SEQ_BLUE   = ["#0d1b4b", "#1e40af", "#3b82f6", "#93c5fd", "#dbeafe"]
SEQ_TEAL   = ["#0f2d2d", "#0f766e", "#14b8a6", "#5eead4", "#ccfbf1"]
DISC_COLORS = ["#3b82f6", "#06b6d4", "#8b5cf6", "#f59e0b", "#10b981", "#ef4444"]

PLATFORM_COLORS = {
    "Freelancer.com": "#3b82f6",
    "Mostaqel.com":   "#06b6d4",
}

def apply_layout(fig: go.Figure, overrides: dict = None) -> go.Figure:
    """Merge BASE_LAYOUT + overrides without key conflicts."""
    layout = dict(BASE_LAYOUT)
    if overrides:
        # Deep-merge axis dicts
        for key, val in overrides.items():
            if key in layout and isinstance(layout[key], dict) and isinstance(val, dict):
                merged = dict(layout[key])
                merged.update(val)
                layout[key] = merged
            else:
                layout[key] = val
    fig.update_layout(**layout)
    return fig


# ===========================================================================
# 1.  DATA LOADING & CLEANING
# ===========================================================================

@st.cache_data(show_spinner="Loading & cleaning data …")
def load_and_clean(path: str) -> pd.DataFrame:
    raw_path = Path(path)
    if not raw_path.exists():
        st.error(f"Cannot find **{path}**. Make sure `scraper.py` has run first.")
        st.stop()

    with open(raw_path, encoding="utf-8") as f:
        data = json.load(f)

    projects = data.get("projects", [])
    if not projects:
        st.warning("The JSON file exists but contains no projects.")
        st.stop()

    df = pd.DataFrame(projects)

    str_cols = ["platform", "title", "url", "budget_currency",
                "budget_type", "category", "posted_date", "description_snippet"]
    for col in str_cols:
        if col in df.columns:
            df[col] = df[col].fillna("").astype(str).str.strip()

    for col in ["budget_min", "budget_max"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df["budget_mid"] = df[["budget_min", "budget_max"]].mean(axis=1)

    if "posted_date" in df.columns:
        df["posted_date_parsed"] = pd.to_datetime(df["posted_date"], errors="coerce")

    if "skills" in df.columns:
        def _to_list(val):
            if isinstance(val, list):
                return [s.strip() for s in val if str(s).strip()]
            if isinstance(val, str) and val:
                return [s.strip() for s in re.split(r"[,;|]", val) if s.strip()]
            return []
        df["skills"] = df["skills"].apply(_to_list)
        df["skills_count"] = df["skills"].apply(len)
    else:
        df["skills"] = [[] for _ in range(len(df))]
        df["skills_count"] = 0

    if "category" in df.columns:
        df["category"] = df["category"].replace("", "Uncategorised")

    return df


def explode_skills(df: pd.DataFrame) -> pd.DataFrame:
    if "skills" not in df.columns:
        return pd.DataFrame(columns=["skill", "platform"])
    exp = df[["platform", "skills"]].explode("skills").dropna(subset=["skills"])
    exp = exp[exp["skills"].str.strip() != ""].rename(columns={"skills": "skill"})
    return exp


# ===========================================================================
# 2.  CHART BUILDERS
# ===========================================================================

def chart_top_skills(df_exp: pd.DataFrame, n: int = 12) -> go.Figure:
    counts = df_exp["skill"].value_counts().head(n).reset_index()
    counts.columns = ["skill", "count"]

    fig = px.bar(
        counts, x="count", y="skill", orientation="h",
        text="count",
        color="count",
        color_continuous_scale=SEQ_BLUE[::-1],
    )
    fig.update_traces(
        textposition="outside",
        marker_line_width=0,
        textfont=dict(color="#8b93b8", size=11),
    )
    return apply_layout(fig, {
        "title": f"Top {n} Most In-Demand Skills",
        "yaxis": {"categoryorder": "total ascending"},
        "coloraxis_showscale": False,
        "height": 460,
    })


def chart_skills_by_platform(df_exp: pd.DataFrame, n: int = 10) -> go.Figure:
    platforms = df_exp["platform"].unique()
    fig = go.Figure()
    colors = list(PLATFORM_COLORS.values())
    for i, plat in enumerate(platforms):
        sub = df_exp[df_exp["platform"] == plat]["skill"].value_counts().head(n).reset_index()
        sub.columns = ["skill", "count"]
        fig.add_trace(go.Bar(
            name=plat, x=sub["count"], y=sub["skill"],
            orientation="h",
            marker_color=colors[i % len(colors)],
            marker_line_width=0,
            text=sub["count"],
            textposition="outside",
            textfont=dict(color="#8b93b8", size=10),
        ))
    fig.update_layout(barmode="group")
    return apply_layout(fig, {
        "title": "Top Skills by Platform",
        "yaxis": {"categoryorder": "total ascending"},
        "height": 460,
        "legend": dict(bgcolor="rgba(0,0,0,0)", borderwidth=0),
    })


def chart_budget_histogram(df: pd.DataFrame) -> go.Figure:
    budgets = df["budget_mid"].dropna()
    upper = budgets.quantile(0.99)
    budgets = budgets[budgets <= upper]

    fig = px.histogram(
        budgets, nbins=40,
        color_discrete_sequence=["#3b82f6"],
        labels={"value": "Budget (mid-point)", "count": "Projects"},
        opacity=0.85,
    )
    fig.update_traces(marker_line_width=0.4, marker_line_color="#080b14")
    return apply_layout(fig, {
        "title": "Budget Distribution (mid-point, 99th pct cap)",
        "xaxis": {"title": "Budget"},
        "yaxis": {"title": "Number of Projects"},
        "showlegend": False,
        "height": 380,
    })


def chart_budget_box(df: pd.DataFrame) -> go.Figure:
    sub = df.dropna(subset=["budget_mid", "platform"])
    upper = sub["budget_mid"].quantile(0.99)
    sub = sub[sub["budget_mid"] <= upper]

    fig = px.box(
        sub, x="platform", y="budget_mid",
        color="platform",
        color_discrete_map=PLATFORM_COLORS,
        points="outliers",
        labels={"platform": "Platform", "budget_mid": "Budget"},
    )
    fig.update_traces(marker_size=3)
    return apply_layout(fig, {
        "title": "Budget Spread by Platform",
        "showlegend": False,
        "height": 360,
    })


def chart_budget_type_pie(df: pd.DataFrame) -> go.Figure:
    counts = df["budget_type"].value_counts().reset_index()
    counts.columns = ["type", "count"]

    fig = px.pie(
        counts, names="type", values="count", hole=0.58,
        color_discrete_sequence=DISC_COLORS,
    )
    fig.update_traces(
        textposition="outside",
        textinfo="label+percent",
        pull=[0.04] * len(counts),
        marker=dict(line=dict(color="#080b14", width=2)),
    )
    return apply_layout(fig, {
        "title": "Budget Type Split",
        "showlegend": True,
        "legend": dict(bgcolor="rgba(0,0,0,0)", borderwidth=0),
        "height": 360,
    })


def chart_projects_per_platform(df: pd.DataFrame) -> go.Figure:
    counts = df["platform"].value_counts().reset_index()
    counts.columns = ["platform", "count"]
    colors = [PLATFORM_COLORS.get(p, "#8b5cf6") for p in counts["platform"]]

    fig = go.Figure(go.Bar(
        x=counts["platform"], y=counts["count"],
        marker_color=colors,
        marker_line_width=0,
        text=counts["count"],
        textposition="outside",
        textfont=dict(color="#8b93b8"),
    ))
    return apply_layout(fig, {
        "title": "Projects per Platform",
        "yaxis": {"title": "Number of Projects"},
        "showlegend": False,
        "height": 320,
    })


def chart_top_categories(df: pd.DataFrame, n: int = 12) -> go.Figure:
    sub = df[(df["category"].str.strip() != "") & (df["category"] != "Uncategorised")]
    counts = sub["category"].value_counts().head(n).reset_index()
    counts.columns = ["category", "count"]

    fig = px.bar(
        counts, x="count", y="category", orientation="h",
        text="count",
        color="count",
        color_continuous_scale=SEQ_TEAL[::-1],
    )
    fig.update_traces(textposition="outside", marker_line_width=0,
                      textfont=dict(color="#8b93b8", size=11))
    return apply_layout(fig, {
        "title": f"Top {n} Project Categories",
        "yaxis": {"categoryorder": "total ascending"},
        "coloraxis_showscale": False,
        "height": 460,
    })


def chart_skills_per_project(df: pd.DataFrame) -> go.Figure:
    counts = df["skills_count"].value_counts().sort_index().reset_index()
    counts.columns = ["skills_count", "projects"]

    fig = px.bar(
        counts, x="skills_count", y="projects",
        color="projects",
        color_continuous_scale=SEQ_BLUE[::-1],
        labels={"skills_count": "Skills per Project", "projects": "# Projects"},
    )
    fig.update_traces(marker_line_width=0)
    return apply_layout(fig, {
        "title": "Skills per Project Distribution",
        "coloraxis_showscale": False,
        "height": 320,
    })


def chart_category_budget(df: pd.DataFrame, n: int = 10) -> go.Figure:
    sub = df[(df["category"] != "Uncategorised") & df["budget_mid"].notna()]
    top_cats = sub["category"].value_counts().head(n).index.tolist()
    sub = sub[sub["category"].isin(top_cats)]
    upper = sub["budget_mid"].quantile(0.99)
    sub = sub[sub["budget_mid"] <= upper]

    avg = sub.groupby("category")["budget_mid"].median().sort_values(ascending=False).reset_index()
    avg.columns = ["category", "median_budget"]

    fig = px.bar(
        avg, x="median_budget", y="category", orientation="h",
        text=avg["median_budget"].map(lambda x: f"${x:,.0f}"),
        color="median_budget",
        color_continuous_scale=SEQ_TEAL[::-1],
    )
    fig.update_traces(textposition="outside", marker_line_width=0,
                      textfont=dict(color="#8b93b8", size=11))
    return apply_layout(fig, {
        "title": "Median Budget by Category (Top 10)",
        "xaxis": {"title": "Median Budget ($)"},
        "yaxis": {"categoryorder": "total ascending"},
        "coloraxis_showscale": False,
        "height": 400,
    })


# ===========================================================================
# 3.  MAIN APP
# ===========================================================================

def main():
    df = load_and_clean(FILE_PATH)
    df_skills = explode_skills(df)

    # ── Header ──────────────────────────────────────────────────────────────
    st.markdown("""
    <div style='padding: 28px 0 4px 0;'>
        <h1 style='font-family:"Space Grotesk",sans-serif;font-size:2.4rem;
                   font-weight:700;margin:0;color:#e8ecff;letter-spacing:-0.02em;'>
            Sha8lny Welnaby
            <span style='color:#3b82f6;'> · Freelance Market Explorer</span>
        </h1>
        <p style='color:#3d4569;font-size:0.82rem;margin-top:8px;letter-spacing:0.06em;'>
            CS313x INFORMATION RETRIEVAL &nbsp;·&nbsp;
            DATA SOURCE: FREELANCER.COM &amp; MOSTAQEL.COM
        </p>
    </div>
    <hr style='border:none;border-top:1px solid #1e2540;margin:8px 0 24px 0;'>
    """, unsafe_allow_html=True)

    # ── Sidebar ──────────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown("## Filters")
        platforms = ["All"] + sorted(df["platform"].unique().tolist())
        selected_platform = st.selectbox("Platform", platforms)

        budget_types = ["All"] + sorted(df["budget_type"].unique().tolist())
        selected_btype = st.selectbox("Budget Type", budget_types)

        st.markdown("---")
        st.caption(f"Data file: `{FILE_PATH}`")
        st.caption(f"Total raw rows: {len(df):,}")

    # ── Apply filters ────────────────────────────────────────────────────────
    fdf = df.copy()
    if selected_platform != "All":
        fdf = fdf[fdf["platform"] == selected_platform]
    if selected_btype != "All":
        fdf = fdf[fdf["budget_type"] == selected_btype]
    fdf_skills = explode_skills(fdf)

    # ── KPIs ─────────────────────────────────────────────────────────────────
    total_projects  = len(fdf)
    avg_budget      = fdf["budget_mid"].mean()
    median_budget   = fdf["budget_mid"].median()
    pct_with_budget = (fdf["budget_mid"].notna().sum() / max(total_projects, 1)) * 100
    unique_skills   = fdf_skills["skill"].nunique() if not fdf_skills.empty else 0
    platform_count  = fdf["platform"].nunique()

    kpis = [
        ("Total Projects",  f"{total_projects:,}"),
        ("Platforms",       f"{platform_count}"),
        ("Avg Budget",      f"${avg_budget:,.0f}" if pd.notna(avg_budget) else "N/A"),
        ("Median Budget",   f"${median_budget:,.0f}" if pd.notna(median_budget) else "N/A"),
        ("Budget Coverage", f"{pct_with_budget:.0f}%"),
        ("Unique Skills",   f"{unique_skills:,}"),
    ]
    cols = st.columns(6)
    for col, (label, value) in zip(cols, kpis):
        with col:
            st.markdown(f"""
            <div class='kpi-card'>
                <div class='kpi-value'>{value}</div>
                <div class='kpi-label'>{label}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Tabs ─────────────────────────────────────────────────────────────────
    tab1, tab2, tab3, tab4 = st.tabs([
        "🛠  Skills Analysis",
        "💰  Budget Insights",
        "📂  Categories",
        "🗄  Raw Data",
    ])

    # ── Tab 1: Skills ────────────────────────────────────────────────────────
    with tab1:
        st.markdown("<div class='section-badge'>Skills Overview</div>", unsafe_allow_html=True)
        c1, c2 = st.columns([3, 2])
        with c1:
            if not fdf_skills.empty:
                st.plotly_chart(chart_top_skills(fdf_skills), use_container_width=True,
                                config=PLOTLY_CONFIG)
            else:
                st.info("No skill data available.")
        with c2:
            st.plotly_chart(chart_projects_per_platform(fdf), use_container_width=True,
                            config=PLOTLY_CONFIG)
            st.plotly_chart(chart_skills_per_project(fdf), use_container_width=True,
                            config=PLOTLY_CONFIG)

        if len(fdf["platform"].unique()) > 1:
            with st.expander("Skills by Platform Comparison", expanded=False):
                st.plotly_chart(chart_skills_by_platform(fdf_skills), use_container_width=True,
                                config=PLOTLY_CONFIG)

    # ── Tab 2: Budget ─────────────────────────────────────────────────────────
    with tab2:
        st.markdown("<div class='section-badge'>Budget Analysis</div>", unsafe_allow_html=True)
        has_budget = fdf["budget_mid"].notna().sum() > 0
        if has_budget:
            b1, b2 = st.columns(2)
            with b1:
                st.plotly_chart(chart_budget_histogram(fdf), use_container_width=True,
                                config=PLOTLY_CONFIG)
            with b2:
                st.plotly_chart(chart_budget_type_pie(fdf), use_container_width=True,
                                config=PLOTLY_CONFIG)
            if len(fdf["platform"].unique()) > 1:
                st.plotly_chart(chart_budget_box(fdf), use_container_width=True,
                                config=PLOTLY_CONFIG)
        else:
            st.info("No numeric budget data available for the current filter.")

    # ── Tab 3: Categories ────────────────────────────────────────────────────
    with tab3:
        st.markdown("<div class='section-badge'>Category Breakdown</div>", unsafe_allow_html=True)
        c3, c4 = st.columns(2)
        with c3:
            st.plotly_chart(chart_top_categories(fdf), use_container_width=True,
                            config=PLOTLY_CONFIG)
        with c4:
            if fdf["budget_mid"].notna().sum() > 0:
                st.plotly_chart(chart_category_budget(fdf), use_container_width=True,
                                config=PLOTLY_CONFIG)
            else:
                st.info("Budget data unavailable.")

    # ── Tab 4: Raw Data ───────────────────────────────────────────────────────
    with tab4:
        st.markdown("<div class='section-badge'>Sample Data</div>", unsafe_allow_html=True)
        display_cols = [c for c in [
            "platform", "title", "budget_min", "budget_max",
            "budget_currency", "budget_type", "category",
            "posted_date", "skills_count",
        ] if c in fdf.columns]

        st.markdown(f"Showing **{min(50, len(fdf))}** of **{len(fdf):,}** filtered projects")
        st.dataframe(fdf[display_cols].head(50), use_container_width=True, height=400)

        with st.expander("Download filtered data as CSV"):
            csv = fdf[display_cols].to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name="sha8lny_filtered.csv",
                mime="text/csv",
            )

    # ── Footer ────────────────────────────────────────────────────────────────
    st.markdown("""
    <hr style='border:none;border-top:1px solid #1e2540;margin:40px 0 12px 0;'>
    <p style='color:#2a3050;font-size:0.72rem;text-align:center;letter-spacing:0.08em;'>
        SHA8LNY WELNABY &nbsp;·&nbsp; CS313x Information Retrieval &nbsp;·&nbsp;
        Freelancer.com &amp; Mostaqel.com
    </p>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()