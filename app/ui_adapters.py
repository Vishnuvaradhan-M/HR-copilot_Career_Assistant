"""
Data adapters that transform backend dataclasses into UI-friendly structures.

No logic transformation—only formatting and organization for display.
"""

from typing import List, Dict, Any, Optional
from app.schemas.career import (
    NormalizedRole,
    SkillGapAnalysis,
    SkillGap,
    CareerLearningPlan,
    LearningPhasePlan,
    LearningTask,
    ProficiencyLevel,
)


def _proficiency_to_score(level) -> float:
    """Convert ProficiencyLevel enum to numeric 0.0-1.0 score."""
    if isinstance(level, str):
        level = level.lower()
    else:
        level = level.value if hasattr(level, 'value') else str(level).lower()
    
    scores = {
        "none": 0.0,
        "beginner": 0.25,
        "intermediate": 0.5,
        "advanced": 0.75,
        "expert": 1.0,
    }
    return scores.get(level, 0.0)

def normalize_role_to_display(normalized_role: NormalizedRole) -> Dict[str, Any]:
    """
    Convert NormalizedRole dataclass to UI display dict.
    
    Returns:
        Dict with keys: normalized_name, confidence, is_promotion, reasoning
    """
    return {
        "normalized_name": normalized_role.normalized_name,
        "original_input": normalized_role.original_input,
        "confidence": normalized_role.confidence,
        "category": normalized_role.category,
        "is_promotion": normalized_role.is_promotion,
        "reasoning": normalized_role.reasoning,
    }


def skill_gap_analysis_to_display(gap_analysis: SkillGapAnalysis) -> Dict[str, Any]:
    """
    Convert SkillGapAnalysis to UI-friendly display structure.
    
    Organizes gaps by severity and phase with formatted metrics.
    """
    # Group gaps by severity
    gaps_by_severity = {}
    severity_order = ["critical", "high", "medium", "low"]
    
    for gap in gap_analysis.all_gaps:
        severity = gap.gap_severity
        if severity not in gaps_by_severity:
            gaps_by_severity[severity] = []
        gaps_by_severity[severity].append(gap)
    
    # Group gaps by phase
    gaps_by_phase = {}
    phase_order = ["foundation", "core", "advanced"]
    
    for gap in gap_analysis.all_gaps:
        phase = gap.learning_phase
        if phase not in gaps_by_phase:
            gaps_by_phase[phase] = []
        gaps_by_phase[phase].append(gap)
    
    # Convert each gap to display format
    def gap_to_display(gap: SkillGap) -> Dict[str, Any]:
        return {
            "skill_name": gap.skill_name,
            "current_level": gap.current_level,
            "required_level": gap.required_level,
            "current_score": _proficiency_to_score(gap.current_level),
            "required_score": _proficiency_to_score(gap.required_level),
            "gap_severity": gap.gap_severity,
            "learning_complexity": gap.learning_complexity,
            "must_have": gap.must_have,
            "learning_phase": gap.learning_phase,
            "normalized_gap_score": gap.normalized_gap_score,
            "reasoning": gap.reasoning,
        }
    
    return {
        "target_role": gap_analysis.target_role,
        "all_gaps": [gap_to_display(gap) for gap in gap_analysis.all_gaps],
        "gaps_by_severity": {
            severity: [gap_to_display(gap) for gap in gaps_by_severity.get(severity, [])]
            for severity in severity_order
        },
        "gaps_by_phase": {
            phase: [gap_to_display(gap) for gap in gaps_by_phase.get(phase, [])]
            for phase in phase_order
        },
        "transferable_skills": gap_analysis.transferable_skills,
        "total_gaps": len(gap_analysis.all_gaps),
        "critical_gaps": len(gaps_by_severity.get("critical", [])),
        "confidence_score": gap_analysis.confidence_score,
    }


def learning_plan_to_display(plan: CareerLearningPlan) -> Dict[str, Any]:
    """
    Convert CareerLearningPlan to UI display structure.
    
    Organizes phases, tasks, timeline, and metrics for dashboard rendering.
    """
    
    def task_to_display(task: LearningTask) -> Dict[str, Any]:
        return {
            "skill_name": task.skill_name,
            "estimated_hours": task.estimated_hours,
            "effort_per_week": getattr(task, 'effort_hours_per_week', None),
            "estimated_weeks": task.estimated_weeks,
            "resource_type": task.resource_type,
            "parallel_with": task.parallel_with,
            "prerequisites": task.prerequisites,
            "reasoning": task.reasoning,
        }
    
    def phase_to_display(phase: LearningPhasePlan) -> Dict[str, Any]:
        phase_names = {1: "Foundation", 2: "Core", 3: "Advanced"}
        
        return {
            "phase_number": phase.phase_number,
            "phase_name": phase_names.get(phase.phase_number, f"Phase {phase.phase_number}"),
            "total_hours": phase.total_hours,
            "sequential_weeks": phase.total_weeks_sequential,
            "recommended_weeks": phase.recommended_weeks,
            "start_week": phase.start_week,
            "end_week": phase.end_week,
            "milestone_count": len(phase.key_milestones),
            "tasks": [task_to_display(task) for task in phase.tasks],
            "task_count": len(phase.tasks),
        }
    
    # Calculate timeline overview
    phases_timeline = []
    for phase in plan.phases:
        phase_names = {1: "Foundation", 2: "Core", 3: "Advanced"}
        phases_timeline.append({
            "phase_name": phase_names.get(phase.phase_number, f"Phase {phase.phase_number}"),
            "week_start": phase.start_week,
            "week_end": phase.end_week,
            "hours": phase.total_hours,
        })
    
    return {
        "user_name": plan.user_name,
        "target_role": plan.target_role,
        "total_hours_required": plan.total_hours_required,
        "total_weeks_recommended": plan.total_weeks_recommended,
        "total_months_recommended": plan.total_months_recommended,
        "feasibility_rating": plan.feasibility_rating,
        "confidence_score": plan.initial_confidence,
        "adjusted_confidence": plan.adjusted_confidence,
        "phases": [phase_to_display(phase) for phase in plan.phases],
        "phases_timeline": phases_timeline,
        "key_actions": plan.key_actions,
        "recommendations": plan.recommendations,
        "reasoning": plan.reasoning,
    }


def get_severity_color(severity: str) -> str:
    """Map severity level to hex color code."""
    colors = {
        "critical": "#DC3545",
        "high": "#FF6B6B",
        "medium": "#FFC107",
        "low": "#28A745",
    }
    return colors.get(severity, "#0066CC")


def get_complexity_label(complexity: str) -> str:
    """Map complexity code to readable label with emoji."""
    labels = {
        "easy": "🟢 Easy",
        "moderate": "🟡 Moderate",
        "hard": "🔴 Hard",
    }
    return labels.get(complexity, complexity)


def format_hours(hours: int) -> str:
    """Format hours with appropriate unit (h, weeks, months)."""
    if hours < 100:
        return f"{hours}h"
    elif hours < 1000:
        weeks = hours / 40
        return f"{weeks:.1f}w ({hours}h)"
    else:
        months = hours / 160
        return f"{months:.1f}mo ({hours}h)"


def format_timeline(weeks: float) -> str:
    """Format weeks into readable timeline string."""
    if weeks < 4:
        return f"{weeks:.1f} weeks"
    elif weeks < 52:
        months = weeks / 4.3
        return f"{months:.1f} months ({weeks:.0f}w)"
    else:
        years = weeks / 52
        months = (weeks % 52) / 4.3
        if months > 0:
            return f"{years:.0f}y {months:.1f}mo ({weeks:.0f}w)"
        else:
            return f"{years:.1f} years"


def get_feasibility_emoji(rating: str) -> str:
    """Get emoji for feasibility rating."""
    emojis = {
        "high": "✅",
        "medium": "⚠️",
        "low": "⛔",
        "very_low": "🚫",
    }
    return emojis.get(rating, "❓")


def get_phase_color(phase_number: int) -> str:
    """Get color for phase number."""
    colors = {
        1: "#1976D2",  # Blue
        2: "#7B1FA2",  # Purple
        3: "#F57C00",  # Orange
    }
    return colors.get(phase_number, "#0066CC")


def extract_audit_trail(
    normalized_role: NormalizedRole,
    gap_analysis: SkillGapAnalysis,
    learning_plan: CareerLearningPlan,
) -> List[Dict[str, str]]:
    """
    Extract decision audit trail from all three phases.
    
    Returns list of decision dicts with reasoning.
    """
    decisions = [
        {
            "decision": f"Normalize '{normalized_role.original_input}' to '{normalized_role.normalized_name}'",
            "reasoning": normalized_role.reasoning,
            "confidence": f"{normalized_role.confidence:.0%}",
        },
        {
            "decision": f"Analyze skill gaps for {gap_analysis.target_role}",
            "reasoning": f"Found {len(gap_analysis.all_gaps)} required skills with {len([g for g in gap_analysis.all_gaps if g.gap_severity == 'critical'])} critical gaps",
            "confidence": f"{gap_analysis.confidence_score:.0%}",
        },
        {
            "decision": f"Generate learning timeline ({learning_plan.total_weeks_recommended:.1f}w, {learning_plan.total_hours_required}h)",
            "reasoning": f"Timeline feasibility: {learning_plan.feasibility_rating.upper()} (confidence: {learning_plan.adjusted_confidence:.0%})",
            "confidence": f"{learning_plan.adjusted_confidence:.0%}",
        },
    ]
    
    # Add top recommendations
    for i, rec in enumerate(learning_plan.recommendations[:3], 1):
        decisions.append({
            "decision": f"Recommendation {i}",
            "reasoning": rec,
            "confidence": "",
        })
    
    return decisions
