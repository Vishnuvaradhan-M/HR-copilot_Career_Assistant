"""
HR Copilot - Unified System
Career Learning Assistant + HR Policy Chat

Both systems run independently but within the same Streamlit interface.
Navigation via sidebar to switch between Career Setup and HR Policy Assistant.
"""

import streamlit as st
from typing import Optional
import json
from datetime import datetime
import plotly.graph_objects as go

# Career exports
from app.career_assistant import (
    normalize_role,
    analyze_skill_gaps,
    generate_learning_timeline,
)
from app.schemas.career import (
    UserProfile,
    CareerGoal,
    Skill,
    ProficiencyLevel,
    NormalizedRole,
    SkillGapAnalysis,
    CareerLearningPlan,
)

# HR Policy exports
from app.hr_policy_chat import query_hr_policy, format_confidence, format_evidence_chunk

# Learning resources
from app.prompts.career_prompts import SKILL_RESOURCES

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="HR Copilot - Career & Policy Assistant",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
/* Base */
.stApp { background-color: #0f1117 !important; }
section[data-testid="stSidebar"] { 
  background: #161b27 !important; 
  border-right: 1px solid #1e2d45 !important; 
}

/* All text inputs, selectboxes, sliders */
.stTextInput > div > div > input,
.stSelectbox > div > div,
.stTextArea textarea,
.stNumberInput input {
  background: #0f1117 !important;
  border: 1px solid #1e2d45 !important;
  border-radius: 8px !important;
  color: #c8d4f0 !important;
  font-size: 13px !important;
}
.stTextInput > div > div > input:focus,
.stTextArea textarea:focus {
  border-color: #4f8ef7 !important;
  box-shadow: 0 0 0 2px rgba(79,142,247,0.15) !important;
}

/* Buttons */
.stButton > button {
  background: #4f8ef7 !important;
  color: white !important;
  border: none !important;
  border-radius: 8px !important;
  font-weight: 600 !important;
  font-size: 14px !important;
  padding: 10px 22px !important;
  transition: background 0.15s !important;
}
.stButton > button:hover { background: #3a7de8 !important; }

/* Secondary button — add class manually via st.markdown wrapper */
.btn-secondary > button {
  background: transparent !important;
  color: #6b7a99 !important;
  border: 1px solid #1e2d45 !important;
}

/* Labels */
.stTextInput label, .stSelectbox label, .stSlider label,
.stNumberInput label, .stTextArea label {
  color: #6b7a99 !important;
  font-size: 11px !important;
  font-weight: 600 !important;
  text-transform: uppercase !important;
  letter-spacing: 0.7px !important;
}

/* Slider */
.stSlider > div > div > div { 
  background: #4f8ef7 !important; 
}

/* Expanders (used for phases) */
.streamlit-expanderHeader {
  background: #161b27 !important;
  border: 1px solid #1e2d45 !important;
  border-radius: 10px !important;
  color: #f0f4ff !important;
  font-weight: 600 !important;
  font-size: 14px !important;
}
.streamlit-expanderContent {
  background: #161b27 !important;
  border: 1px solid #1e2d45 !important;
  border-top: none !important;
  border-radius: 0 0 10px 10px !important;
}

/* Metrics */
[data-testid="metric-container"] {
  background: #0f1117 !important;
  border: 1px solid #1e2d45 !important;
  border-radius: 10px !important;
  padding: 14px !important;
}
[data-testid="stMetricLabel"] { 
  color: #6b7a99 !important; 
  font-size: 11px !important; 
  text-transform: uppercase !important;
  letter-spacing: 0.7px !important;
}
[data-testid="stMetricValue"] { 
  color: #f0f4ff !important; 
  font-size: 26px !important; 
  font-weight: 700 !important; 
}

/* Info / success / warning / error boxes */
.stAlert { border-radius: 10px !important; border: none !important; }
[data-testid="stInfo"] { 
  background: rgba(79,142,247,0.08) !important; 
  border-left: 3px solid #4f8ef7 !important; 
  color: #8ab4f8 !important; 
}
[data-testid="stSuccess"] { 
  background: rgba(82,183,136,0.08) !important; 
  border-left: 3px solid #52b788 !important; 
}
[data-testid="stWarning"] { 
  background: rgba(239,159,39,0.08) !important; 
  border-left: 3px solid #ef9f27 !important; 
}
[data-testid="stError"] { 
  background: rgba(224,82,82,0.08) !important; 
  border-left: 3px solid #e05252 !important; 
}

/* Divider */
hr { border-color: #1e2d45 !important; }

/* Sidebar nav items */
.css-17lntkn { color: #8a9bb8 !important; }

/* Progress bars */
.stProgress > div > div { 
  background: #4f8ef7 !important; 
  border-radius: 4px !important; 
}
.stProgress > div { 
  background: #1e2d45 !important; 
  border-radius: 4px !important; 
}

/* Download button */
.stDownloadButton > button {
  background: #161b27 !important;
  color: #4f8ef7 !important;
  border: 1px solid #4f8ef7 !important;
  border-radius: 8px !important;
  font-weight: 600 !important;
}
.stDownloadButton > button:hover {
  background: rgba(79,142,247,0.12) !important;
}
</style>
""", unsafe_allow_html=True)

# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

def init_session_state():
    """Initialize all session state keys."""
    
    # Main system state
    if "system_tab" not in st.session_state:
        st.session_state.system_tab = "Career Setup"
    
    # ===== CAREER STATE =====
    if "career_step" not in st.session_state:
        st.session_state.career_step = 1
    
    if "career_profile" not in st.session_state:
        st.session_state.career_profile = None
    
    if "career_skills" not in st.session_state:
        st.session_state.career_skills = []
    
    if "normalized_current" not in st.session_state:
        st.session_state.normalized_current = None
    
    if "normalized_target" not in st.session_state:
        st.session_state.normalized_target = None
    
    if "gap_analysis" not in st.session_state:
        st.session_state.gap_analysis = None
    
    if "learning_plan" not in st.session_state:
        st.session_state.learning_plan = None
    
    # ===== HR POLICY STATE =====
    if "hr_chat_history" not in st.session_state:
        st.session_state.hr_chat_history = []

init_session_state()


# ============================================================================
# HELPER FUNCTIONS - CAREER
# ============================================================================

def go_to_career_step(step: int):
    """Navigate to specified career step."""
    st.session_state.career_step = step
    st.rerun()


def clear_career_state():
    """Clear all career-related session state."""
    st.session_state.career_step = 1
    st.session_state.career_profile = None
    st.session_state.career_skills = []
    st.session_state.normalized_current = None
    st.session_state.normalized_target = None
    st.session_state.gap_analysis = None
    st.session_state.learning_plan = None


def normalize_role_safe(role_string: str, current_role: str = None, years_exp: float = 0) -> Optional[NormalizedRole]:
    """Safely normalize a role string with error handling."""
    try:
        result = normalize_role(role_string, current_role, years_exp)
        return result
    except Exception as e:
        st.error(f"⚠️ Error normalizing role '{role_string}': {str(e)}")
        return None


def analyze_gaps_safe(user_profile: UserProfile, target_role: str) -> Optional[SkillGapAnalysis]:
    """Safely analyze skill gaps with error handling."""
    try:
        result = analyze_skill_gaps(user_profile, target_role)
        return result
    except Exception as e:
        st.error(f"⚠️ Error analyzing skill gaps: {str(e)}")
        return None


def generate_timeline_safe(gap_analysis: SkillGapAnalysis, user_profile: UserProfile) -> Optional[CareerLearningPlan]:
    """Safely generate learning timeline with error handling."""
    try:
        result = generate_learning_timeline(gap_analysis, user_profile)
        return result
    except Exception as e:
        st.error(f"⚠️ Error generating timeline: {str(e)}")
        return None


# ============================================================================
# UI HELPER FUNCTIONS
# ============================================================================

def page_header(badge_text: str, title: str, subtitle: str):
    """Render a styled page header with badge, title, and subtitle."""
    st.markdown(f"""
    <div style="margin-bottom:28px;">
      <div style="display:inline-flex;align-items:center;gap:6px;
        background:rgba(79,142,247,0.1);border:1px solid rgba(79,142,247,0.2);
        padding:4px 12px;border-radius:20px;font-size:11px;color:#4f8ef7;
        margin-bottom:10px;text-transform:uppercase;letter-spacing:0.7px;">{badge_text}</div>
      <h1 style="font-size:28px;font-weight:700;color:#f0f4ff;
        letter-spacing:-0.5px;margin:0;">{title}</h1>
      <p style="font-size:14px;color:#8a9bb8;margin:6px 0 0;font-weight:500;">{subtitle}</p>
    </div>
    """, unsafe_allow_html=True)


def card(title: str = "", content: str = ""):
    """Render a styled card container."""
    title_html = f"""<div style='font-size:10px;font-weight:600;text-transform:uppercase;
                              letter-spacing:0.8px;color:#3d4f6e;margin-bottom:14px;'>{title}</div>""" if title else ""
    
    st.markdown(f"""
    <div style="background:#161b27;border:1px solid #1e2d45;
      border-radius:12px;padding:20px;margin-bottom:14px;">
      {title_html}
      {content}
    </div>
    """, unsafe_allow_html=True)


def render_severity_cards(critical: int, high: int, medium: int, low: int):
    """Render colored severity indicator cards."""
    st.markdown(f"""
    <div style="display:flex;gap:10px;margin-bottom:16px;flex-wrap:wrap;">
      <div style="flex:1;min-width:120px;background:rgba(224,82,82,0.12);
        border:1px solid rgba(224,82,82,0.25);border-radius:10px;
        padding:14px;text-align:center;">
        <div style="font-size:26px;font-weight:700;color:#e05252;">{critical}</div>
        <div style="font-size:10px;color:#8a9bb8;text-transform:uppercase;
          letter-spacing:0.5px;margin-top:3px;font-weight:600;">Critical</div>
      </div>
      <div style="flex:1;min-width:120px;background:rgba(239,159,39,0.12);
        border:1px solid rgba(239,159,39,0.25);border-radius:10px;
        padding:14px;text-align:center;">
        <div style="font-size:26px;font-weight:700;color:#ef9f27;">{high}</div>
        <div style="font-size:10px;color:#8a9bb8;text-transform:uppercase;
          letter-spacing:0.5px;margin-top:3px;font-weight:600;">High</div>
      </div>
      <div style="flex:1;min-width:120px;background:rgba(79,142,247,0.10);
        border:1px solid rgba(79,142,247,0.20);border-radius:10px;
        padding:14px;text-align:center;">
        <div style="font-size:26px;font-weight:700;color:#4f8ef7;">{medium}</div>
        <div style="font-size:10px;color:#8a9bb8;text-transform:uppercase;
          letter-spacing:0.5px;margin-top:3px;font-weight:600;">Medium</div>
      </div>
      <div style="flex:1;min-width:120px;background:rgba(82,183,136,0.10);
        border:1px solid rgba(82,183,136,0.20);border-radius:10px;
        padding:14px;text-align:center;">
        <div style="font-size:26px;font-weight:700;color:#52b788;">{low}</div>
        <div style="font-size:10px;color:#8a9bb8;text-transform:uppercase;
          letter-spacing:0.5px;margin-top:3px;font-weight:600;">Low</div>
      </div>
    </div>
    """, unsafe_allow_html=True)


def render_skill_table(gaps):
    """Render an HTML-styled skill table."""
    rows = ""
    for gap in gaps:
        status_map = {
            "missing": ('<span style="background:rgba(224,82,82,0.1);'
                       'color:#e05252;border:1px solid rgba(224,82,82,0.2);'
                       'padding:4px 10px;border-radius:20px;font-size:10px;'
                       'font-weight:600;">Missing</span>'),
            "partial": ('<span style="background:rgba(239,159,39,0.1);'
                       'color:#ef9f27;border:1px solid rgba(239,159,39,0.2);'
                       'padding:4px 10px;border-radius:20px;font-size:10px;'
                       'font-weight:600;">Partial</span>'),
            "met":     ('<span style="background:rgba(82,183,136,0.1);'
                       'color:#52b788;border:1px solid rgba(82,183,136,0.2);'
                       'padding:4px 10px;border-radius:20px;font-size:10px;'
                       'font-weight:600;">Met</span>')
        }
        status = status_map.get(gap.status.lower(), "") if hasattr(gap, 'status') else ""
        skill_name = gap.skill_name if hasattr(gap, 'skill_name') else gap.name
        required_level = gap.required_level.value if hasattr(gap.required_level, 'value') else str(gap.required_level)
        user_level = gap.user_level if hasattr(gap, 'user_level') else 'N/A'
        
        rows += f"""<div style="display:grid;grid-template-columns:2fr 1.2fr 1.2fr 1fr;
          padding:10px 14px;border-bottom:1px solid #1e2d45;
          align-items:center;font-size:13px;">
          <span style="color:#c8d4f0;font-weight:500;">{skill_name}</span>
          <span style="color:#8a9bb8;">{required_level}</span>
          <span style="color:#8a9bb8;">{user_level or '—'}</span>
          <div>{status}</div>
        </div>"""
    
    st.markdown(f"""
    <div style="background:#161b27;border:1px solid #1e2d45;
      border-radius:12px;overflow:hidden;margin-bottom:16px;">
      <div style="display:grid;grid-template-columns:2fr 1.2fr 1.2fr 1fr;
        padding:10px 14px;font-size:10px;text-transform:uppercase;
        letter-spacing:0.8px;color:#6b7a99;background:#0f1117;font-weight:600;">
        <span>Skill</span><span>Required</span>
        <span>Your Level</span><span>Status</span>
      </div>
      {rows}
    </div>
    """, unsafe_allow_html=True)


def render_feasibility_banner(feasibility_label: str, hours_per_week: float, total_weeks: int):
    """Render a colored feasibility status banner."""
    feasibility_colors = {
        "Achievable": ("rgba(82,183,136,0.08)", "rgba(82,183,136,0.2)", "#52b788"),
        "Moderate commitment": ("rgba(239,159,39,0.08)", "rgba(239,159,39,0.2)", "#ef9f27"),
        "Long-term plan": ("rgba(79,142,247,0.08)", "rgba(79,142,247,0.2)", "#4f8ef7"),
        "Extended journey": ("rgba(224,82,82,0.08)", "rgba(224,82,82,0.2)", "#e05252"),
    }
    bg, border, color = feasibility_colors.get(feasibility_label, 
                        feasibility_colors["Long-term plan"])
    st.markdown(f"""
    <div style="background:{bg};border:1px solid {border};
      border-radius:10px;padding:12px 16px;font-size:13px;
      color:{color};margin-bottom:16px;font-weight:500;">
      <strong>{feasibility_label}</strong> — at {hours_per_week}h/week, 
      this plan completes in approximately {total_weeks} weeks
    </div>
    """, unsafe_allow_html=True)


# ============================================================================
# CAREER PAGES
# ============================================================================

def page_career_onboarding():
    """Career Step 1: Onboarding."""
    page_header(
        badge_text="Step 1 of 3 · Profile",
        title="Career Setup",
        subtitle="Tell us where you are and where you want to go"
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div style='font-size:13px;font-weight:600;color:#f0f4ff;margin-bottom:16px;text-transform:uppercase;letter-spacing:0.5px;'>
        📍 Your Current Situation
        </div>
        """, unsafe_allow_html=True)
        name = st.text_input("Your Name", value="", key="onboard_name")
        current_role = st.text_input("Current Role", placeholder="e.g., Junior Developer", key="onboard_current")
        years_in_role = st.number_input("Years in Current Role", min_value=0.0, max_value=50.0, value=2.0, step=0.5, key="onboard_years_in")
        total_years = st.number_input("Total Years of Experience", min_value=0.0, max_value=50.0, value=5.0, step=0.5, key="onboard_total_years")
        hours_available = st.number_input("Hours per Week Available for Learning", min_value=1.0, max_value=50.0, value=5.0, step=0.5, key="onboard_hours")
    
    with col2:
        st.markdown("""
        <div style='font-size:13px;font-weight:600;color:#f0f4ff;margin-bottom:16px;text-transform:uppercase;letter-spacing:0.5px;'>
        🎯 Your Career Goal
        </div>
        """, unsafe_allow_html=True)
        target_role = st.text_input("Target Role", placeholder="e.g., Senior Developer", key="onboard_target")
        reason = st.text_area("Why this transition? (optional)", placeholder="e.g., Want to lead a team...", key="onboard_reason")
        timeline = st.number_input("Desired Timeline (months)", min_value=1, max_value=60, value=12, step=1, key="onboard_timeline")
        learning_style = st.selectbox(
            "Your Learning Style",
            ["balanced", "visual", "hands-on", "theoretical"],
            key="onboard_style"
        )
    
    st.divider()
    
    st.markdown("""
    <div style='font-size:13px;font-weight:600;color:#f0f4ff;margin-bottom:16px;text-transform:uppercase;letter-spacing:0.5px;'>
    💼 Your Current Skills
    </div>
    <div style='color:#8a9bb8;font-size:12px;margin-bottom:16px;'>
    List skills you already have with proficiency level.
    </div>
    """, unsafe_allow_html=True)
    
    num_skills = st.number_input("Number of skills to add", min_value=1, max_value=10, value=3, key="onboard_num_skills")
    
    skills_input = []
    for i in range(int(num_skills)):
        skill_col, level_col = st.columns([2, 1])
        with skill_col:
            skill_name = st.text_input(f"Skill {i+1}", key=f"skill_name_{i}")
        with level_col:
            skill_level = st.selectbox(
                "Level",
                ["beginner", "intermediate", "advanced", "expert"],
                key=f"skill_level_{i}",
                label_visibility="collapsed"
            )
        if skill_name:
            skills_input.append({"name": skill_name, "level": skill_level})
    
    st.divider()
    
    if st.button("Next: Analyze Skill Gaps →", use_container_width=True, type="primary"):
        if not name or not current_role or not target_role or not skills_input:
            st.error("⚠️ Please fill in all required fields.")
            return
        
        skill_objects = []
        for skill_input in skills_input:
            proficiency = ProficiencyLevel(skill_input["level"])
            skill_objects.append(Skill(name=skill_input["name"], proficiency=proficiency))
        
        profile = UserProfile(
            name=name,
            current_role=current_role,
            years_in_role=years_in_role,
            total_experience_years=total_years,
            current_skills=skill_objects,
            hours_per_week_available=hours_available,
            learning_style=learning_style,
        )
        
        st.session_state.career_profile = profile
        st.session_state.career_skills = skills_input
        
        norm_current = normalize_role_safe(current_role, None, total_years)
        norm_target = normalize_role_safe(target_role, current_role, total_years)
        
        if norm_current and norm_target:
            st.session_state.normalized_current = norm_current
            st.session_state.normalized_target = norm_target
            go_to_career_step(2)
        else:
            st.error("⚠️ Could not normalize one or both roles.")


def page_career_gaps():
    """Career Step 2: Skill Gap Analysis."""
    
    if not st.session_state.career_profile or not st.session_state.normalized_current:
        st.warning("⚠️ Please complete the onboarding first.")
        if st.button("← Back to Start"):
            go_to_career_step(1)
        return
    
    profile = st.session_state.career_profile
    norm_current = st.session_state.normalized_current
    norm_target = st.session_state.normalized_target
    
    page_header(
        badge_text="Step 2 of 3 · Gap Analysis",
        title="Skill Gap Analysis",
        subtitle=f"{norm_current.normalized_name} → {norm_target.normalized_name}"
    )
    
    if st.session_state.gap_analysis is None:
        with st.spinner("Analyzing your skill gaps..."):
            gap_analysis = analyze_gaps_safe(profile, norm_target.normalized_name)
            if gap_analysis:
                st.session_state.gap_analysis = gap_analysis
            else:
                st.error("⚠️ Failed to analyze skill gaps.")
                if st.button("← Try Again"):
                    go_to_career_step(1)
                return
    
    gap_analysis = st.session_state.gap_analysis
    
    # ========== VISUAL A: READINESS GAUGE ==========
    skills_met = len(profile.current_skills)
    total_required = gap_analysis.total_required_skills
    readiness_pct = (skills_met / total_required * 100) if total_required > 0 else 0
    
    fig_gauge = go.Figure(data=[go.Indicator(
        mode="gauge+number+delta",
        value=readiness_pct,
        domain={"x": [0, 1], "y": [0, 1]},
        title={"text": f"Overall Readiness for {norm_target.normalized_name}", "font": {"size": 16, "color": "#ffffff"}},
        delta={"reference": 50, "increasing": {"color": "#2ecc71"}, "decreasing": {"color": "#e74c3c"}},
        number={"font": {"size": 28, "color": "#ffffff"}},
        gauge={
            "axis": {"range": [0, 100], "tickcolor": "#ffffff", "tickfont": {"color": "#ffffff"}},
            "bar": {"color": "#3498db"},
            "steps": [
                {"range": [0, 33], "color": "rgba(220, 53, 69, 0.3)"},
                {"range": [33, 66], "color": "rgba(255, 193, 7, 0.3)"},
                {"range": [66, 100], "color": "rgba(46, 204, 113, 0.3)"}
            ],
            "threshold": {
                "line": {"color": "#e74c3c", "width": 3},
                "thickness": 0.75,
                "value": 90
            }
        }
    )])
    fig_gauge.update_layout(
        height=320, 
        margin=dict(l=20, r=20, t=80, b=20),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color="#ffffff", size=12)
    )
    st.plotly_chart(fig_gauge, use_container_width=True)
    
    st.divider()
    
    # Severity cards
    st.markdown("<div style='font-size:11px;font-weight:600;color:#6b7a99;text-transform:uppercase;letter-spacing:0.7px;margin-bottom:16px;'>Gap Severity Breakdown</div>", unsafe_allow_html=True)
    render_severity_cards(
        critical=gap_analysis.gaps_by_severity.get("critical", 0),
        high=gap_analysis.gaps_by_severity.get("high", 0),
        medium=gap_analysis.gaps_by_severity.get("medium", 0),
        low=gap_analysis.gaps_by_severity.get("low", 0)
    )
    
    st.divider()
    
    # ========== VISUAL B: GAP SEVERITY BAR CHART ==========
    severity_order = ["critical", "high", "medium", "low"]
    severity_labels = ["Critical", "High", "Medium", "Low"]
    severity_colors = ["#ff4b4b", "#ff8c00", "#ffd700", "#2ecc71"]
    severity_counts_list = [gap_analysis.gaps_by_severity.get(sev, 0) for sev in severity_order]
    
    fig_bar = go.Figure(data=[go.Bar(
        y=severity_labels,
        x=severity_counts_list,
        orientation='h',
        marker=dict(color=severity_colors, line=dict(color="rgba(255,255,255,0.3)", width=1)),
        text=severity_counts_list,
        textposition='outside',
        textfont=dict(color="#ffffff", size=12),
        hovertemplate='<b>%{y}</b><br>Count: %{x}<extra></extra>'
    )])
    fig_bar.update_layout(
        title=dict(text="Skill Gaps by Severity", font=dict(size=16, color="#ffffff")),
        xaxis_title=dict(text="Number of Skills", font=dict(color="#ffffff")),
        yaxis_title="",
        height=280,
        margin=dict(l=30, r=30, t=60, b=30),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=True, gridwidth=1, gridcolor="rgba(255,255,255,0.1)", zeroline=False, tickfont=dict(color="#ffffff")),
        yaxis=dict(showgrid=False, tickfont=dict(color="#ffffff")),
        hovermode='closest'
    )
    st.plotly_chart(fig_bar, use_container_width=True)
    
    st.divider()
    
    # Skill breakdown
    st.markdown("<div style='font-size:11px;font-weight:600;color:#6b7a99;text-transform:uppercase;letter-spacing:0.7px;margin-bottom:16px;'>Skill-by-Skill Breakdown</div>", unsafe_allow_html=True)
    col_skill, col_req, col_current, col_status = st.columns([2, 1.5, 1.5, 1.5])
    
    with col_skill:
        st.write("**Skill**")
    with col_req:
        st.write("**Required**")
    with col_current:
        st.write("**Your Level**")
    with col_status:
        st.write("**Status**")
    
    st.divider()
    
    for gap in gap_analysis.all_gaps:
        col_skill, col_req, col_current, col_status = st.columns([2, 1.5, 1.5, 1.5])
        
        with col_skill:
            st.write(f"**{gap.skill_name}**")
        
        with col_req:
            st.write(gap.required_level.value)
        
        with col_current:
            st.write(gap.current_level.value)
        
        with col_status:
            if gap.gap_severity == "critical":
                st.markdown('<span class="badge badge-critical">🔴 Missing</span>', unsafe_allow_html=True)
            elif gap.gap_severity == "high":
                st.markdown('<span class="badge badge-high">🟡 Upgrade</span>', unsafe_allow_html=True)
            elif gap.gap_severity == "medium":
                st.markdown('<span class="badge badge-medium">🟢 Build</span>', unsafe_allow_html=True)
            else:
                st.markdown('<span class="badge badge-low">🟢 Optional</span>', unsafe_allow_html=True)
        
        st.divider()
    
    # Navigation
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("← Back to Start", use_container_width=True):
            go_to_career_step(1)
    
    with col2:
        if st.button("Generate My Learning Plan →", use_container_width=True, type="primary"):
            go_to_career_step(3)


def page_career_timeline():
    """Career Step 3: Learning Timeline."""
    
    if not st.session_state.gap_analysis:
        st.warning("⚠️ Please complete skill gap analysis first.")
        if st.button("← Back to Gaps"):
            go_to_career_step(2)
        return
    
    profile = st.session_state.career_profile
    gap_analysis = st.session_state.gap_analysis
    norm_target = st.session_state.normalized_target
    
    page_header(
        badge_text="Step 3 of 3 · Learning Plan",
        title="Your Learning Roadmap",
        subtitle=f"Personalized path to {norm_target.normalized_name}"
    )
    
    if st.session_state.learning_plan is None:
        with st.spinner("Building your learning roadmap..."):
            learning_plan = generate_timeline_safe(gap_analysis, profile)
            if learning_plan:
                st.session_state.learning_plan = learning_plan
            else:
                st.error("⚠️ Failed to generate learning timeline.")
                if st.button("← Try Again"):
                    go_to_career_step(2)
                return
    
    learning_plan = st.session_state.learning_plan
    
    # Summary
    hours_per_week = profile.hours_per_week_available
    weeks_needed = learning_plan.total_weeks_recommended
    months_needed = weeks_needed / 4.3
    feasibility = learning_plan.feasibility_rating
    
    render_feasibility_banner(feasibility, hours_per_week, int(weeks_needed))
    st.divider()
    
    # ========== VISUALIZATIONS: TIMELINE & EFFORT ==========
    col_gantt, col_pie = st.columns([2, 1])
    
    # VISUAL C: Phase Timeline Gantt
    with col_gantt:
        phases_data = []
        phase_colors = {"foundation": "#3498db", "core": "#e67e22", "advanced": "#9b59b6"}
        
        for phase in learning_plan.phases:
            color = phase_colors.get(phase.phase_name.lower(), "#95a5a6")
            phases_data.append(go.Bar(
                x=[phase.recommended_weeks],
                y=[phase.phase_name],
                orientation='h',
                name=phase.phase_name,
                marker=dict(color=color, line=dict(color="rgba(255,255,255,0.5)", width=2)),
                text=f"{int(phase.recommended_weeks)}w",
                textposition='inside',
                textfont=dict(color='white', size=13, family="Arial Black"),
                hovertemplate=f"<b>{phase.phase_name}</b><br>Duration: {int(phase.recommended_weeks)} weeks<extra></extra>"
            ))
        
        fig_gantt = go.Figure(data=phases_data)
        fig_gantt.update_layout(
            title=dict(text="Learning Roadmap Timeline", font=dict(size=16, color="#ffffff")),
            xaxis_title=dict(text="Weeks", font=dict(color="#ffffff")),
            yaxis_title="",
            barmode='stack',
            height=300,
            margin=dict(l=30, r=30, t=60, b=30),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(showgrid=True, gridwidth=1, gridcolor="rgba(255,255,255,0.1)", zeroline=False, tickfont=dict(color="#ffffff")),
            yaxis=dict(showgrid=False, tickfont=dict(color="#ffffff", size=12), automargin=True),
            showlegend=False,
            hovermode='closest'
        )
        st.plotly_chart(fig_gantt, use_container_width=True)
    
    # VISUAL D: Hours Distribution Pie Chart
    with col_pie:
        phase_hours = []
        phase_labels = []
        phase_colors_pie = []
        phase_color_map = {"foundation": "#3498db", "core": "#e67e22", "advanced": "#9b59b6"}
        
        for phase in learning_plan.phases:
            phase_hours.append(phase.total_hours)
            phase_labels.append(f"{phase.phase_name}")
            phase_colors_pie.append(phase_color_map.get(phase.phase_name.lower(), "#95a5a6"))
        
        fig_pie = go.Figure(data=[go.Pie(
            labels=phase_labels,
            values=phase_hours,
            marker=dict(colors=phase_colors_pie, line=dict(color="rgba(255,255,255,0.3)", width=2)),
            textinfo='label+percent',
            textfont=dict(color="#ffffff", size=11),
            hovertemplate='<b>%{label}</b><br>Hours: %{value}<br>%{percent}<extra></extra>',
            textposition='inside'
        )])
        fig_pie.update_layout(
            title=dict(text="Effort Distribution", font=dict(size=16, color="#ffffff")),
            height=300,
            margin=dict(l=20, r=20, t=60, b=20),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color="#ffffff", size=11),
            showlegend=True,
            legend=dict(font=dict(color="#ffffff"))
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    
    st.divider()
    
    # Learning phases
    st.markdown("<div style='font-size:13px;font-weight:600;color:#f0f4ff;margin-bottom:16px;text-transform:uppercase;letter-spacing:0.5px;'>📚 Learning Phases</div>", unsafe_allow_html=True)
    
    for phase_idx, phase in enumerate(learning_plan.phases, 1):
        with st.expander(f"Phase {phase_idx}: {phase.phase_name} - {int(phase.recommended_weeks)} weeks", expanded=(phase_idx == 1)):
            
            progress_text = f"{phase.critical_task_count} critical · {phase.nice_to_have_count} nice-to-have" if phase.critical_task_count > 0 else f"{phase.nice_to_have_count} tasks"
            st.write(f"**Tasks:** {progress_text}")
            st.write(f"**Total Effort:** {phase.total_hours} hours")
            st.write(f"**Recommended Pace:** {phase.recommended_weeks} weeks")
            
            st.divider()
            st.write("**Learning Tasks:**")
            
            for task in phase.tasks:
                col_1, col_2, col_3, col_4 = st.columns([2, 1, 1, 1])
                
                with col_1:
                    st.write(f"**{task.skill_name}**")
                
                with col_2:
                    st.write(f"{task.estimated_hours}h")
                
                with col_3:
                    if task.must_complete:
                        st.markdown('<span class="badge badge-critical">Critical</span>', unsafe_allow_html=True)
                    else:
                        st.markdown('<span class="badge badge-low">Optional</span>', unsafe_allow_html=True)
                
                with col_4:
                    st.write(f"{task.difficulty}")
                
                # Look up and display resources for this skill
                skill_name_lower = task.skill_name.lower()
                resources_found = None
                
                for skill_key in SKILL_RESOURCES.keys():
                    if skill_key.lower() == skill_name_lower:
                        resources_found = SKILL_RESOURCES[skill_key]
                        break
                
                if resources_found:
                    resource_links = []
                    for resource in resources_found:
                        emoji = "🎓" if resource["type"] == "course" else "📖" if resource["type"] == "book" else "💻"
                        resource_links.append(f"{emoji} [{resource['name']}]({resource['url']})")
                    
                    st.caption(" · ".join(resource_links))
                
                st.divider()
            
            if phase.key_milestones:
                st.write("**Milestones:**")
                for milestone in phase.key_milestones:
                    st.write(f"✓ {milestone}")
    
    st.divider()
    
    # Key actions
    st.markdown("<div style='font-size:13px;font-weight:600;color:#f0f4ff;margin-bottom:16px;text-transform:uppercase;letter-spacing:0.5px;'>🎯 Next Steps</div>", unsafe_allow_html=True)
    for idx, action in enumerate(learning_plan.key_actions, 1):
        st.write(f"{idx}. {action}")
    
    st.divider()
    
    # Download - try PDF first, fallback to TXT
    pdf_bytes = generate_pdf(profile, gap_analysis, learning_plan)
    
    if pdf_bytes:
        st.download_button(
            label="📄 Download Learning Plan (PDF)",
            data=pdf_bytes,
            file_name="career_learning_plan.pdf",
            mime="application/pdf",
            use_container_width=True
        )
    else:
        # Fallback to .txt if PDF generation failed
        plan_text = _generate_plan_text(profile, gap_analysis, learning_plan)
        st.download_button(
            label="📄 Download Learning Plan (.txt)",
            data=plan_text,
            file_name="career_learning_plan.txt",
            mime="text/plain",
            use_container_width=True
        )
    
    st.divider()
    
    # Navigation
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("← Back to Gaps", use_container_width=True):
            go_to_career_step(2)
    
    with col2:
        if st.button("Review Gaps", use_container_width=True):
            go_to_career_step(2)
    
    with col3:
        if st.button("Start Over →", use_container_width=True, type="primary"):
            clear_career_state()
            st.rerun()


# ============================================================================
# PDF EXPORT
# ============================================================================

def generate_pdf(profile: UserProfile, gap_analysis: SkillGapAnalysis, learning_plan: CareerLearningPlan) -> Optional[bytes]:
    """
    Generate a professional, visually rich PDF export of the career learning plan.
    
    Returns bytes of the PDF file, or None if generation fails.
    """
    try:
        from fpdf import FPDF
        
        # ===== BUG 3: Normalize target role at start =====
        raw_target = learning_plan.target_role \
            if hasattr(learning_plan, 'target_role') \
            else gap_analysis.target_role
        
        if hasattr(raw_target, 'name'):
            target_display = raw_target.name.replace("_", " ").title()
        else:
            target_display = str(raw_target).replace("_", " ").title()
        
        # ===== SAFETY HELPER =====
        def skill_str(val):
            """Convert skill value to safe string, handling Skill objects."""
            if hasattr(val, 'name'):
                return str(val.name)
            return str(val)
        
        # Helper methods
        def _draw_header_band(pdf, title, right_text, bg_color_rgb, y_start=0):
            """Draw a colored header band with optional right-aligned text."""
            pdf.set_fill_color(*bg_color_rgb)
            pdf.rect(0, y_start, 210, 45, "F")
            
            pdf.set_font("Helvetica", "B", 11)
            pdf.set_text_color(255, 255, 255)
            pdf.set_xy(15, y_start + 12)
            pdf.cell(0, 0, title)
            
            pdf.set_font("Helvetica", "", 8)
            pdf.set_text_color(107, 122, 153)
            pdf.set_xy(15, y_start + 18)
            pdf.cell(0, 0, "Career Intelligence Platform")
            
            if right_text:
                pdf.set_xy(180, y_start + 12)
                pdf.cell(15, 0, str(right_text), align="R")
            pdf.set_text_color(200, 212, 240)
        
        def _draw_footer(pdf, page_label):
            """Draw footer band at the bottom of the CURRENT page only."""
            footer_y = 282
            pdf.set_fill_color(22, 27, 39)
            pdf.rect(0, footer_y, 210, 12, "F")
            pdf.set_xy(0, footer_y + 3)
            pdf.set_font("Helvetica", "", 7)
            pdf.set_text_color(107, 122, 153)
            pdf.cell(210, 6, str(page_label), align='C')
            pdf.set_text_color(200, 212, 240)
        
        def _draw_progress_bar(pdf, x, y, width, filled_ratio, color_rgb, label=""):
            """Draw a progress bar with optional label."""
            pdf.set_draw_color(30, 45, 69)
            pdf.rect(x, y, width, 5)
            
            filled_width = max(0, min(width, width * filled_ratio))
            pdf.set_fill_color(*color_rgb)
            pdf.rect(x, y, filled_width, 5, "F")
            pdf.set_fill_color(15, 17, 23)
            
            if label:
                pdf.set_font("Helvetica", "B", 9)
                pdf.set_text_color(*color_rgb)
                pdf.set_xy(x + width + 5, y)
                pct = int(filled_ratio * 100)
                pdf.cell(0, 5, f"{pct}%")
                pdf.set_text_color(200, 212, 240)
        
        def _get_severity_color(severity_name):
            """Return RGB tuple for severity level."""
            severity_map = {
                "critical": (245, 210, 210),
                "high": (252, 235, 200),
                "medium": (210, 225, 252),
                "optional": (210, 240, 228),
                "low": (210, 240, 228),
            }
            return severity_map.get(severity_name.lower(), (210, 225, 252))
        
        def _get_severity_dark_color(severity_name):
            """Return dark RGB tuple for severity level."""
            severity_map = {
                "critical": (180, 40, 40),
                "high": (180, 100, 10),
                "medium": (40, 80, 180),
                "optional": (40, 100, 40),
                "low": (40, 100, 40),
            }
            return severity_map.get(severity_name.lower(), (40, 80, 180))
        
        def _draw_severity_badge(pdf, x, y, severity_text, bg_color):
            """Draw a filled badge for severity."""
            pdf.set_fill_color(*bg_color)
            pdf.rect(x, y - 1.5, 28, 5, "F")
            pdf.set_font("Helvetica", "B", 7)
            pdf.set_text_color(*_get_severity_dark_color(str(severity_text)))
            pdf.set_xy(x + 1, y)
            pdf.cell(0, 0, str(severity_text))
            pdf.set_text_color(200, 212, 240)
            pdf.set_fill_color(15, 17, 23)
        
        # ===== INITIALIZATION =====
        pdf = FPDF(orientation='P', unit='mm', format='A4')
        pdf.set_auto_page_break(False)  # BUG 1: Disable auto page breaks - we control them explicitly
        dark_navy = (15, 17, 23)
        dark_grey = (22, 27, 39)
        accent_blue = (79, 142, 247)
        amber = (239, 159, 39)
        light_text = (240, 244, 255)
        muted_grey = (107, 122, 153)
        border_grey = (30, 45, 69)
        
        phase_colors = {
            0: (52, 120, 246),   # Foundation - blue
            1: (215, 130, 30),   # Core - orange
            2: (130, 90, 210),   # Advanced - purple
        }
        
        # ===== PAGE 1: COVER PAGE =====
        pdf.add_page()
        generated_date = datetime.now().strftime("%B %d, %Y")
        
        # Header band
        _draw_header_band(pdf, "HR COPILOT", generated_date, dark_navy, 0)
        
        # Centered title and name
        pdf.set_font("Helvetica", "B", 26)
        pdf.set_text_color(*dark_navy)
        pdf.set_xy(0, 65)
        pdf.cell(0, 0, "Career Learning Plan", align="C")
        
        pdf.set_font("Helvetica", "", 16)
        pdf.set_text_color(*accent_blue)
        pdf.set_xy(0, 80)
        pdf.cell(0, 0, profile.name, align="C")
        
        # Horizontal rule
        pdf.set_draw_color(*border_grey)
        pdf.line(45, 92, 165, 92)
        
        # Summary box
        pdf.set_draw_color(*border_grey)
        pdf.rect(30, 100, 150, 60)
        
        # Left column
        pdf.set_font("Helvetica", "", 7)
        pdf.set_text_color(*muted_grey)
        pdf.set_xy(40, 108)
        pdf.cell(0, 0, "CURRENT ROLE")
        
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(15, 17, 23)  # BUG 4: Use dark text for visibility on white background
        pdf.set_xy(40, 113)
        pdf.cell(0, 0, gap_analysis.current_role[:20])
        pdf.set_text_color(200, 212, 240)
        
        pdf.set_font("Helvetica", "", 7)
        pdf.set_text_color(*muted_grey)
        pdf.set_xy(40, 123)
        pdf.cell(0, 0, "TARGET ROLE")
        
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(*accent_blue)
        pdf.set_xy(40, 128)
        pdf.cell(0, 0, target_display[:20])
        pdf.set_text_color(200, 212, 240)
        
        pdf.set_font("Helvetica", "", 7)
        pdf.set_text_color(*muted_grey)
        pdf.set_xy(40, 138)
        pdf.cell(0, 0, "GENERATED")
        
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(200, 212, 240)
        pdf.set_xy(40, 143)
        pdf.cell(0, 0, generated_date)
        
        # Right column
        total_weeks = int(learning_plan.total_weeks_recommended)
        total_hours = learning_plan.total_hours_required
        feasibility = learning_plan.feasibility_rating
        
        feasibility_colors = {
            "Achievable": (82, 183, 136),
            "Moderate commitment": (239, 159, 39),
            "Long-term plan": (79, 142, 247),
            "Extended journey": (224, 82, 82),
        }
        feasibility_color = feasibility_colors.get(feasibility, (79, 142, 247))
        
        pdf.set_font("Helvetica", "", 7)
        pdf.set_text_color(*muted_grey)
        pdf.set_xy(120, 108)
        pdf.cell(0, 0, "TIMELINE")
        
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(15, 17, 23)  # BUG 4: Use dark text for visibility
        pdf.set_xy(120, 113)
        pdf.cell(0, 0, f"{total_weeks} weeks")
        pdf.set_text_color(200, 212, 240)
        
        pdf.set_font("Helvetica", "", 7)
        pdf.set_text_color(*muted_grey)
        pdf.set_xy(120, 123)
        pdf.cell(0, 0, "TOTAL EFFORT")
        
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(*amber)
        pdf.set_xy(120, 128)
        pdf.cell(0, 0, f"{total_hours}h")
        
        pdf.set_font("Helvetica", "", 7)
        pdf.set_text_color(*muted_grey)
        pdf.set_xy(120, 138)
        pdf.cell(0, 0, "FEASIBILITY")
        
        pdf.set_font("Helvetica", "B", 9)
        feasibility_label = learning_plan.feasibility_rating
        fc = feasibility_colors.get(feasibility_label, (200, 212, 240))
        pdf.set_text_color(*fc)
        pdf.set_xy(120, 143)
        pdf.cell(0, 5, feasibility_label)
        pdf.set_text_color(200, 212, 240)
        
        # Footer
        _draw_footer(pdf, "CONFIDENTIAL - FOR INTERNAL USE ONLY")
        
        # ===== PAGE 2: SKILL GAP ANALYSIS =====
        pdf.add_page()
        
        # Section header
        pdf.set_fill_color(*dark_grey)
        pdf.rect(0, 0, 210, 18, "F")
        
        pdf.set_font("Helvetica", "B", 13)
        pdf.set_text_color(255, 255, 255)
        pdf.set_xy(15, 6)
        pdf.cell(0, 0, "SKILL GAP ANALYSIS")
        
        skills_met = len(profile.current_skills)
        total_skills = gap_analysis.total_required_skills
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*muted_grey)
        pdf.set_xy(165, 6)
        pdf.cell(0, 0, f"{skills_met} of {total_skills} skills met", align="R")
        
        # Readiness progress bar
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(*muted_grey)
        pdf.set_xy(15, 22)
        pdf.cell(0, 0, "Overall Readiness")
        
        readiness_ratio = skills_met / max(total_skills, 1)
        if readiness_ratio < 0.5:
            bar_color = accent_blue
        elif readiness_ratio < 0.8:
            bar_color = amber
        else:
            bar_color = (82, 183, 136)
        
        _draw_progress_bar(pdf, 15, 27, 180, readiness_ratio, bar_color)
        
        # Severity summary boxes
        severity_counts = gap_analysis.gaps_by_severity
        severities = [
            ("Critical", severity_counts.get('critical', 0), (245, 210, 210)),
            ("High", severity_counts.get('high', 0), (252, 235, 200)),
            ("Medium", severity_counts.get('medium', 0), (210, 225, 252)),
            ("Low", severity_counts.get('low', 0), (210, 240, 228)),
        ]
        
        box_y = 40
        for idx, (label, count, color) in enumerate(severities):
            box_x = 15 + (idx * 48)
            pdf.set_fill_color(*color)
            pdf.rect(box_x, box_y, 40, 18, "F")
            pdf.set_draw_color(*_get_severity_dark_color(label.lower()))
            pdf.rect(box_x, box_y, 40, 18)
            
            pdf.set_font("Helvetica", "B", 18)
            pdf.set_text_color(*_get_severity_dark_color(label.lower()))
            pdf.set_xy(box_x, box_y + 2)
            pdf.cell(40, 0, str(count), align="C")
            
            pdf.set_font("Helvetica", "", 7)
            pdf.set_text_color(*muted_grey)
            pdf.set_xy(box_x, box_y + 12)
            pdf.cell(40, 0, label, align="C")
        
        # Skill table
        table_y = 65
        header_height = 8
        row_height = 9
        
        pdf.set_fill_color(*dark_grey)
        pdf.rect(0, table_y, 210, header_height, "F")
        
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_text_color(255, 255, 255)
        pdf.set_xy(15, table_y + 1)
        pdf.cell(0, 0, "SKILL")
        pdf.set_xy(90, table_y + 1)
        pdf.cell(0, 0, "REQUIRED LEVEL")
        pdf.set_xy(140, table_y + 1)
        pdf.cell(0, 0, "SEVERITY")
        
        # Table rows
        row_y = table_y + header_height
        for gap_idx, gap in enumerate(gap_analysis.all_gaps[:8]):  # Limit to 8 rows
            if gap_idx % 2 == 0:
                pdf.set_fill_color(*dark_grey)
            else:
                pdf.set_fill_color(*dark_navy)
            pdf.rect(0, row_y, 210, row_height, "F")
            
            # Left accent bar
            severity_lower = gap.gap_severity.lower()
            pdf.set_fill_color(*_get_severity_color(severity_lower))
            pdf.rect(13, row_y, 2, row_height, "F")
            
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(200, 212, 240)
            pdf.set_xy(15, row_y + 2)
            pdf.cell(0, 0, gap.skill_name[:30])
            
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(*muted_grey)
            pdf.set_xy(90, row_y + 2)
            pdf.cell(0, 0, gap.required_level.value)
            
            _draw_severity_badge(pdf, 137, row_y + 4.5, gap.gap_severity.capitalize(), _get_severity_color(severity_lower))
            
            row_y += row_height
        
        _draw_footer(pdf, "PAGE 2: SKILL GAP ANALYSIS")
        
        # ===== PAGES 3+: LEARNING PHASES =====
        for phase_idx, phase in enumerate(learning_plan.phases):
            pdf.add_page()
            phase_color = phase_colors.get(phase_idx, (79, 142, 247))
            
            # Phase header band
            pdf.set_fill_color(*phase_color)
            pdf.rect(0, 0, 210, 22, "F")
            
            phase_label = ["Foundation", "Core", "Advanced"][phase_idx] if phase_idx < 3 else "Phase"
            
            pdf.set_font("Helvetica", "B", 8)
            pdf.set_text_color(255, 255, 255)
            pdf.set_xy(28, 5)
            pdf.cell(0, 0, f"PHASE {phase_idx + 1}")
            
            pdf.set_font("Helvetica", "B", 15)
            pdf.set_text_color(255, 255, 255)
            pdf.set_xy(28, 11)
            pdf.cell(0, 0, phase_label)
            
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(255, 255, 255)
            pdf.set_xy(170, 8)
            pdf.cell(0, 0, f"{int(phase.recommended_weeks)} weeks  ·  {phase.total_hours} hours", align="R")
            
            # Phase progress bar - FIX: handle Skill objects in profile.current_skills
            phase_task_names = [t.skill_name.lower() if isinstance(t.skill_name, str) else t.skill_name.name.lower() for t in phase.tasks]
            phase_skills_met = len([s for s in profile.current_skills if s.name.lower() in phase_task_names])
            phase_ratio = phase_skills_met / max(len(phase.tasks), 1)
            
            pdf.set_font("Helvetica", "", 8)
            pdf.set_text_color(*muted_grey)
            pdf.set_xy(15, 28)
            pdf.cell(0, 0, "Phase completion from existing skills")
            
            _draw_progress_bar(pdf, 15, 33, 180, phase_ratio, phase_color)
            
            # Task cards
            card_y = 43
            max_hours = max((t.estimated_hours for t in phase.tasks), default=1)
            
            for task in phase.tasks:
                # Card outline - FIXED: Increased height from 28 to 38 for content fit
                card_height = 38
                pdf.set_draw_color(*border_grey)
                pdf.rect(15, card_y, 180, card_height)
                
                # Left accent bar
                pdf.set_fill_color(*phase_color)
                pdf.rect(15, card_y, 2, card_height, "F")
                
                # Priority badge
                severity = "CRITICAL" if task.must_complete else "OPTIONAL"
                badge_color = (245, 210, 210) if task.must_complete else (210, 225, 252)
                _draw_severity_badge(pdf, 17, card_y + 5, severity, badge_color)
                
                # Skill name and hours - Fixed visibility and positioning
                pdf.set_font("Helvetica", "B", 11)
                pdf.set_text_color(15, 17, 23)  # Dark text for visibility
                pdf.set_xy(50, card_y + 1.5)
                skill_display = skill_str(task.skill_name)[:25]  # Truncate to fit
                pdf.cell(0, 0, skill_display)
                
                pdf.set_font("Helvetica", "B", 10)
                pdf.set_text_color(*amber)
                pdf.set_xy(155, card_y + 1.5)  # Move left to fit inside box
                pdf.cell(30, 0, f"{task.estimated_hours}h", align="R")  # Constrain width
                pdf.set_text_color(200, 212, 240)
                
                # Resources line + links
                pdf.set_font("Helvetica", "B", 7)
                pdf.set_text_color(15, 17, 23)  # Dark text for visibility
                pdf.set_xy(17, card_y + 8)
                pdf.cell(0, 0, "RESOURCES:")
                
                # BUG 2: Fix SKILL_RESOURCES lookup with proper normalization
                raw_name = task.skill_name
                if hasattr(raw_name, 'name'):
                    skill_key = raw_name.name.lower().strip()
                elif isinstance(raw_name, str):
                    skill_key = raw_name.lower().strip()
                else:
                    skill_key = str(raw_name).lower().strip()
                
                resources = SKILL_RESOURCES.get(skill_key, [])
                
                if resources:
                    pdf.set_font("Helvetica", "U", 8)
                    pdf.set_text_color(79, 142, 247)
                    y_res = card_y + 8
                    for idx, res in enumerate(resources[:2]):  # Show top 2 resources
                        name = res.get("name", "")
                        url  = res.get("url", "")
                        if name:
                            pdf.set_xy(40, y_res)
                            # FIXED: Always create link if URL exists, even if partial
                            if url and url.strip():
                                pdf.cell(70, 5, name, link=url)  # Working hyperlink
                            else:
                                pdf.cell(70, 5, name)  # No link if URL missing
                            y_res += 4
                    pdf.set_text_color(200, 212, 240)
                else:
                    pdf.set_font("Helvetica", "U", 8)
                    pdf.set_text_color(52, 120, 246)  # Blue for fallback
                    pdf.set_xy(40, card_y + 8)
                    # FIXED: Add working fallback URLs
                    pdf.cell(0, 5, "Coursera", link="https://www.coursera.org")
                    pdf.set_xy(40, card_y + 11.5)
                    pdf.cell(0, 5, "Kaggle", link="https://www.kaggle.com")
                    pdf.set_text_color(200, 212, 240)
                
                # Effort bar
                pdf.set_draw_color(*border_grey)
                pdf.line(17, card_y + 15, 193, card_y + 15)
                
                pdf.set_font("Helvetica", "B", 7)
                pdf.set_text_color(15, 17, 23)  # Dark text for visibility
                pdf.set_xy(17, card_y + 16.5)
                pdf.cell(0, 0, "EFFORT:")
                
                effort_ratio = task.estimated_hours / max_hours if max_hours > 0 else 0
                pdf.set_fill_color(*border_grey)
                pdf.rect(50, card_y + 17, 60, 3, "F")
                
                lighter_phase = tuple(min(int(c * 1.3), 255) for c in phase_color)
                pdf.set_fill_color(*lighter_phase)
                pdf.rect(50, card_y + 17, 60 * effort_ratio, 3, "F")
                
                card_y += 40  # FIXED: Increased spacing from 32 to 40 to match card height
            
            _draw_footer(pdf, f"PHASE {phase_idx + 1}: {phase_label}")
        
        # ===== FINAL PAGE: SUMMARY & NEXT STEPS =====
        pdf.add_page()
        
        # Header
        _draw_header_band(pdf, "NEXT STEPS & RECOMMENDATIONS", "", dark_navy, 0)
        
        # Three action boxes
        first_task = learning_plan.phases[0].tasks[0] if learning_plan.phases and learning_plan.phases[0].tasks else None
        box_width = 55
        box_height = 50
        box_y = 55
        
        # Box 1: Start This Week - FIX: use skill_str() for safe skill name conversion
        box_x = 15
        pdf.set_draw_color(52, 120, 246)
        pdf.set_line_width(2)
        pdf.line(box_x, box_y, box_x + box_width, box_y)
        pdf.set_line_width(0.2)
        pdf.rect(box_x, box_y, box_width, box_height)
        
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(52, 120, 246)
        pdf.set_xy(box_x, box_y + 3)
        pdf.cell(box_width, 0, "Start This Week", align="C")
        
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(*muted_grey)
        pdf.set_xy(box_x + 2, box_y + 10)
        task_name = skill_str(first_task.skill_name) if first_task else "Begin Phase 1"
        
        # BUG 2: Get proper resource names for this skill with proper normalization
        first_skill_key = ""
        if first_task and hasattr(first_task, 'skill_name'):
            raw_name = first_task.skill_name
            if hasattr(raw_name, 'name'):
                first_skill_key = raw_name.name.lower().strip()
            elif isinstance(raw_name, str):
                first_skill_key = raw_name.lower().strip()
            else:
                first_skill_key = str(raw_name).lower().strip()
        
        first_resources = SKILL_RESOURCES.get(first_skill_key, [])
        if first_resources:
            resource_names = [r.get("name", "") for r in first_resources[:2]]
            resource_text = "  ·  ".join([x for x in resource_names if x])
        else:
            resource_text = "Coursera or Kaggle"
        
        pdf.multi_cell(box_x + box_width - 4, 3, f"{task_name}\n\n{resource_text}")
        
        # Box 2: Track Progress
        box_x = 75
        pdf.set_draw_color(82, 183, 136)
        pdf.set_line_width(2)
        pdf.line(box_x, box_y, box_x + box_width, box_y)
        pdf.set_line_width(0.2)
        pdf.rect(box_x, box_y, box_width, box_height)
        
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(82, 183, 136)
        pdf.set_xy(box_x, box_y + 3)
        pdf.cell(box_width, 0, "Track Progress", align="C")
        
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(*muted_grey)
        pdf.set_xy(box_x + 2, box_y + 10)
        pdf.multi_cell(box_width - 4, 3, "Review your plan every 2 weeks. Update skills as you complete each phase.")
        
        # Box 3: Stay Consistent
        box_x = 135
        pdf.set_draw_color(239, 159, 39)
        pdf.set_line_width(2)
        pdf.line(box_x, box_y, box_x + box_width, box_y)
        pdf.set_line_width(0.2)
        pdf.rect(box_x, box_y, box_width, box_height)
        
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(239, 159, 39)
        pdf.set_xy(box_x, box_y + 3)
        pdf.cell(box_width, 0, "Stay Consistent", align="C")
        
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(*muted_grey)
        phase1_weeks = int(learning_plan.phases[0].recommended_weeks) if learning_plan.phases else 12
        hours_per_week = total_hours // total_weeks if total_weeks > 0 else 0
        pdf.set_xy(box_x + 2, box_y + 10)
        pdf.multi_cell(box_width - 4, 3, f"At {hours_per_week}h/week, Phase 1 takes {phase1_weeks} weeks. Consistency beats intensity.")
        
        # Final line
        pdf.set_font("Helvetica", "I", 8)
        pdf.set_text_color(61, 79, 110)
        pdf.set_xy(0, 250)
        pdf.cell(0, 0, "Generated by HR Copilot - Career Intelligence Platform", align="C")
        
        _draw_footer(pdf, "FINAL: NEXT STEPS & RECOMMENDATIONS")
        
        # ===== FINALIZE =====
        pdf_bytes = pdf.output()
        
        if isinstance(pdf_bytes, str):
            pdf_bytes = pdf_bytes.encode('latin-1')
        elif isinstance(pdf_bytes, bytearray):
            pdf_bytes = bytes(pdf_bytes)
        
        return pdf_bytes
    
    except ImportError:
        return None
    except Exception as e:
        st.error(f"PDF generation error: {str(e)}")
        return None
        
def _generate_plan_text(profile: UserProfile, gap_analysis: SkillGapAnalysis, learning_plan: CareerLearningPlan) -> str:
    """Generate text export of learning plan."""
    lines = [
        "=" * 80,
        "CAREER LEARNING PLAN",
        "=" * 80,
        "",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "OVERVIEW",
        f"  Name: {profile.name}",
        f"  Current Role: {gap_analysis.current_role}",
        f"  Target Role: {gap_analysis.target_role}",
        f"  Timeline: {int(learning_plan.total_weeks_recommended)} weeks",
        f"  Total Effort: {learning_plan.total_hours_required} hours",
        f"  Feasibility: {learning_plan.feasibility_rating}",
        "",
        "SKILL GAPS",
        f"  Total Required Skills: {gap_analysis.total_required_skills}",
        f"  Critical Gaps: {gap_analysis.gaps_by_severity.get('critical', 0)}",
        f"  High Priority: {gap_analysis.gaps_by_severity.get('high', 0)}",
        "",
        "LEARNING PHASES",
    ]
    
    for phase_idx, phase in enumerate(learning_plan.phases, 1):
        lines.extend([
            "",
            f"Phase {phase_idx}: {phase.phase_name}",
            f"  Duration: {int(phase.recommended_weeks)} weeks",
            f"  Total Hours: {phase.total_hours}",
        ])
        for task in phase.tasks:
            prefix = "[CRITICAL]" if task.must_complete else "[OPTIONAL]"
            lines.append(f"  {prefix} {task.skill_name} ({task.estimated_hours}h)")
    
    lines.append("")
    lines.append("=" * 80)
    return "\n".join(lines)


# ============================================================================
# HR POLICY CHAT
# ============================================================================

def page_hr_policy():
    """HR Policy Assistant - Chat interface."""
    page_header(
        badge_text="HR Knowledge Base · RAG",
        title="HR Policy Assistant",
        subtitle="Evidence-backed answers with source citations"
    )
    
    # Chat display container with custom styling
    st.markdown("<div style='font-size:11px;font-weight:600;color:#6b7a99;text-transform:uppercase;letter-spacing:0.7px;margin-bottom:16px;'>💬 Chat History</div>", unsafe_allow_html=True)
    
    if st.session_state.hr_chat_history:
        chat_container = st.container()
        with chat_container:
            for idx, message in enumerate(st.session_state.hr_chat_history):
                if message["role"] == "user":
                    st.markdown(f"""
                    <div style="display:flex;justify-content:flex-end;margin:8px 0;">
                      <div style="max-width:75%;background:#4f8ef7;color:white;
                        padding:11px 15px;border-radius:12px 12px 2px 12px;
                        font-size:13px;line-height:1.6;">{message['content']}</div>
                    </div>""", unsafe_allow_html=True)
                else:
                    response_content = message['content']
                    confidence = message.get('confidence', '❌ 0% Low')
                    evidence = message.get('evidence', [])
                    
                    evidence_pills = ""
                    for src in evidence[:3]:
                        evidence_pills += f"""<span style="display:inline-flex;
                          align-items:center;gap:4px;background:rgba(79,142,247,0.1);
                          border:1px solid rgba(79,142,247,0.2);border-radius:20px;
                          padding:4px 10px;font-size:10px;color:#4f8ef7;
                          margin:6px 4px 0 0;font-weight:600;">📄 {src[:50]}...</span>"""
                    
                    st.markdown(f"""
                    <div style="display:flex;justify-content:flex-start;margin:8px 0;">
                      <div style="max-width:78%;">
                        <div style="background:#161b27;border:1px solid #1e2d45;
                          color:#c8d4f0;padding:11px 15px;
                          border-radius:12px 12px 12px 2px;
                          font-size:13px;line-height:1.6;">{response_content}</div>
                        <div style="margin-top:8px;font-size:10px;color:#6b7a99;">
                          <strong>Confidence:</strong> {confidence}
                        </div>
                        <div style="margin-top:4px;display:flex;flex-wrap:wrap;">
                          {evidence_pills}
                        </div>
                      </div>
                    </div>""", unsafe_allow_html=True)
    else:
        st.info("👋 No chat history yet. Ask a question below to get started!")
    
    st.divider()
    
    # Input section
    st.markdown("<div style='font-size:11px;font-weight:600;color:#6b7a99;text-transform:uppercase;letter-spacing:0.7px;margin-bottom:16px;'>❓ Ask a Question</div>", unsafe_allow_html=True)
    col_input, col_send = st.columns([0.85, 0.15])
    
    with col_input:
        user_query = st.text_input(
            "Your question:",
            placeholder="e.g., What is the maternity leave policy?",
            key="hr_query_input",
            label_visibility="collapsed"
        )
    
    with col_send:
        send_button = st.button("Ask", use_container_width=True, type="primary", key="send_hr_query")
    
    if send_button and user_query:
        # Add user message to history immediately
        st.session_state.hr_chat_history.append({
            "role": "user",
            "content": user_query
        })
        
        # Query backend with visible spinner
        with st.spinner("🔍 Searching knowledge base..."):
            result = query_hr_policy(user_query)
        
        if result:
            confidence = result.get("confidence", 0.0)
            answer = result.get("answer", "No answer found.")
            hits = result.get("hits", [])
            
            # Format response
            confidence_badge = format_confidence(confidence)
            
            # Format evidence list for display
            formatted_evidence = []
            if hits:
                for idx, hit in enumerate(hits[:3]):
                    formatted_evidence.append(format_evidence_chunk(hit, idx))
            
            st.session_state.hr_chat_history.append({
                "role": "assistant",
                "content": answer,
                "confidence": confidence_badge,
                "evidence": formatted_evidence
            })
            
            st.success("✅ Answer retrieved and added to chat history!")
        else:
            error_msg = "⚠️ Could not connect to the HR policy database. Please check if the service is running."
            st.session_state.hr_chat_history.append({
                "role": "assistant",
                "content": error_msg,
                "confidence": "❌ 0% Low"
            })
            st.error("Connection Error - Could not reach the knowledge base")
        
        st.rerun()


# ============================================================================
# MAIN ROUTER
# ============================================================================

def main():
    """Main entry point - unified system."""
    init_session_state()
    
    # Sidebar navigation
    st.sidebar.markdown("# 🚀 HR Copilot")
    st.sidebar.markdown("Career & Policy Assistant")
    st.sidebar.divider()
    
    # Tab selection
    tabs = st.sidebar.radio(
        "Select a module:",
        ["Career Setup", "HR Policy Assistant"],
        index=0 if st.session_state.system_tab == "Career Setup" else 1,
    )
    
    st.session_state.system_tab = tabs
    
    st.sidebar.divider()
    
    # Career progress indicator
    if st.session_state.system_tab == "Career Setup":
        st.sidebar.write("**Career Setup Progress**")
        st.sidebar.progress(
            value=st.session_state.career_step / 3,
            text=f"Step {st.session_state.career_step} of 3"
        )
    
    # Route
    if st.session_state.system_tab == "Career Setup":
        if st.session_state.career_step == 1:
            page_career_onboarding()
        elif st.session_state.career_step == 2:
            page_career_gaps()
        elif st.session_state.career_step == 3:
            page_career_timeline()
        else:
            st.session_state.career_step = 1
            st.rerun()
    
    elif st.session_state.system_tab == "HR Policy Assistant":
        page_hr_policy()


if __name__ == "__main__":
    main()
