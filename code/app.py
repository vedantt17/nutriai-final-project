from __future__ import annotations

from html import escape
from pathlib import Path

import pandas as pd

try:
    import streamlit as st
except ModuleNotFoundError as exc:
    raise SystemExit("Streamlit is not installed. Run: pip install -r requirements.txt") from exc

from nutriai import NutriAIPlanner, UserProfile
from nutriai.export import (
    capability_dataframe,
    daily_totals_dataframe,
    dataframe_to_csv_bytes,
    exclusions_dataframe,
    plan_dataframe,
    rda_dataframe,
)
from nutriai.personas import REQUIRED_PERSONAS, persona_by_name


PROJECT_ROOT = Path(__file__).resolve().parents[1]


st.set_page_config(
    page_title="NutriAI",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)

def inject_design_system() -> None:
    st.markdown(
        """
        <style>
          :root {
            --nutri-bg: #f7faf7;
            --nutri-bg-soft: #edf6f1;
            --nutri-panel: #ffffff;
            --nutri-panel-tint: #fbfdfb;
            --nutri-ink: #18201f;
            --nutri-muted: #61716b;
            --nutri-line: #d9e5dd;
            --nutri-accent: #2f6f62;
            --nutri-accent-soft: #e3f2ed;
            --nutri-accent-pale: #f1f8f5;
            --nutri-shadow: 0 14px 34px rgba(31, 72, 59, 0.08);
          }

          html, body, .stApp {
            background: var(--nutri-bg) !important;
            color: var(--nutri-ink) !important;
            font-family: "Aptos", "Segoe UI", "Geist", Arial, sans-serif;
          }

          [data-testid="stToolbarActions"],
          [data-testid="stStatusWidget"],
          [data-testid="stAppDeployButton"],
          #MainMenu,
          footer {
            display: none !important;
          }

          header[data-testid="stHeader"] {
            display: block !important;
            background: transparent !important;
            box-shadow: none !important;
            pointer-events: none;
          }

          header[data-testid="stHeader"] * {
            pointer-events: auto;
          }

          [data-testid="stToolbar"] {
            display: flex !important;
            background: transparent !important;
            pointer-events: none;
          }

          [data-testid="stToolbar"] button[data-testid="stExpandSidebarButton"] {
            pointer-events: auto;
          }

          div[data-testid="stDecoration"] {
            display: none;
          }

          [data-testid="stSidebarCollapseButton"],
          [data-testid="stSidebarCollapseButton"] button,
          [data-testid="stSidebarCollapsedControl"],
          [data-testid="stSidebarCollapsedControl"] button,
          button[data-testid="stExpandSidebarButton"] {
            visibility: visible !important;
            opacity: 1 !important;
          }

          [data-testid="stSidebarCollapseButton"] button,
          [data-testid="stSidebarCollapsedControl"] button,
          button[data-testid="stExpandSidebarButton"],
          button[data-testid="stBaseButton-headerNoPadding"] {
            color: var(--nutri-accent) !important;
            border-radius: 10px !important;
            background: rgba(255, 255, 255, 0.88) !important;
            border: 1px solid #cce5da !important;
            box-shadow: 0 8px 20px rgba(31, 72, 59, 0.08) !important;
          }

          [data-testid="stSidebarCollapseButton"] button:hover,
          [data-testid="stSidebarCollapsedControl"] button:hover,
          button[data-testid="stExpandSidebarButton"]:hover,
          button[data-testid="stBaseButton-headerNoPadding"]:hover {
            background: var(--nutri-accent-pale) !important;
            border-color: #a9d5c6 !important;
          }

          button[data-testid="stExpandSidebarButton"] {
            position: fixed !important;
            top: 14px !important;
            left: 14px !important;
            z-index: 999999 !important;
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
            width: 38px !important;
            height: 38px !important;
            min-width: 38px !important;
            min-height: 38px !important;
          }

          .block-container {
            max-width: 1480px;
            padding-top: 2.2rem;
            padding-bottom: 3rem;
          }

          [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #ffffff 0%, #f2f8f4 100%) !important;
            border-right: 1px solid var(--nutri-line);
            box-shadow: 8px 0 30px rgba(31, 72, 59, 0.05);
          }

          [data-testid="stSidebar"] label,
          [data-testid="stSidebar"] p,
          [data-testid="stSidebar"] span {
            color: var(--nutri-ink) !important;
          }

          [data-testid="stSidebar"] label {
            font-size: 0.86rem;
            font-weight: 720;
          }

          .stTextInput input,
          .stNumberInput input,
          [data-baseweb="select"] > div,
          [data-baseweb="input"] {
            min-height: 42px;
            background: #ffffff !important;
            color: var(--nutri-ink) !important;
            border: 1px solid var(--nutri-line) !important;
            border-radius: 10px !important;
            box-shadow: none !important;
          }

          .stTextInput input:focus,
          .stNumberInput input:focus,
          [data-baseweb="select"] > div:focus-within,
          [data-baseweb="input"]:focus-within {
            border-color: var(--nutri-accent) !important;
            box-shadow: 0 0 0 3px rgba(47, 111, 98, 0.13) !important;
          }

          [data-baseweb="tag"] {
            background: var(--nutri-accent-soft) !important;
            border: 1px solid #c7e2d7 !important;
            border-radius: 999px !important;
          }

          [data-baseweb="tag"] span {
            color: #1f5f53 !important;
            font-weight: 700 !important;
          }

          .stCheckbox label span {
            color: var(--nutri-ink) !important;
          }

          .stButton > button,
          .stDownloadButton > button,
          button[kind="primary"],
          button[kind="secondary"] {
            min-height: 42px;
            border-radius: 10px !important;
            border: 1px solid var(--nutri-accent) !important;
            color: #ffffff !important;
            background: var(--nutri-accent) !important;
            font-weight: 750 !important;
            box-shadow: 0 10px 24px rgba(47, 111, 98, 0.16);
            transition: transform 140ms ease, box-shadow 140ms ease, background 140ms ease;
          }

          .stButton > button:hover,
          .stDownloadButton > button:hover {
            background: #24594f !important;
            border-color: #24594f !important;
            transform: translateY(-1px);
            box-shadow: 0 14px 28px rgba(47, 111, 98, 0.22);
          }

          .nutri-hero {
            display: grid;
            grid-template-columns: minmax(0, 1.45fr) minmax(300px, 0.9fr);
            gap: 1.1rem;
            align-items: stretch;
            padding: 28px;
            border: 1px solid var(--nutri-line);
            border-radius: 18px;
            background:
              radial-gradient(circle at 92% 8%, rgba(47, 111, 98, 0.12), transparent 30%),
              linear-gradient(135deg, #ffffff 0%, #f3f9f5 100%);
            box-shadow: var(--nutri-shadow);
          }

          .nutri-eyebrow {
            color: var(--nutri-accent);
            font-size: 0.78rem;
            font-weight: 780;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            margin-bottom: 0.35rem;
          }

          .nutri-title {
            color: var(--nutri-ink);
            font-size: clamp(2.35rem, 4.4vw, 4.4rem);
            line-height: 0.96;
            font-weight: 840;
            letter-spacing: 0;
            margin: 0;
          }

          .nutri-subtitle {
            color: var(--nutri-muted);
            max-width: 780px;
            font-size: 1.02rem;
            line-height: 1.62;
            margin: 1rem 0 0;
          }

          .nutri-profile-card {
            border: 1px solid var(--nutri-line);
            border-radius: 16px;
            background: rgba(255, 255, 255, 0.88);
            padding: 18px;
          }

          .nutri-profile-name {
            color: var(--nutri-ink);
            font-size: 1.18rem;
            font-weight: 800;
            margin-bottom: 0.72rem;
          }

          .nutri-pill-row {
            display: flex;
            flex-wrap: wrap;
            gap: 0.45rem;
          }

          .nutri-pill {
            display: inline-flex;
            align-items: center;
            min-height: 30px;
            padding: 0 0.72rem;
            border-radius: 999px;
            background: var(--nutri-accent-pale);
            border: 1px solid #cce5da;
            color: #24594f;
            font-size: 0.8rem;
            font-weight: 730;
            white-space: nowrap;
          }

          .metric-grid {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 0.95rem;
            margin-top: 1rem;
          }

          .metric-card {
            min-height: 112px;
            padding: 18px 18px 16px;
            border-radius: 16px;
            background: var(--nutri-panel);
            border: 1px solid var(--nutri-line);
            box-shadow: 0 10px 28px rgba(31, 72, 59, 0.06);
          }

          .metric-label {
            color: var(--nutri-muted);
            font-size: 0.78rem;
            font-weight: 780;
            letter-spacing: 0.04em;
            text-transform: uppercase;
          }

          .metric-value {
            color: var(--nutri-ink);
            font-size: clamp(1.78rem, 2.4vw, 2.55rem);
            line-height: 1.1;
            font-weight: 830;
            margin-top: 0.55rem;
          }

          .metric-note {
            color: var(--nutri-muted);
            font-size: 0.78rem;
            margin-top: 0.25rem;
          }

          .section-heading {
            display: flex;
            align-items: flex-end;
            justify-content: space-between;
            gap: 1rem;
            margin: 1.15rem 0 0.55rem;
          }

          .section-heading h2 {
            color: var(--nutri-ink);
            font-size: 1.16rem;
            line-height: 1.2;
            letter-spacing: 0;
            margin: 0;
          }

          .section-heading p {
            color: var(--nutri-muted);
            font-size: 0.9rem;
            margin: 0.25rem 0 0;
          }

          .status-grid {
            display: grid;
            grid-template-columns: repeat(6, minmax(0, 1fr));
            gap: 0.6rem;
            margin: 0.8rem 0 0.25rem;
          }

          .status-chip {
            min-height: 58px;
            padding: 10px 12px;
            border: 1px solid #cce5da;
            border-radius: 12px;
            background: #ffffff;
            color: var(--nutri-ink);
          }

          .status-chip strong {
            display: block;
            color: #24594f;
            font-size: 0.74rem;
            line-height: 1.25;
          }

          .status-chip span {
            display: block;
            color: var(--nutri-muted);
            font-size: 0.72rem;
            margin-top: 0.25rem;
          }

          .macro-panel {
            display: grid;
            grid-template-columns: minmax(220px, 0.62fr) minmax(320px, 1fr);
            gap: 1rem;
            align-items: center;
            margin: 0.8rem 0 1rem;
            padding: 18px;
            border: 1px solid var(--nutri-line);
            border-radius: 16px;
            background: linear-gradient(135deg, #ffffff 0%, #f8fcfa 100%);
            box-shadow: 0 12px 30px rgba(31, 72, 59, 0.06);
          }

          .macro-donut-wrap {
            display: flex;
            align-items: center;
            gap: 1.05rem;
          }

          .macro-donut {
            position: relative;
            width: 138px;
            aspect-ratio: 1;
            flex: 0 0 138px;
            border-radius: 50%;
            box-shadow: inset 0 0 0 1px rgba(24, 32, 31, 0.04), 0 12px 28px rgba(31, 72, 59, 0.08);
          }

          .macro-donut::after {
            content: "";
            position: absolute;
            inset: 28px;
            border-radius: 50%;
            background: #ffffff;
            border: 1px solid var(--nutri-line);
          }

          .macro-donut-center {
            position: absolute;
            inset: 38px;
            z-index: 1;
            display: grid;
            place-items: center;
            text-align: center;
            color: var(--nutri-ink);
          }

          .macro-donut-center strong {
            display: block;
            font-size: 1.18rem;
            line-height: 1;
            font-weight: 840;
          }

          .macro-donut-center span {
            display: block;
            margin-top: 0.18rem;
            color: var(--nutri-muted);
            font-size: 0.68rem;
            font-weight: 720;
            text-transform: uppercase;
            letter-spacing: 0.04em;
          }

          .macro-donut-svg {
            width: 172px;
            height: 172px;
            overflow: visible;
            flex: 0 0 172px;
          }

          .macro-slice circle {
            fill: none;
            cursor: pointer;
            pointer-events: visibleStroke;
            stroke-width: 22;
            transform: rotate(-90deg);
            transform-origin: 60px 60px;
            transition: stroke-width 140ms ease, filter 140ms ease, opacity 140ms ease;
          }

          .macro-slice circle:focus {
            outline: none;
          }

          .macro-slice:hover circle,
          .macro-slice:focus-within circle {
            filter: drop-shadow(0 5px 8px rgba(31, 72, 59, 0.18));
            opacity: 0.96;
            stroke-width: 26;
          }

          .macro-svg-tooltip {
            opacity: 0;
            pointer-events: none;
            transform: translateY(4px);
            transition: opacity 120ms ease, transform 120ms ease;
          }

          .macro-slice:hover .macro-svg-tooltip,
          .macro-slice:focus-within .macro-svg-tooltip {
            opacity: 1;
            transform: translateY(0);
          }

          .macro-kicker {
            color: var(--nutri-accent);
            font-size: 0.72rem;
            font-weight: 820;
            letter-spacing: 0.08em;
            text-transform: uppercase;
          }

          .macro-title {
            color: var(--nutri-ink);
            font-size: 1.08rem;
            line-height: 1.2;
            font-weight: 820;
            margin-top: 0.25rem;
          }

          .macro-note {
            color: var(--nutri-muted);
            font-size: 0.84rem;
            line-height: 1.45;
            margin-top: 0.35rem;
          }

          .macro-legend {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 0.7rem;
          }

          .macro-legend-item {
            min-height: 78px;
            padding: 12px;
            border: 1px solid var(--nutri-line);
            border-radius: 12px;
            background: rgba(255, 255, 255, 0.72);
          }

          .macro-label {
            display: flex;
            align-items: center;
            gap: 0.4rem;
            color: var(--nutri-muted);
            font-size: 0.74rem;
            font-weight: 780;
            text-transform: uppercase;
            letter-spacing: 0.04em;
          }

          .macro-dot {
            width: 9px;
            height: 9px;
            border-radius: 50%;
            flex: 0 0 9px;
          }

          .macro-percent {
            color: var(--nutri-ink);
            font-size: 1.45rem;
            line-height: 1.1;
            font-weight: 840;
            margin-top: 0.55rem;
          }

          .macro-grams {
            color: var(--nutri-muted);
            font-size: 0.78rem;
            margin-top: 0.18rem;
          }

          div[data-testid="stDataFrame"] {
            border: 1px solid var(--nutri-line);
            border-radius: 14px;
            overflow: hidden;
            background: #ffffff;
            box-shadow: 0 12px 30px rgba(31, 72, 59, 0.05);
          }

          div[data-testid="stDataFrame"] div {
            color: var(--nutri-ink);
          }

          .stTabs [data-baseweb="tab-list"] {
            gap: 0.35rem;
            border-bottom: 1px solid var(--nutri-line);
          }

          .stTabs [data-baseweb="tab"] {
            min-height: 42px;
            padding: 0 12px;
            color: var(--nutri-muted);
            border-radius: 10px 10px 0 0;
            font-weight: 720;
          }

          .stTabs [aria-selected="true"] {
            color: var(--nutri-accent) !important;
            background: #ffffff;
          }

          .stAlert {
            border-radius: 12px;
          }

          @media (max-width: 980px) {
            .nutri-hero,
            .metric-grid,
            .status-grid,
            .macro-panel,
            .macro-legend {
              grid-template-columns: 1fr;
            }

            .macro-donut-wrap {
              align-items: flex-start;
              flex-wrap: wrap;
            }

            .block-container {
              padding-left: 1rem;
              padding-right: 1rem;
            }
          }
        </style>
        """,
        unsafe_allow_html=True,
    )


@st.cache_resource(show_spinner=False)
def load_planner() -> NutriAIPlanner:
    return NutriAIPlanner(project_root=PROJECT_ROOT)


@st.cache_data(show_spinner=False)
def load_source_inventory() -> pd.DataFrame:
    path = PROJECT_ROOT / "data" / "source_inventory.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


@st.cache_data(show_spinner=False)
def load_usda_reference_summary() -> dict[str, int]:
    path = PROJECT_ROOT / "data" / "usda_fooddata_reference.csv"
    if not path.exists():
        return {"rows": 0, "api_matches": 0, "source_reference_rows": 0, "offline_reference_rows": 0}
    data = pd.read_csv(path)
    matches = data.get("fdc_id", pd.Series(dtype=str)).fillna("").astype(str).str.strip().ne("").sum()
    source_reference_rows = data.get("source_reference_id", pd.Series(dtype=str)).fillna("").astype(str).str.strip().ne("").sum()
    return {
        "rows": int(len(data)),
        "api_matches": int(matches),
        "source_reference_rows": int(source_reference_rows),
        "offline_reference_rows": int(max(source_reference_rows - matches, 0)),
    }


@st.cache_data(show_spinner=False)
def load_food_database_summary() -> dict[str, int]:
    path = PROJECT_ROOT / "data" / "food_database.csv"
    if not path.exists():
        return {
            "rows": 0,
            "unique_food_ids": 0,
            "unique_dedup_signatures": 0,
            "duplicate_dedup_signatures": 0,
            "rows_with_source_ids": 0,
            "rows_with_fdc_ids": 0,
            "rows_with_unmapped_ingredients": 0,
        }
    data = pd.read_csv(
        path,
        usecols=lambda column: column
        in {
            "food_id",
            "dedup_signature",
            "nutrition_source_ids",
            "nutrition_source_fdc_ids",
            "nutrition_source_unmapped_ingredients",
        },
    )
    rows = int(len(data))
    unique_food_ids = int(data.get("food_id", pd.Series(dtype=str)).nunique())
    if "dedup_signature" in data:
        unique_signatures = int(data["dedup_signature"].nunique())
    else:
        unique_signatures = 0
    rows_with_source_ids = int(data.get("nutrition_source_ids", pd.Series(dtype=str)).fillna("").astype(str).str.strip().ne("").sum())
    rows_with_fdc_ids = int(data.get("nutrition_source_fdc_ids", pd.Series(dtype=str)).fillna("").astype(str).str.strip().ne("").sum())
    rows_with_unmapped = int(
        data.get("nutrition_source_unmapped_ingredients", pd.Series(dtype=str)).fillna("").astype(str).str.strip().ne("").sum()
    )
    return {
        "rows": rows,
        "unique_food_ids": unique_food_ids,
        "unique_dedup_signatures": unique_signatures,
        "duplicate_dedup_signatures": max(rows - unique_signatures, 0),
        "rows_with_source_ids": rows_with_source_ids,
        "rows_with_fdc_ids": rows_with_fdc_ids,
        "rows_with_unmapped_ingredients": rows_with_unmapped,
    }


def _safe_text(value: object) -> str:
    return escape(str(value or ""))


def _join_or_default(values, default: str = "None") -> str:
    cleaned = [str(value).strip() for value in values if str(value).strip()]
    return ", ".join(cleaned) if cleaned else default


def section_heading(title: str, detail: str = "") -> None:
    detail_html = f"<p>{_safe_text(detail)}</p>" if detail else ""
    st.markdown(
        f"""
        <div class="section-heading">
          <div>
            <h2>{_safe_text(title)}</h2>
            {detail_html}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_header(result) -> None:
    profile = result.profile
    generation_time = f"{result.generation_time_sec:.2f}"
    safe_count = f"{result.benchmarks.get('safe_records', 0):,}"
    profile_bits = [
        f"{profile.age} years",
        profile.sex,
        f"{profile.calorie_target:,} kcal",
        profile.diet_mode,
    ]
    profile_bits.extend(profile.conditions)
    profile_bits.extend(profile.allergies)
    pill_html = "".join(f'<span class="nutri-pill">{_safe_text(bit)}</span>' for bit in profile_bits if bit)
    st.markdown(
        f"""
        <div class="nutri-hero">
          <div>
            <div class="nutri-eyebrow">Clinical meal planning dashboard</div>
            <h1 class="nutri-title">NutriAI</h1>
            <p class="nutri-subtitle">
              {_safe_text(len(result.days))} days, {_safe_text(len(result.all_meals))} meals,
              {_safe_text(generation_time)} seconds, {_safe_text(safe_count)} safe candidates.
            </p>
          </div>
          <div class="nutri-profile-card">
            <div class="nutri-profile-name">{_safe_text(profile.name)}</div>
            <div class="nutri-pill-row">{pill_html}</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_status_chips(result) -> None:
    label_map = {
        "Clinical Condition Filtering": "Clinical",
        "Allergy Detection & Exclusion": "Allergy",
        "Dietary Preference Handling": "Diet",
        "Diversity Engine": "Diversity",
        "Macro & Micronutrient Analysis": "Nutrients",
        "Sub-60-Second Generation": "Speed",
    }
    chips = []
    for check in result.capability_checks:
        label = label_map.get(check["capability"], check["capability"])
        chips.append(
            f'<div class="status-chip"><strong>{_safe_text(label)}</strong><span>{_safe_text(check["status"])}</span></div>'
        )
    st.markdown(f'<div class="status-grid">{"".join(chips)}</div>', unsafe_allow_html=True)


def profile_form() -> UserProfile:
    st.sidebar.markdown("### Plan inputs")
    persona_names = ["Custom"] + [profile.name for profile in REQUIRED_PERSONAS]
    selected_persona = st.sidebar.selectbox("Profile preset", persona_names, index=0)
    preset = persona_by_name(selected_persona) if selected_persona != "Custom" else None

    default = preset or UserProfile(
        name="Demo User",
        age=29,
        sex="female",
        calorie_target=1900,
        diet_mode="vegetarian",
        allergies=("gluten",),
        conditions=("IBS",),
        micro_priorities=("iron", "calcium", "vitamin d"),
    )

    with st.sidebar.form("profile_form"):
        name = st.text_input("Name", value=default.name)
        age = st.number_input("Age", min_value=2, max_value=100, value=int(default.age), step=1)
        sex = st.selectbox("Sex", ["female", "male"], index=0 if default.sex == "female" else 1)
        calorie_target = st.number_input(
            "Daily calories",
            min_value=900,
            max_value=4200,
            value=int(default.calorie_target),
            step=50,
        )
        diet_modes = ["vegetarian", "vegan", "non-vegetarian", "pescatarian"]
        diet_mode = st.selectbox(
            "Diet mode",
            diet_modes,
            index=diet_modes.index(default.diet_mode) if default.diet_mode in diet_modes else 0,
        )
        allergy_options = ["lactose", "dairy", "gluten", "tree nuts", "peanuts", "shellfish", "soy", "sesame", "eggs"]
        allergies = st.multiselect("Allergies / intolerances", allergy_options, default=list(default.allergies))
        condition_options = ["IBS", "GERD", "type 2 diabetes", "hypertension"]
        conditions = st.multiselect("Clinical conditions", condition_options, default=list(default.conditions))
        cultural_options = ["no pork", "halal", "kosher", "no beef", "no shellfish"]
        cultural_constraints = st.multiselect(
            "Cultural constraints",
            cultural_options,
            default=list(default.cultural_constraints),
        )
        micro_options = ["iron", "calcium", "vitamin b12", "vitamin d", "zinc", "potassium", "magnesium", "omega-3", "fiber"]
        micro_priorities = st.multiselect("Micronutrient priorities", micro_options, default=list(default.micro_priorities))
        meal_preferences = st.text_input("Preference keywords", value=", ".join(default.meal_preferences))
        strict_cross_contamination = st.checkbox("Strict cross-contamination exclusion", value=True)
        submitted = st.form_submit_button("Generate plan", use_container_width=True)

    profile = UserProfile(
        name=name,
        age=int(age),
        sex=sex,
        calorie_target=int(calorie_target),
        diet_mode=diet_mode,
        allergies=tuple(allergies),
        conditions=tuple(conditions),
        cultural_constraints=tuple(cultural_constraints),
        micro_priorities=tuple(micro_priorities),
        meal_preferences=tuple(part.strip() for part in meal_preferences.split(",") if part.strip()),
        strict_cross_contamination=strict_cross_contamination,
    )
    if submitted or "result" not in st.session_state:
        st.session_state["profile"] = profile
        st.session_state["run_generation"] = True
    return profile


def render_metrics(result):
    safe = result.benchmarks.get("safe_records", 0)
    excluded = result.benchmarks.get("excluded_records", 0)
    metrics = [
        ("Generation", f"{result.generation_time_sec:.2f}s", "End-to-end runtime"),
        ("Diversity", f"{result.diversity_score:.1f}/100", "Unique meals and cuisine spread"),
        ("Safe candidates", f"{safe:,}", "Available after hard filters"),
        ("Excluded", f"{excluded:,}", "Removed before ranking"),
    ]
    cards = []
    for label, value, note in metrics:
        cards.append(
            f'<div class="metric-card"><div class="metric-label">{_safe_text(label)}</div><div class="metric-value">{_safe_text(value)}</div><div class="metric-note">{_safe_text(note)}</div></div>'
        )
    st.markdown(f'<div class="metric-grid">{"".join(cards)}</div>', unsafe_allow_html=True)


def render_weekly_macro_mix(plan_df: pd.DataFrame) -> None:
    macro_parts = [
        ("Protein", float(plan_df["protein_g"].sum()), 4.0, "#2f6f62"),
        ("Carbs", float(plan_df["carbs_g"].sum()), 4.0, "#d7a23c"),
        ("Fat", float(plan_df["fat_g"].sum()), 9.0, "#c77c6f"),
    ]
    kcal_values = [grams * kcal_per_gram for _, grams, kcal_per_gram, _ in macro_parts]
    total_macro_kcal = max(sum(kcal_values), 1.0)
    percentages = [value / total_macro_kcal * 100 for value in kcal_values]
    avg_daily_kcal = total_macro_kcal / 7.0

    segment_svgs = []
    offset = 0.0
    for (label, grams, _, color), percent, macro_kcal in zip(macro_parts, percentages, kcal_values):
        tooltip = f"{label}: {percent:.0f}%, {grams / 7.0:.1f} g/day, {macro_kcal / 7.0:.0f} kcal/day"
        segment_svgs.append(
            f'<g class="macro-slice">'
            f'<circle cx="60" cy="60" r="44" pathLength="100" stroke="{color}" '
            f'stroke-dasharray="{percent:.3f} {100 - percent:.3f}" stroke-dashoffset="-{offset:.3f}" '
            f'tabindex="0" focusable="true" role="img" aria-label="{_safe_text(tooltip)}">'
            f'<title>{_safe_text(tooltip)}</title></circle>'
            f'<g class="macro-svg-tooltip">'
            f'<rect x="17" y="35" width="86" height="50" rx="12" fill="#18201f" opacity="0.94"></rect>'
            f'<text x="60" y="52" text-anchor="middle" fill="#ffffff" font-size="8.5" font-weight="800">{_safe_text(label)} {percent:.0f}%</text>'
            f'<text x="60" y="66" text-anchor="middle" fill="#dcebe5" font-size="7.2">{grams / 7.0:.1f} g/day</text>'
            f'<text x="60" y="77" text-anchor="middle" fill="#dcebe5" font-size="7.2">{macro_kcal / 7.0:.0f} kcal/day</text>'
            f'</g></g>'
        )
        offset += percent

    donut_svg = (
        '<svg class="macro-donut-svg" viewBox="0 0 120 120" role="img" aria-label="Interactive weekly macro mix">'
        '<circle cx="60" cy="60" r="44" fill="none" stroke="#e8f0eb" stroke-width="22"></circle>'
        '<circle cx="60" cy="60" r="31" fill="#ffffff" stroke="#d9e5dd" stroke-width="1" pointer-events="none"></circle>'
        f'<text x="60" y="58" text-anchor="middle" fill="#18201f" font-size="15" font-weight="840" pointer-events="none">{avg_daily_kcal:.0f}</text>'
        '<text x="60" y="71" text-anchor="middle" fill="#61716b" font-size="7" font-weight="720" pointer-events="none">kcal/day</text>'
        f'{"".join(segment_svgs)}'
        '</svg>'
    )

    legend_items = []
    for (label, grams, _, color), percent in zip(macro_parts, percentages):
        legend_items.append(
            f'<div class="macro-legend-item">'
            f'<div class="macro-label"><span class="macro-dot" style="background:{color};"></span>{_safe_text(label)}</div>'
            f'<div class="macro-percent">{percent:.0f}%</div>'
            f'<div class="macro-grams">{grams / 7.0:.1f} g/day avg</div>'
            f'</div>'
        )

    legend_html = "".join(legend_items)
    st.markdown(
        (
            '<div class="macro-panel">'
            '<div class="macro-donut-wrap">'
            f'{donut_svg}'
            '<div>'
            '<div class="macro-kicker">Weekly macro mix</div>'
            '<div class="macro-title">Protein, carbs, and fat energy split</div>'
            '<div class="macro-note">Calculated from all 21 selected meals after portion scaling.</div>'
            '</div></div>'
            f'<div class="macro-legend">{legend_html}</div>'
            '</div>'
        ),
        unsafe_allow_html=True,
    )


def render_plan(result):
    plan_df = plan_dataframe(result)
    display = plan_df[
        [
            "day",
            "meal_type",
            "base_name",
            "serving_multiplier",
            "calories",
            "protein_g",
            "carbs_g",
            "fat_g",
            "fiber_g",
        ]
    ].rename(
        columns={
            "day": "Day",
            "meal_type": "Meal",
            "base_name": "Menu item",
            "serving_multiplier": "Serving",
            "calories": "Calories",
            "protein_g": "Protein",
            "carbs_g": "Carbs",
            "fat_g": "Fat",
            "fiber_g": "Fiber",
        }
    )
    numeric_cols = ["Serving", "Calories", "Protein", "Carbs", "Fat", "Fiber"]
    display[numeric_cols] = display[numeric_cols].round(1)
    section_heading("7-day plan", "Twenty-one selected meals with portion scaling and ranking rationale.")
    render_weekly_macro_mix(plan_df)
    st.dataframe(
        display,
        hide_index=True,
        use_container_width=True,
        height=462,
        column_config={
            "Day": st.column_config.NumberColumn("Day", width="small"),
            "Meal": st.column_config.TextColumn("Meal", width="small"),
            "Menu item": st.column_config.TextColumn("Menu item", width="large"),
            "Serving": st.column_config.NumberColumn("Serving", format="%.2f", width="small"),
            "Calories": st.column_config.NumberColumn("Calories", format="%.0f", width="small"),
            "Protein": st.column_config.NumberColumn("Protein", format="%.1f g", width="small"),
            "Carbs": st.column_config.NumberColumn("Carbs", format="%.1f g", width="small"),
            "Fat": st.column_config.NumberColumn("Fat", format="%.1f g", width="small"),
            "Fiber": st.column_config.NumberColumn("Fiber", format="%.1f g", width="small"),
        },
    )
    st.download_button(
        "Download meal plan CSV",
        data=dataframe_to_csv_bytes(plan_df),
        file_name="nutriai_7_day_plan.csv",
        mime="text/csv",
        use_container_width=True,
    )


def render_nutrients(result):
    totals = daily_totals_dataframe(result)
    display = totals.rename(
        columns={
            "day": "Day",
            "calories": "Calories",
            "protein_g": "Protein",
            "carbs_g": "Carbs",
            "fat_g": "Fat",
            "fiber_g": "Fiber",
            "iron_mg": "Iron",
            "calcium_mg": "Calcium",
            "vitamin_b12_mcg": "B12",
            "vitamin_d_mcg": "Vitamin D",
            "zinc_mg": "Zinc",
            "potassium_mg": "Potassium",
            "magnesium_mg": "Magnesium",
            "sodium_mg": "Sodium",
            "omega3_g": "Omega-3",
        }
    )
    for column in display.columns:
        if column != "Day":
            display[column] = display[column].round(1)
    section_heading("Daily nutrient profile", "Macro and micronutrient totals by day.")
    st.dataframe(display, hide_index=True, use_container_width=True, height=260)
    chart_data = totals.set_index("day")[["calories", "protein_g", "fiber_g", "sodium_mg"]]
    st.line_chart(chart_data, use_container_width=True)
    selected_day = st.selectbox("RDA comparison day", [day.day for day in result.days], index=0)
    rda_display = rda_dataframe(result, int(selected_day)).rename(
        columns={
            "nutrient": "Nutrient",
            "actual": "Actual",
            "target": "Target",
            "percent_of_target": "Percent",
            "target_type": "Target type",
            "pass": "Pass",
        }
    )
    section_heading(f"RDA comparison: day {selected_day}")
    st.dataframe(rda_display, hide_index=True, use_container_width=True, height=310)
    warning_rows = []
    for day in result.days:
        for warning in day.warnings:
            warning_rows.append({"day": day.day, "warning": warning})
    if warning_rows:
        warning_display = pd.DataFrame(warning_rows).rename(columns={"day": "Day", "warning": "Warning"})
        st.dataframe(warning_display, hide_index=True, use_container_width=True)


def render_explain(result):
    selected_rows = []
    for meal in result.all_meals:
        selected_rows.append(
            {
                "Day": meal.day,
                "Meal": meal.meal_type,
                "Menu item": meal.base_name,
                "Why selected": meal.why_selected,
                "Ingredients": meal.ingredients,
            }
        )
    section_heading("Selected meal explanations", "Ranking factors for every meal in the current plan.")
    st.dataframe(pd.DataFrame(selected_rows), hide_index=True, use_container_width=True, height=360)
    exclusions = exclusions_dataframe(result).rename(
        columns={
            "food_id": "Food ID",
            "meal_name": "Excluded item",
            "meal_type": "Meal",
            "reasons": "Reason",
        }
    )
    section_heading("Excluded examples", "Safety and clinical filters applied before ranking.")
    st.dataframe(exclusions, hide_index=True, use_container_width=True, height=360)


def render_benchmarks(result):
    section_heading("Capability checks")
    capability = capability_dataframe(result).rename(
        columns={"capability": "Capability", "status": "Status", "evidence": "Evidence"}
    )
    st.dataframe(capability, hide_index=True, use_container_width=True, height=260)
    benchmark_rows = [{"Metric": key.replace("_", " ").title(), "Value": value} for key, value in result.benchmarks.items() if key != "techniques"]
    section_heading("Runtime benchmarks")
    st.dataframe(pd.DataFrame(benchmark_rows), hide_index=True, use_container_width=True, height=270)
    technique_pills = "".join(f'<span class="nutri-pill">{_safe_text(item)}</span>' for item in result.benchmarks.get("techniques", []))
    st.markdown(f'<div class="nutri-pill-row">{technique_pills}</div>', unsafe_allow_html=True)


def render_sources():
    section_heading(
        "Source provenance",
        "Local source-reference files used by the offline planner; no live API call is required while using the app.",
    )
    summary = load_usda_reference_summary()
    food_summary = load_food_database_summary()
    source_metrics = [
        {"Metric": "USDA ingredient reference rows", "Value": f"{summary['rows']:,}"},
        {"Metric": "USDA API matches in cache", "Value": f"{summary['api_matches']:,}"},
        {"Metric": "USDA/source reference coverage rows", "Value": f"{summary['source_reference_rows']:,}"},
        {"Metric": "Offline source-reference rows", "Value": f"{summary['offline_reference_rows']:,}"},
        {"Metric": "Runtime external API calls", "Value": "0"},
        {"Metric": "Meal candidates", "Value": f"{food_summary['rows']:,} deduplicated records"},
        {"Metric": "Meal candidates with source refs", "Value": f"{food_summary['rows_with_source_ids']:,}"},
        {"Metric": "Meal candidates with FDC IDs", "Value": f"{food_summary['rows_with_fdc_ids']:,}"},
        {"Metric": "Meal candidates with unmapped ingredients", "Value": f"{food_summary['rows_with_unmapped_ingredients']:,}"},
        {"Metric": "Unique dedup signatures", "Value": f"{food_summary['unique_dedup_signatures']:,}"},
        {"Metric": "Duplicate dedup signatures", "Value": f"{food_summary['duplicate_dedup_signatures']:,}"},
    ]
    st.dataframe(pd.DataFrame(source_metrics), hide_index=True, use_container_width=True, height=360)

    inventory = load_source_inventory()
    if inventory.empty:
        st.info("Source inventory has not been generated yet. Run scripts/build_source_reference_data.py.")
        return

    display = inventory.rename(
        columns={
            "source_name": "Source",
            "url": "URL",
            "local_file": "Local file",
            "used_for": "Used for",
            "incorporation_type": "Incorporation",
            "runtime_requirement": "Runtime",
            "caveat": "Caveat",
        }
    )
    st.dataframe(display, hide_index=True, use_container_width=True, height=360)


def render_persona_tests(planner: NutriAIPlanner):
    section_heading("Required persona checks")
    if st.button("Run required persona tests", use_container_width=True):
        rows = []
        for persona in REQUIRED_PERSONAS:
            result = planner.generate_plan(persona)
            statuses = {item["capability"]: item["status"] for item in result.capability_checks}
            rows.append(
                {
                    "persona": persona.name,
                    "generation_sec": result.generation_time_sec,
                    "diversity_score": result.diversity_score,
                    **statuses,
                }
            )
        st.session_state["persona_test_rows"] = rows
    if "persona_test_rows" in st.session_state:
        display = pd.DataFrame(st.session_state["persona_test_rows"]).rename(
            columns={
                "persona": "Persona",
                "generation_sec": "Generation",
                "diversity_score": "Diversity",
            }
        )
        st.dataframe(display, hide_index=True, use_container_width=True)


def main():
    inject_design_system()
    profile = profile_form()
    planner = load_planner()

    if st.session_state.get("run_generation"):
        with st.spinner("Generating clinically filtered plan"):
            st.session_state["result"] = planner.generate_plan(st.session_state.get("profile", profile))
        st.session_state["run_generation"] = False

    result = st.session_state.get("result")
    if result is None:
        result = planner.generate_plan(profile)
        st.session_state["result"] = result

    render_header(result)
    render_metrics(result)
    render_status_chips(result)

    tabs = st.tabs(["Plan", "Nutrients", "Explain", "Benchmarks", "Sources", "Personas"])
    with tabs[0]:
        render_plan(result)
    with tabs[1]:
        render_nutrients(result)
    with tabs[2]:
        render_explain(result)
    with tabs[3]:
        render_benchmarks(result)
    with tabs[4]:
        render_sources()
    with tabs[5]:
        render_persona_tests(planner)


if __name__ == "__main__":
    main()
