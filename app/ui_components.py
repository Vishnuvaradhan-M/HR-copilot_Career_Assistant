"""
Reusable Streamlit UI components for the Career Assistant frontend.

Provides modern, minimalist cards, bars, timeline blocks, and interactive elements.
"""

import streamlit as st
from typing import List, Dict, Any, Tuple, Optional
import math


def render_hero_header(title: str, subtitle: str) -> None:
    """Render a large hero header with whitespace."""
    st.markdown(f"<h1 style='text-align: center; font-size: 3em; margin: 1em 0 0.3em 0;'>{title}</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: center; font-size: 1.2em; color: #666; margin-bottom: 2em;'>{subtitle}</p>", unsafe_allow_html=True)


def render_card(title: str, content: Any, width: float = 1.0, expandable: bool = False, 
                help_text: Optional[str] = None) -> Optional[bool]:
    """
    Render a minimalist card with soft shadow and rounded corners.
    
    Returns True if expanded (if expandable=True), False otherwise.
    """
    card_html = f"""
    <div style='
        background: white;
        border-radius: 12px;
        padding: 1.5em;
        margin: 0.5em 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        transition: box-shadow 0.2s ease;
    ' onmouseover="this.style.boxShadow='0 4px 16px rgba(0,0,0,0.12)'" 
      onmouseout="this.style.boxShadow='0 2px 8px rgba(0,0,0,0.08)'">
        <h3 style='margin: 0 0 0.5em 0; color: #1a1a1a;'>{title}</h3>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)
    
    if expandable:
        with st.expander(f"View Details", expanded=False):
            st.write(content)
            if help_text:
                st.caption(f"💡 {help_text}")
        return True
    else:
        st.write(content)
        if help_text:
            st.caption(f"💡 {help_text}")
        return False


def render_metric_card(label: str, value: str, context: str = "", color: str = "#0066CC") -> None:
    """Render a metric card with large value display."""
    metric_html = f"""
    <div style='
        background: linear-gradient(135deg, {color}15 0%, {color}05 100%);
        border-left: 4px solid {color};
        border-radius: 8px;
        padding: 1.5em;
        margin: 0.5em 0;
        text-align: center;
    '>
        <p style='margin: 0; color: #666; font-size: 0.9em;'>{label}</p>
        <h2 style='margin: 0.3em 0; color: {color}; font-size: 2.5em;'>{value}</h2>
        <p style='margin: 0; color: #999; font-size: 0.85em;'>{context}</p>
    </div>
    """
    st.markdown(metric_html, unsafe_allow_html=True)


def render_severity_bar(skill_name: str, current: float, required: float, 
                       severity: str, complexity: str) -> None:
    """
    Render a horizontal severity bar showing skill gap.
    
    Args:
        skill_name: Skill name
        current: Current proficiency (0-1)
        required: Required proficiency (0-1)
        severity: "critical", "high", "medium", "low"
        complexity: "hard", "moderate", "easy"
    """
    severity_colors = {
        "critical": "#DC3545",
        "high": "#FF6B6B",
        "medium": "#FFC107",
        "low": "#28A745"
    }
    color = severity_colors.get(severity, "#0066CC")
    gap = required - current
    
    bar_html = f"""
    <div style='margin: 1em 0;'>
        <div style='display: flex; justify-content: space-between; margin-bottom: 0.3em;'>
            <span style='font-weight: 500; color: #1a1a1a;'>{skill_name}</span>
            <span style='font-size: 0.85em; color: #666;'>{severity.upper()} • {complexity.capitalize()}</span>
        </div>
        <div style='display: flex; gap: 0.5em; align-items: center; height: 24px;'>
            <!-- Current Level -->
            <div style='flex: 1; background: #E0E0E0; border-radius: 4px; position: relative; height: 8px;'>
                <div style='background: #0066CC; height: 8px; width: {current*100}%; border-radius: 4px; transition: width 0.3s;'></div>
            </div>
            <span style='font-size: 0.8em; color: #999; width: 40px; text-align: right;'>{current:.0%}</span>
        </div>
        <div style='display: flex; gap: 0.5em; align-items: center; height: 24px; margin-top: 0.3em;'>
            <!-- Required Level -->
            <div style='flex: 1; background: #F5F5F5; border-radius: 4px; position: relative; height: 8px; border: 1px dashed {color};'>
                <div style='background: {color}; height: 8px; width: {required*100}%; border-radius: 4px; opacity: 0.6;'></div>
            </div>
            <span style='font-size: 0.8em; color: {color}; width: 40px; text-align: right;'>{required:.0%}</span>
        </div>
    </div>
    """
    st.markdown(bar_html, unsafe_allow_html=True)


def render_chip(label: str, color: str = "#0066CC", deletable: bool = False) -> Optional[bool]:
    """
    Render a chip/badge element. Returns True if delete clicked (if deletable=True).
    """
    chip_html = f"""
    <span style='
        display: inline-block;
        background: {color}20;
        color: {color};
        border-radius: 20px;
        padding: 0.4em 0.8em;
        margin: 0.3em;
        font-size: 0.9em;
        font-weight: 500;
        border: 1px solid {color}40;
    '>{label}</span>
    """
    st.markdown(chip_html, unsafe_allow_html=True)


def render_transferable_skills(skills: List[str]) -> None:
    """Render transferable skills as colorful chips."""
    if not skills:
        return
    
    st.markdown("#### ✓ Transferable Skills")
    chips_html = '<div style="margin: 1em 0;">'
    for skill in skills:
        chips_html += f"""
        <span style='
            display: inline-block;
            background: #D4EDDA;
            color: #155724;
            border-radius: 20px;
            padding: 0.5em 1em;
            margin: 0.3em;
            font-size: 0.9em;
            font-weight: 500;
            border: 1px solid #C3E6CB;
        '>✓ {skill}</span>
        """
    chips_html += '</div>'
    st.markdown(chips_html, unsafe_allow_html=True)


def render_phase_block(phase_name: str, phase_number: int, weeks: float, hours: int, 
                       tasks: List[Dict[str, Any]], is_parallel: bool = False) -> None:
    """
    Render a timeline phase block showing tasks, duration, and effort.
    
    Args:
        phase_name: "Foundation", "Core", "Advanced"
        phase_number: 1, 2, 3
        weeks: Duration in weeks
        hours: Total effort hours
        tasks: List of task dicts with skill_name, hours, resource_type
        is_parallel: Whether this phase runs in parallel
    """
    phase_colors = {
        1: "#E3F2FD",
        2: "#F3E5F5",
        3: "#FFF3E0"
    }
    phase_border = {
        1: "#1976D2",
        2: "#7B1FA2",
        3: "#F57C00"
    }
    
    bg_color = phase_colors.get(phase_number, "#F5F5F5")
    border_color = phase_border.get(phase_number, "#999")
    weeks = weeks or 0.0
    hours = hours or 0
    
    block_html = f"""
    <div style='
        background: {bg_color};
        border-left: 5px solid {border_color};
        border-radius: 8px;
        padding: 1.5em;
        margin: 1em 0;
    '>
        <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 1em;'>
            <h4 style='margin: 0; color: {border_color};'>Phase {phase_number}: {phase_name}</h4>
            <span style='background: {border_color}20; color: {border_color}; padding: 0.3em 0.8em; border-radius: 12px; font-size: 0.85em;'>
                {weeks:.1f}w • {hours}h
            </span>
        </div>
        {f"<p style='margin: 0 0 1em 0; font-size: 0.9em; color: #666;'>⚡ Runs in parallel with other phases</p>" if is_parallel else ""}
    </div>
    """
    st.markdown(block_html, unsafe_allow_html=True)
    
    # Render tasks
    if tasks:
        for task in tasks:
            skill = task.get("skill_name", "Task")
            est_hours = task.get("estimated_hours", 0) or 0
            res_type = task.get("resource_type", "Learning")
            task_html = f"""
            <div style='
                background: white;
                border-radius: 6px;
                padding: 1em;
                margin: 0.5em 0;
                border-left: 3px solid {border_color};
                box-shadow: 0 1px 3px rgba(0,0,0,0.05);
            '>
                <div style='display: flex; justify-content: space-between;'>
                    <span style='font-weight: 500;'>{skill}</span>
                    <span style='color: #666;'>{est_hours}h</span>
                </div>
                <p style='margin: 0.5em 0 0 0; font-size: 0.85em; color: #999;'>
                    📚 {res_type}
                </p>
            </div>
            """
            st.markdown(task_html, unsafe_allow_html=True)


def render_feasibility_gauge(confidence: float, rating: str) -> None:
    """
    Render a feasibility confidence gauge with emoji-based rating.
    
    Args:
        confidence: 0.0-1.0 confidence score
        rating: "high", "medium", "low", "very_low"
    """
    rating_icons = {
        "high": "✅ ACHIEVABLE",
        "medium": "⚠️ MODERATE",
        "low": "⛔ CHALLENGING",
        "very_low": "🚫 VERY DIFFICULT"
    }
    rating_colors = {
        "high": "#28A745",
        "medium": "#FFC107",
        "low": "#FF6B6B",
        "very_low": "#DC3545"
    }
    
    color = rating_colors.get(rating, "#999")
    icon = rating_icons.get(rating, "UNKNOWN")
    conf_pct = max(0, min(100, confidence * 100))
    
    # Gauge visualization (CSS-based progress bar, no SVG)
    gauge_html = f"""
    <div style='
        background: white;
        border-radius: 12px;
        padding: 2em;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        margin: 1em 0;
    '>
        <h3 style='margin: 0 0 1.5em 0; color: #1a1a1a;'>Career Transition Feasibility</h3>
        
        <p style='margin: 0 0 0.5em 0; font-size: 3em; font-weight: bold; color: {color};'>{confidence:.0%}</p>
        <p style='margin: 0 0 1.5em 0; font-size: 0.9em; color: #666;'>Feasibility Confidence</p>
        
        <div style='margin-bottom: 1.5em;'>
            <div style='background: #E0E0E0; border-radius: 8px; height: 16px; overflow: hidden;'>
                <div style='background: {color}; height: 100%; width: {conf_pct}%; transition: width 0.3s ease;'></div>
            </div>
        </div>
        
        <div style='background: {color}15; border: 2px solid {color}; border-radius: 10px; padding: 1.2em;'>
            <p style='margin: 0; font-size: 1.3em; font-weight: 600; color: {color};'>{icon}</p>
            <p style='margin: 0.5em 0 0 0; font-size: 0.9em; color: #666;'>Based on timeline and effort requirements</p>
        </div>
    </div>
    """
    st.markdown(gauge_html, unsafe_allow_html=True)


def render_recommendation_card(title: str, description: str, icon: str = "💡") -> None:
    """Render an actionable recommendation card."""
    card_html = f"""
    <div style='
        background: #FFFACD;
        border-left: 4px solid #FFC107;
        border-radius: 8px;
        padding: 1.2em;
        margin: 0.8em 0;
    '>
        <div style='display: flex; gap: 1em;'>
            <span style='font-size: 1.5em;'>{icon}</span>
            <div style='flex: 1;'>
                <h4 style='margin: 0 0 0.3em 0; color: #1a1a1a;'>{title}</h4>
                <p style='margin: 0; color: #666; font-size: 0.95em;'>{description}</p>
            </div>
        </div>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)


def render_timeline_horizontal(phases: List[Dict[str, Any]]) -> None:
    """
    Render a horizontal timeline showing phase progression.
    
    Args:
        phases: List of phase dicts with phase_name, week_start, week_end, hours
    """
    if not phases:
        return
    
    timeline_html = '<div style="margin: 2em 0;">'
    timeline_html += '<h3 style="margin: 0 0 1.5em 0; color: #1a1a1a;">Timeline Overview</h3>'
    
    colors = {
        "Foundation": "#1976D2",
        "Core": "#7B1FA2",
        "Advanced": "#F57C00"
    }
    
    for phase in phases:
        phase_name = phase.get("phase_name", "Unknown")
        start = phase.get("week_start") or 0
        end = phase.get("week_end") or 0
        hours = phase.get("hours") or 0
        duration = end - start
        color = colors.get(phase_name, "#0066CC")
        
        timeline_html += f"""
        <div style='
            background: {color}15;
            border-left: 4px solid {color};
            border-radius: 6px;
            padding: 1em;
            margin: 0.8em 0;
        '>
            <div style='display: flex; justify-content: space-between; align-items: center;'>
                <span style='font-weight: 600; color: {color};'>{phase_name}</span>
                <span style='color: #666; font-size: 0.9em;'>Weeks {start}-{end} ({duration}w, {hours}h)</span>
            </div>
        </div>
        """
    
    timeline_html += '</div>'
    st.markdown(timeline_html, unsafe_allow_html=True)


def render_audit_trail(decisions: List[Dict[str, str]]) -> None:
    """Render an expandable audit trail showing decision reasoning."""
    with st.expander("📋 Decision Audit Trail", expanded=False):
        audit_html = '<div style="margin: 1em 0;">'
        for i, decision in enumerate(decisions, 1):
            audit_html += f"""
            <div style='
                background: #F5F5F5;
                border-radius: 6px;
                padding: 1em;
                margin: 0.8em 0;
                border-left: 3px solid #0066CC;
            '>
                <p style='margin: 0 0 0.5em 0; font-weight: 500; color: #1a1a1a;'>{i}. {decision.get("decision", "")}</p>
                <p style='margin: 0; color: #666; font-size: 0.9em;'>{decision.get("reasoning", "")}</p>
                {f'<p style="margin: 0.5em 0 0 0; font-size: 0.85em; color: #999;">🔢 Confidence: {decision.get("confidence", "N/A")}</p>' if decision.get("confidence") else ""}
            </div>
            """
        audit_html += '</div>'
        st.markdown(audit_html, unsafe_allow_html=True)


def render_page_divider() -> None:
    """Render a subtle page divider."""
    st.markdown("""
    <div style='margin: 3em 0; border-top: 1px solid #E0E0E0;'></div>
    """, unsafe_allow_html=True)
