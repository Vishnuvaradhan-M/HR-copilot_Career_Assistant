"""
Pydantic schemas for Goal-Driven AI (GAG) Career Assistant.

These schemas define the domain model for career planning:
- Input: user's current state + career goal
- Intermediate: normalized roles, skill requirements, gaps
- Output: structured learning plan with timeline & feasibility

All schemas are immutable to ensure deterministic reasoning.
"""

from dataclasses import dataclass
from typing import Optional, List
from enum import Enum
from datetime import date


class ProficiencyLevel(str, Enum):
    """Standard skill proficiency scale."""
    NONE = "none"
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


@dataclass
class Skill:
    """Represents a single skill with proficiency level."""
    name: str  # e.g., "Python", "SQL", "Team Leadership"
    proficiency: ProficiencyLevel
    years_experience: Optional[float] = None  # e.g., 2.5 years

    def __hash__(self):
        return hash((self.name, self.proficiency))


@dataclass
class UserProfile:
    """Current state of a user."""
    name: str
    current_role: str
    years_in_role: float
    total_experience_years: float
    current_skills: List[Skill]
    hours_per_week_available: float  # For learning
    learning_style: str = "balanced"  # Options: "visual", "hands-on", "theoretical", "balanced"


@dataclass
class CareerGoal:
    """User's career transition objective."""
    target_role: str
    reason: Optional[str] = None  # Why they want this transition
    timeline_months: Optional[int] = None  # Desired timeline


@dataclass
class NormalizedRole:
    """Standardized role after disambiguation."""
    original_input: str
    normalized_name: str  # E.g., "Data Scientist", "Senior Software Engineer"
    confidence: float  # 0.0-1.0; high means unambiguous match
    category: str  # E.g., "engineering", "data", "leadership", "design"
    is_promotion: bool = False  # True if lateral/upward move from current role
    reasoning: str = ""  # Explanation of normalization choice


@dataclass
class SkillGap:
    """Identifies a single skill gap (Phase 2 output, UI-optimized)."""
    skill_name: str
    current_level: ProficiencyLevel
    required_level: ProficiencyLevel
    gap_severity: str  # "critical", "high", "medium", "low"
    learning_complexity: str  # "easy", "moderate", "hard"
    must_have: bool  # True if critical to job role, False if nice-to-have
    learning_phase: str  # "foundation", "core", "advanced"
    normalized_gap_score: float  # 0.0-1.0 for UI progress bars
    reasoning: str  # Audit trail explaining gap assessment


@dataclass
class SkillGapAnalysis:
    """Complete skill gap analysis for a user-role pair (Phase 2 output)."""
    user_name: str
    current_role: str
    target_role: str
    normalized_target_role: str  # Canonical form
    total_required_skills: int
    gaps_by_severity: dict  # {"critical": 3, "high": 5, "medium": 2, "low": 1}
    gaps_by_phase: dict  # {"foundation": [...], "core": [...], "advanced": [...]}
    all_gaps: List[SkillGap]  # Flat list of all gaps
    transferable_skills: List[str]  # Skills user already has for this role
    confidence_score: float  # 0.0-1.0 overall feasibility


# ============================================================================
# PHASE 3: LEARNING PLAN & TIMELINE SCHEMAS
# ============================================================================

@dataclass
class LearningTask:
    """Individual learning task with effort estimation (Phase 3)."""
    skill_name: str
    current_level: ProficiencyLevel
    required_level: ProficiencyLevel
    learning_phase: str  # "foundation", "core", "advanced"
    resource_type: str  # "course", "book", "project", "practice", "hands-on"
    estimated_hours: int  # Total hours to complete this task
    effort_hours_per_week: int  # Recommended effort per week (for pacing)
    estimated_weeks: float  # How many weeks at recommended pace
    must_complete: bool  # True if critical, False if nice-to-have
    difficulty: str  # "easy", "moderate", "hard"
    gap_severity: str  # "critical", "high", "medium", "low"
    parallel_with: List[str] = None  # Other skill names that can be learned in parallel
    prerequisites: List[str] = None  # Skills that must be learned first
    reasoning: str = ""  # Audit trail explaining effort estimation


@dataclass
class LearningPhasePlan:
    """Aggregated plan for one learning phase (Phase 3)."""
    phase_name: str  # "Foundation", "Core", "Advanced"
    phase_number: int  # 1, 2, 3
    tasks: List[LearningTask]  # All tasks in this phase
    total_hours: int  # Sum of estimated_hours across tasks
    total_weeks_sequential: float  # If tasks were sequential
    total_weeks_parallel: float  # If max parallelism allowed
    recommended_weeks: float  # Balanced recommendation
    start_week: int  # When to start (1-indexed)
    end_week: int  # When to complete (1-indexed)
    critical_task_count: int  # Count of must_complete tasks
    nice_to_have_count: int  # Count of optional tasks
    key_milestones: List[str]  # Major achievements in this phase


@dataclass
class CareerLearningPlan:
    """Complete learning roadmap from current role to target role (Phase 3 output)."""
    user_name: str
    current_role: str
    target_role: str
    normalized_target_role: str
    
    # Learning structure
    phases: List[LearningPhasePlan]  # Ordered phases: foundation, core, advanced
    all_tasks: List[LearningTask]  # Flat list of all tasks
    
    # Timeline metrics
    total_hours_required: int
    total_weeks_recommended: float  # Realistic timeline given user availability
    total_months_recommended: float  # Months (for easier reading)
    
    # Feasibility
    initial_confidence: float  # From SkillGapAnalysis
    timeline_confidence: float  # 1.0 = achievable, 0.5 = ambitious, 0.3 = very tight
    adjusted_confidence: float  # Geometric mean of initial × timeline
    feasibility_rating: str  # "high", "medium", "low", "very_low"
    
    # Guidance
    key_actions: List[str]  # Top 3-5 immediate next steps
    recommendations: List[str]  # Pacing, parallel tracks, etc.
    reasoning: str = ""  # Audit trail


# Legacy schema (kept for backward compatibility with Phase 1/2)
@dataclass
class LearningPhase:
    """One phase in a multi-phase learning path."""
    phase_number: int  # 1=Foundations, 2=Core, 3=Advanced
    phase_name: str
    duration_weeks: int
    skills_covered: List[str]  # Skill names to learn in this phase
    key_milestones: List[str]  # E.g., ["Complete fundamentals", "Build 2 projects"]
    resources: List[str]  # E.g., ["Online course X", "Book Y", "Practice Z"]
    prerequisite_phases: List[int] = None  # Phase dependencies


@dataclass
class CareerPlan:
    """Complete structured career transition plan."""
    user_name: str
    current_role: str
    target_role: str
    skill_gaps: List[SkillGap]
    phases: List[LearningPhase]
    total_estimated_weeks: int
    feasibility: str  # "high", "medium", "low"
    feasibility_score: float  # 0.0-1.0
    feasibility_reasoning: str
    generated_at: date
    key_actions: List[str]  # Top 3-5 actionable first steps


@dataclass
class CareerAssistantOutput:
    """Complete output bundle from career assistant."""
    plan: CareerPlan
    human_readable_summary: str
    json_serializable: dict  # For API responses
    confidence_indicators: dict  # Detailed confidence scores per component
