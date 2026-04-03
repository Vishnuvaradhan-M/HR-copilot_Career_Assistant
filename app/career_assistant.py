"""
Career Assistant: Main module with role normalization and reasoning steps.

This module is COMPLETELY ISOLATED from the HR RAG system.
It does NOT use FAISS, document retrieval, or external APIs.

Architecture:
- Pure functions for each reasoning step
- Immutable schemas (dataclasses)
- Deterministic output given same input
- Every step produces structured intermediate data
- Full audit trail via reasonings strings

Phase 1 Implementation: Role Normalization
- Normalize user input roles to standard canonical names
- Handle synonyms, abbreviations, ambiguity
- Confidence scoring for disambiguation
"""

import re
import sys
import os
from typing import Tuple, List
from difflib import SequenceMatcher

# Add repo root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.schemas.career import (
    NormalizedRole, UserProfile, CareerGoal, SkillGap, SkillGapAnalysis, 
    ProficiencyLevel, LearningTask, LearningPhasePlan, CareerLearningPlan
)
from app.prompts.career_prompts import ROLE_SYNONYMS, STANDARD_ROLES, ROLE_CATEGORIES


def _string_similarity(a: str, b: str) -> float:
    """
    Calculate string similarity using SequenceMatcher (0.0 to 1.0).
    Used for fuzzy matching when synonyms don't match exactly.
    """
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def _normalize_input(role_input: str) -> str:
    """
    Normalize role input string for matching:
    - Strip whitespace
    - Convert to lowercase
    - Remove extra punctuation
    
    Examples:
        "Senior Software Engineer" -> "senior software engineer"
        "Sr. Dev" -> "sr dev"
        "ML/AI Engineer" -> "ml/ai engineer"
    """
    normalized = role_input.strip().lower()
    # Remove common punctuation
    normalized = re.sub(r'[\.\,\-\(\)]+', '', normalized)
    # Collapse multiple spaces
    normalized = re.sub(r'\s+', ' ', normalized)
    return normalized


def _find_exact_synonym_match(normalized_role: str) -> Tuple[str, float]:
    """
    Find exact match in ROLE_SYNONYMS dictionary.
    
    Returns:
        (canonical_name, confidence) where confidence is 1.0 for exact match
    """
    if normalized_role in ROLE_SYNONYMS:
        return ROLE_SYNONYMS[normalized_role], 1.0
    
    # Check if normalized_role is already a standard role
    if normalized_role.replace(" ", "_") in STANDARD_ROLES:
        return normalized_role.replace(" ", "_"), 1.0
    
    return None, 0.0


def _find_fuzzy_match(normalized_role: str) -> Tuple[str, float]:
    """
    Find best fuzzy match using string similarity when exact match fails.
    
    Thresholds:
        >= 0.85: High confidence
        >= 0.70: Medium confidence
        < 0.70: Low confidence (ambiguous)
    
    Returns:
        (canonical_name, confidence)
    """
    best_match = None
    best_score = 0.0
    
    # Search in synonym keys
    for synonym, canonical in ROLE_SYNONYMS.items():
        similarity = _string_similarity(normalized_role, synonym)
        if similarity > best_score:
            best_score = similarity
            best_match = canonical
    
    # Also search in standard role names (with spaces)
    for standard_role in STANDARD_ROLES:
        standard_role_spaced = standard_role.replace("_", " ")
        similarity = _string_similarity(normalized_role, standard_role_spaced)
        if similarity > best_score:
            best_score = similarity
            best_match = standard_role
    
    if best_score >= 0.70:  # Only return if at least 70% similar
        return best_match, best_score
    
    return None, 0.0


def _assess_career_progression(
    current_role: str,
    target_role: str,
    current_category: str,
    target_category: str
) -> bool:
    """
    Determine if target role represents a reasonable career progression.
    
    Rules:
    - Same category = lateral move (acceptable)
    - Engineering -> Leadership = promotion (acceptable)
    - Data -> Engineering = very difficult (flag as unusual)
    - Backwards moves = flag with lower confidence
    
    Returns:
        is_reasonable_progression: bool
    """
    # Engineer -> Staff/Principal = valid promotion
    if "engineer" in current_role and ("staff" in target_role or "principal" in target_role):
        return True
    
    # Engineer -> Engineering Manager = valid promotion
    if "engineer" in current_role and "manager" in target_role:
        return True
    
    # Same category = lateral move
    if current_category == target_category:
        return True
    
    # Data -> Engineering or similar cross-functional = difficult but possible
    # (should lower confidence, but not reject)
    return True  # Accept with caution


def normalize_role(
    input_role: str,
    current_role: str = None,
    user_experience_years: float = 5.0
) -> NormalizedRole:
    """
    Normalize a role title to a standard canonical name.
    
    Process:
    1. Normalize string (lowercase, remove punctuation)
    2. Try exact synonym match (confidence = 1.0)
    3. Try fuzzy match on synonyms (confidence 0.7-0.99)
    4. Assess career progression viability
    5. Return structured NormalizedRole with reasoning
    
    Args:
        input_role: User-provided role title (may be ambiguous)
        current_role: User's current role (for progression assessment)
        user_experience_years: Years of experience (for feasibility)
    
    Returns:
        NormalizedRole with normalized_name, confidence, category, reasoning
    """
    normalized_input = _normalize_input(input_role)
    reasoning_steps = []
    
    # Step 1: Try exact match
    reasoning_steps.append(f"Input normalized to: '{normalized_input}'")
    
    exact_match, exact_confidence = _find_exact_synonym_match(normalized_input)
    if exact_match:
        reasoning_steps.append(f"Exact synonym match found: '{exact_match}'")
        confidence = 1.0
        matched_role = exact_match
    else:
        reasoning_steps.append("No exact synonym match; attempting fuzzy match...")
        fuzzy_match, fuzzy_confidence = _find_fuzzy_match(normalized_input)
        
        if fuzzy_match:
            # Confidence based on string similarity
            if fuzzy_confidence >= 0.90:
                confidence = 0.95  # Very likely match
            elif fuzzy_confidence >= 0.80:
                confidence = 0.80  # Probable match
            else:
                confidence = 0.65  # Ambiguous; user should verify
            
            matched_role = fuzzy_match
            reasoning_steps.append(
                f"Fuzzy match: '{fuzzy_match}' (similarity: {fuzzy_confidence:.2f})"
            )
        else:
            # No reasonable match found
            reasoning_steps.append("No fuzzy match found (all < 0.70 similarity)")
            matched_role = normalized_input.replace(" ", "_")
            confidence = 0.30  # Very low confidence; likely an unknown role
    
    # Step 2: Determine category
    target_category = ROLE_CATEGORIES.get(matched_role, "unknown")
    reasoning_steps.append(f"Role category: '{target_category}'")
    
    # Step 3: Assess progression (if current role provided)
    is_promotion = False
    if current_role:
        current_normalized = _normalize_input(current_role)
        current_canonical, _ = _find_exact_synonym_match(current_normalized)
        if current_canonical:
            current_category = ROLE_CATEGORIES.get(current_canonical, "unknown")
            is_progression = _assess_career_progression(
                current_role=current_canonical,
                target_role=matched_role,
                current_category=current_category,
                target_category=target_category
            )
            
            # Upward move = promotion
            if current_role != matched_role and "senior" in matched_role:
                is_promotion = True
            
            reasoning_steps.append(
                f"Career progression feasible: {is_progression} "
                f"(from '{current_category}' to '{target_category}')"
            )
    
    # Step 4: Adjust confidence based on experience
    # More experienced workers can attempt more ambitious transitions
    if user_experience_years >= 10:
        confidence = min(confidence + 0.1, 1.0)
        reasoning_steps.append(f"Confidence boosted for experienced user (+0.1)")
    elif user_experience_years < 2 and confidence < 0.8:
        confidence = max(confidence - 0.1, 0.1)
        reasoning_steps.append(f"Confidence reduced for junior user (-0.1)")
    
    # Construct result
    return NormalizedRole(
        original_input=input_role,
        normalized_name=matched_role,
        confidence=confidence,
        category=target_category,
        is_promotion=is_promotion,
        reasoning="\n".join(reasoning_steps)
    )


# ============================================================================
# PHASE 2: SKILL GAP ANALYSIS ENGINE
# ============================================================================

def infer_required_skills(normalized_role: str) -> list:
    """
    Infer required skills for a target role.
    
    Process:
    1. Look up role in ROLE_SKILL_REQUIREMENTS
    2. If role not found, return empty list (unknown role)
    3. Convert to list of (skill_name, required_level) tuples
    
    Args:
        normalized_role: Canonical role name (e.g., "data_scientist")
    
    Returns:
        List of (skill_name, required_level_str) tuples
        Empty list if role unknown
    """
    from app.prompts.career_prompts import ROLE_SKILL_REQUIREMENTS
    
    # Try direct lookup first
    if normalized_role in ROLE_SKILL_REQUIREMENTS:
        return ROLE_SKILL_REQUIREMENTS[normalized_role]
    
    # Try with underscores replaced by spaces
    role_with_spaces = normalized_role.replace("_", " ")
    for role_key, skills in ROLE_SKILL_REQUIREMENTS.items():
        if role_key.replace("_", " ") == role_with_spaces:
            return skills
    
    return []  # Unknown role


def _proficiency_to_score(proficiency: str) -> float:
    """
    Convert proficiency level string to numeric score (0.0-1.0).
    Used for gap calculation.
    """
    mapping = {
        "none": 0.0,
        "beginner": 0.25,
        "intermediate": 0.5,
        "advanced": 0.75,
        "expert": 1.0,
    }
    return mapping.get(proficiency.lower(), 0.0)


def _get_user_skill_level(user_skills: list, skill_name: str) -> str:
    """
    Get user's current proficiency level for a skill.
    
    Args:
        user_skills: List of Skill objects from UserProfile
        skill_name: Name of skill to look up
    
    Returns:
        ProficiencyLevel string, defaults to "none" if not found
    """
    for skill in user_skills:
        if skill.name.lower() == skill_name.lower():
            # Handle both enum and string proficiency
            prof = skill.proficiency
            if hasattr(prof, 'value'):
                return prof.value
            return str(prof)
    
    return "none"  # User doesn't have this skill


def _compute_gap_severity(current_score: float, required_score: float) -> str:
    """
    Determine severity of skill gap.
    
    Scoring:
    - Gap 0.0-0.2   = Low (minimal effort)
    - Gap 0.2-0.4   = Medium (moderate effort)
    - Gap 0.4-0.7   = High (significant effort)
    - Gap 0.7-1.0   = Critical (foundational, must-have)
    
    Args:
        current_score: User's proficiency score (0.0-1.0)
        required_score: Required proficiency score (0.0-1.0)
    
    Returns:
        Severity level: "critical", "high", "medium", "low"
    """
    gap = required_score - current_score
    
    if gap < 0:
        return "low"  # User exceeds requirement
    elif gap < 0.2:
        return "low"
    elif gap < 0.4:
        return "medium"
    elif gap < 0.7:
        return "high"
    else:
        return "critical"


def _assign_learning_phase(
    skill_name: str,
    gap_severity: str,
    must_have: bool
) -> str:
    """
    Assign skill to a learning phase (foundation/core/advanced).
    
    Rules:
    1. Critical + must-have skills → foundation phase
    2. High + must-have skills → core phase
    3. Medium/Low + must-have → core (still important)
    4. Nice-to-have (not must-have) → based on skill_criticality mapping
    
    Args:
        skill_name: Name of skill
        gap_severity: "critical", "high", "medium", "low"
        must_have: Whether skill is critical for job function
    
    Returns:
        Phase: "foundation", "core", or "advanced"
    """
    from app.prompts.career_prompts import SKILL_CRITICALITY
    
    # If we have skill criticality metadata, use it
    if skill_name in SKILL_CRITICALITY:
        _, default_phase = SKILL_CRITICALITY[skill_name]
        return default_phase
    
    # Fallback heuristic: use severity + must_have flag
    if must_have:
        if gap_severity == "critical":
            return "foundation"
        elif gap_severity == "high":
            return "core"
        else:
            return "core"
    else:
        # Nice-to-have: put in advanced
        return "advanced"


def compute_skill_gap(
    skill_name: str,
    current_proficiency: str,
    required_proficiency: str,
    user_skills: list,
    must_have: bool = True
) -> "SkillGap":
    """
    Compute a single skill gap with all metrics.
    
    Produces:
    - current_level, required_level
    - gap_severity (critical/high/medium/low)
    - learning_complexity (easy/moderate/hard)
    - normalized_gap_score (0.0-1.0)
    - learning_phase (foundation/core/advanced)
    
    Args:
        skill_name: Name of skill
        current_proficiency: User's current proficiency (from infer or lookup)
        required_proficiency: Required proficiency for role
        user_skills: List of user's Skill objects
        must_have: Whether this is critical (vs nice-to-have)
    
    Returns:
        SkillGap object with all fields populated
    """
    from app.prompts.career_prompts import SKILL_COMPLEXITY
    
    # Convert to scores for gap calculation
    current_score = _proficiency_to_score(current_proficiency)
    required_score = _proficiency_to_score(required_proficiency)
    
    # Compute gap severity
    gap_severity = _compute_gap_severity(current_score, required_score)
    
    # Get learning complexity
    learning_complexity = SKILL_COMPLEXITY.get(skill_name, "moderate")
    
    # Normalized gap score (0.0 = no gap, 1.0 = complete gap)
    gap_diff = max(0, required_score - current_score)
    normalized_gap_score = gap_diff
    
    # Assign learning phase
    learning_phase = _assign_learning_phase(skill_name, gap_severity, must_have)
    
    # Build reasoning
    reasoning_parts = [
        f"Current: {current_proficiency}, Required: {required_proficiency}",
        f"Gap score: {gap_diff:.2f} ({gap_severity} severity)",
        f"Complexity: {learning_complexity}",
        f"Must-have: {must_have}",
        f"Assigned to: {learning_phase} phase",
    ]
    
    return SkillGap(
        skill_name=skill_name,
        current_level=ProficiencyLevel(current_proficiency),
        required_level=ProficiencyLevel(required_proficiency),
        gap_severity=gap_severity,
        learning_complexity=learning_complexity,
        must_have=must_have,
        learning_phase=learning_phase,
        normalized_gap_score=normalized_gap_score,
        reasoning="\n".join(reasoning_parts)
    )


def analyze_skill_gaps(
    user_profile: "UserProfile",
    target_role_normalized: str,
    target_role_original: str = None
) -> "SkillGapAnalysis":
    """
    Complete skill gap analysis for a user targeting a role.
    
    Process:
    1. Infer required skills for target role
    2. For each required skill, compute gap with user's current level
    3. Categorize by severity and phase
    4. Identify transferable skills
    5. Calculate overall confidence
    
    Args:
        user_profile: UserProfile with current_skills list
        target_role_normalized: Canonical role name
        target_role_original: Original input (for metadata)
    
    Returns:
        SkillGapAnalysis with gaps organized by severity/phase
    """
    from app.prompts.career_prompts import SKILL_CRITICALITY
    
    # Step 1: Get required skills for role
    required_skills = infer_required_skills(target_role_normalized)
    
    if not required_skills:
        # Unknown role - return empty analysis
        return SkillGapAnalysis(
            user_name=user_profile.name,
            current_role=user_profile.current_role,
            target_role=target_role_original or target_role_normalized,
            normalized_target_role=target_role_normalized,
            total_required_skills=0,
            gaps_by_severity={},
            gaps_by_phase={},
            all_gaps=[],
            transferable_skills=[],
            confidence_score=0.0
        )
    
    # Step 2: Compute gaps for each required skill
    all_gaps = []
    transferable = []
    severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    phase_gaps = {"foundation": [], "core": [], "advanced": []}
    
    for skill_name, required_level in required_skills:
        # Determine if must-have
        must_have = True
        if skill_name in SKILL_CRITICALITY:
            must_have, _ = SKILL_CRITICALITY[skill_name]
        
        # Get current level
        current_level = _get_user_skill_level(user_profile.current_skills, skill_name)
        
        # Compute gap
        gap = compute_skill_gap(
            skill_name=skill_name,
            current_proficiency=current_level,
            required_proficiency=required_level,
            user_skills=user_profile.current_skills,
            must_have=must_have
        )
        
        all_gaps.append(gap)
        severity_counts[gap.gap_severity] += 1
        phase_gaps[gap.learning_phase].append(gap.skill_name)
        
        # Track transferable (user already has this skill)
        if gap.gap_severity == "low" and current_level != "none":
            transferable.append(skill_name)
    
    # Step 3: Calculate overall confidence
    # Higher confidence = user already has relevant skills
    transferable_ratio = len(transferable) / len(all_gaps) if all_gaps else 0
    critical_count = severity_counts["critical"]
    
    # Confidence scoring:
    # - Start at 0.5 baseline
    # - +0.3 if >30% transferable
    # - -0.2 per critical gap (up to -0.6 max)
    confidence = 0.5 + (0.3 if transferable_ratio > 0.3 else 0)
    confidence -= min(critical_count * 0.2, 0.6)
    confidence = max(0.1, min(confidence, 1.0))  # Clamp to 0.1-1.0
    
    return SkillGapAnalysis(
        user_name=user_profile.name,
        current_role=user_profile.current_role,
        target_role=target_role_original or target_role_normalized,
        normalized_target_role=target_role_normalized,
        total_required_skills=len(all_gaps),
        gaps_by_severity=severity_counts,
        gaps_by_phase=phase_gaps,
        all_gaps=all_gaps,
        transferable_skills=transferable,
        confidence_score=confidence
    )


# ============================================================================
# PHASE 3: LEARNING PLAN & TIMELINE GENERATION
# ============================================================================

def _proficiency_jump_hours(current_level: str, required_level: str) -> int:
    """
    Calculate base hours needed for a proficiency jump.
    
    Maps the jump between two proficiency levels to estimated hours.
    
    Args:
        current_level: Current proficiency (string: "none", "beginner", etc.)
        required_level: Target proficiency
    
    Returns:
        Base hours (before complexity/severity multipliers)
    """
    from app.prompts.career_prompts import PROFICIENCY_JUMP_HOURS
    
    # Map all level transitions
    level_order = ["none", "beginner", "intermediate", "advanced", "expert"]
    
    try:
        current_idx = level_order.index(current_level.lower())
        required_idx = level_order.index(required_level.lower())
    except ValueError:
        return 40  # Default fallback
    
    if required_idx <= current_idx:
        return 0  # User already at or above requirement
    
    # Sum up all jumps
    total_hours = 0
    for i in range(current_idx, required_idx):
        jump_key = f"{level_order[i]}_to_{level_order[i+1]}"
        total_hours += PROFICIENCY_JUMP_HOURS.get(jump_key, 60)
    
    return total_hours


def estimate_effort_hours(
    skill_gap: SkillGap,
    user_availability_hours_per_week: float
) -> tuple:
    """
    Estimate total effort hours for a single skill gap.
    
    Process:
    1. Calculate base hours from proficiency jump
    2. Apply complexity multiplier
    3. Apply severity multiplier
    4. Calculate pacing (weeks needed at recommended effort)
    
    Args:
        skill_gap: SkillGap object with current/required levels
        user_availability_hours_per_week: Hours user can dedicate weekly
    
    Returns:
        (total_hours, effort_per_week, estimated_weeks, reasoning_str)
    """
    from app.prompts.career_prompts import COMPLEXITY_MULTIPLIERS, SEVERITY_MULTIPLIERS, PHASE_INTENSITY
    
    # Step 1: Base hours
    base_hours = _proficiency_jump_hours(
        skill_gap.current_level.value,
        skill_gap.required_level.value
    )
    
    # Step 2: Apply complexity multiplier
    complexity_mult = COMPLEXITY_MULTIPLIERS.get(skill_gap.learning_complexity, 1.5)
    hours_after_complexity = base_hours * complexity_mult
    
    # Step 3: Apply severity multiplier (lowers hours for less critical skills)
    severity_mult = SEVERITY_MULTIPLIERS.get(skill_gap.gap_severity, 0.8)
    total_hours = int(hours_after_complexity * severity_mult)
    
    # Step 4: Calculate weekly effort
    # Use phase intensity to determine recommended % of available hours
    phase_intensity = PHASE_INTENSITY.get(skill_gap.learning_phase, 0.6)
    effort_per_week = max(1, int(user_availability_hours_per_week * phase_intensity))
    
    # Step 5: Estimate weeks
    estimated_weeks = total_hours / effort_per_week if effort_per_week > 0 else 999
    
    # Build reasoning
    reasoning_parts = [
        f"Base hours: {base_hours}h (from proficiency jump)",
        f"After complexity ({skill_gap.learning_complexity}): {int(hours_after_complexity)}h × {complexity_mult}",
        f"After severity ({skill_gap.gap_severity}): {total_hours}h × {severity_mult}",
        f"Weekly effort ({skill_gap.learning_phase}): {effort_per_week}h/week @ {phase_intensity*100:.0f}% availability",
        f"Estimated timeline: {estimated_weeks:.1f} weeks",
    ]
    
    return total_hours, effort_per_week, estimated_weeks, "\n".join(reasoning_parts)


def build_learning_tasks(
    skill_gap_analysis: SkillGapAnalysis,
    user_profile: UserProfile
) -> List[LearningTask]:
    """
    Convert SkillGapAnalysis into individual LearningTask objects.
    
    For each skill gap, creates a task with:
    - Effort estimation
    - Resource type recommendation
    - Pacing guidance
    - Reasoning trail
    - Proficiency-based reduction (if user has relevant skills)
    
    Args:
        skill_gap_analysis: Output from analyze_skill_gaps()
        user_profile: UserProfile with availability hours
    
    Returns:
        List of LearningTask objects (ordered by phase, then severity)
    """
    from app.prompts.career_prompts import RESOURCE_TYPE_MAPPING
    import math
    
    tasks = []
    
    for skill_gap in skill_gap_analysis.all_gaps:
        # Estimate effort
        total_hours, effort_per_week, estimated_weeks, effort_reasoning = estimate_effort_hours(
            skill_gap,
            user_profile.hours_per_week_available
        )
        
        # Apply proficiency-based reduction
        user_skill_level = _get_user_skill_level(user_profile.current_skills, skill_gap.skill_name)
        proficiency_reduction_factor = 1.0
        
        if user_skill_level == "beginner":
            proficiency_reduction_factor = 0.7
        elif user_skill_level == "intermediate":
            proficiency_reduction_factor = 0.4
        elif user_skill_level == "advanced":
            proficiency_reduction_factor = 0.1
        # "none" stays at 1.0 (100% of full hours)
        
        # Apply reduction
        adjusted_hours = int(total_hours * proficiency_reduction_factor)
        
        # Recalculate weeks based on user's availability
        if user_profile.hours_per_week_available > 0:
            adjusted_weeks = math.ceil(adjusted_hours / user_profile.hours_per_week_available)
        else:
            adjusted_weeks = 999
        
        # Update reasoning with proficiency adjustment
        adjusted_reasoning = effort_reasoning + f"\n[Proficiency adjustment: {user_skill_level} proficiency → {proficiency_reduction_factor*100:.0f}% of base hours]"
        
        # Determine resource type
        resource_key = (skill_gap.gap_severity, skill_gap.learning_complexity)
        resource_type = RESOURCE_TYPE_MAPPING.get(resource_key, "course")
        
        # Create task
        task = LearningTask(
            skill_name=skill_gap.skill_name,
            current_level=skill_gap.current_level,
            required_level=skill_gap.required_level,
            learning_phase=skill_gap.learning_phase,
            resource_type=resource_type,
            estimated_hours=adjusted_hours,
            effort_hours_per_week=effort_per_week,
            estimated_weeks=adjusted_weeks,
            must_complete=skill_gap.must_have,
            difficulty=skill_gap.learning_complexity,
            gap_severity=skill_gap.gap_severity,
            parallel_with=None,  # Filled in later
            prerequisites=None,  # Filled in later
            reasoning=adjusted_reasoning
        )
        
        tasks.append(task)
    
    # Sort by phase (foundation → core → advanced), then by severity
    phase_order = {"foundation": 0, "core": 1, "advanced": 2}
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    
    tasks.sort(key=lambda t: (
        phase_order.get(t.learning_phase, 9),
        severity_order.get(t.gap_severity, 9)
    ))
    
    return tasks


def group_tasks_by_phase(tasks: List[LearningTask]) -> dict:
    """
    Group tasks into Foundation/Core/Advanced phases.
    
    Returns:
        Dict mapping phase_name → List[LearningTask]
    """
    phases = {"foundation": [], "core": [], "advanced": []}
    
    for task in tasks:
        if task.learning_phase in phases:
            phases[task.learning_phase].append(task)
    
    return phases


def generate_learning_timeline(
    skill_gap_analysis: SkillGapAnalysis,
    user_profile: UserProfile
) -> CareerLearningPlan:
    """
    Main orchestrator: Convert SkillGapAnalysis into a complete CareerLearningPlan.
    
    Process:
    1. Build individual learning tasks
    2. Group by phase
    3. Calculate timeline metrics
    4. Assess feasibility
    5. Generate guidance
    
    Args:
        skill_gap_analysis: From analyze_skill_gaps()
        user_profile: User's availability, learning style
    
    Returns:
        CareerLearningPlan with all timeline & feasibility info
    """
    # Step 1: Build tasks
    tasks = build_learning_tasks(skill_gap_analysis, user_profile)
    
    # Step 2: Group by phase
    tasks_by_phase = group_tasks_by_phase(tasks)
    
    # Step 3: Create LearningPhasePlan for each phase
    phase_plans = []
    
    for phase_num, (phase_name_lower, phase_tasks) in enumerate([
        ("foundation", tasks_by_phase["foundation"]),
        ("core", tasks_by_phase["core"]),
        ("advanced", tasks_by_phase["advanced"])
    ], start=1):
        phase_name = phase_name_lower.capitalize()
        
        if not phase_tasks:
            continue  # Skip empty phases
        
        # Calculate totals
        total_hours = sum(t.estimated_hours for t in phase_tasks)
        critical_count = sum(1 for t in phase_tasks if t.must_complete)
        nice_to_have_count = len(phase_tasks) - critical_count
        
        # Timeline calculations
        total_weeks_sequential = sum(t.estimated_weeks for t in phase_tasks)
        
        # Parallel: max of all task weeks (they can overlap)
        max_weeks = max((t.estimated_weeks for t in phase_tasks), default=0)
        total_weeks_parallel = max_weeks
        
        # Recommended: middle ground
        recommended_weeks = (total_weeks_sequential + total_weeks_parallel * 2) / 3
        
        # Phase timing
        start_week = 1 if phase_num == 1 else phase_plans[-1].end_week + 1
        end_week = int(start_week + recommended_weeks)
        
        # Milestones
        milestones = []
        if phase_name_lower == "foundation":
            milestones = ["Complete foundational concepts", "Practice with simple exercises"]
        elif phase_name_lower == "core":
            milestones = ["Build confidence with core skills", "Complete practical projects"]
        else:
            milestones = ["Deepen specialization", "Tackle advanced challenges"]
        
        phase_plan = LearningPhasePlan(
            phase_name=phase_name,
            phase_number=phase_num,
            tasks=phase_tasks,
            total_hours=total_hours,
            total_weeks_sequential=total_weeks_sequential,
            total_weeks_parallel=total_weeks_parallel,
            recommended_weeks=recommended_weeks,
            start_week=start_week,
            end_week=end_week,
            critical_task_count=critical_count,
            nice_to_have_count=nice_to_have_count,
            key_milestones=milestones
        )
        
        phase_plans.append(phase_plan)
    
    # Step 4: Calculate overall timeline
    total_hours = sum(p.total_hours for p in phase_plans)
    
    # Overall timeline: foundation sequential, then core+advanced can overlap
    if len(phase_plans) >= 1:
        timeline_weeks = phase_plans[0].recommended_weeks  # Foundation
        if len(phase_plans) >= 2:
            timeline_weeks += max(p.recommended_weeks for p in phase_plans[1:])  # Max of remaining
    else:
        timeline_weeks = 0
    
    timeline_months = timeline_weeks / 4.33  # Convert to months
    
    # Step 5: Assess feasibility
    # Timeline confidence: based on how realistic the timeline is given availability
    hours_per_week_needed = total_hours / timeline_weeks if timeline_weeks > 0 else 999
    hours_available = user_profile.hours_per_week_available
    
    if hours_per_week_needed <= hours_available * 0.7:
        timeline_confidence = 1.0  # Comfortable pace
    elif hours_per_week_needed <= hours_available:
        timeline_confidence = 0.8  # Tight but doable
    elif hours_per_week_needed <= hours_available * 1.5:
        timeline_confidence = 0.5  # Ambitious, requires focus
    else:
        timeline_confidence = 0.3  # Very tight, risky
    
    # Adjusted confidence: geometric mean
    adjusted_confidence = (skill_gap_analysis.confidence_score * timeline_confidence) ** 0.5
    
    # Feasibility rating based on total weeks
    if timeline_weeks <= 12:
        feasibility_rating = "Achievable"
    elif timeline_weeks <= 26:
        feasibility_rating = "Moderate commitment"
    elif timeline_weeks <= 52:
        feasibility_rating = "Long-term plan"
    else:
        feasibility_rating = "Extended journey"
    
    # Step 6: Generate guidance
    key_actions = [
        f"Start with {tasks_by_phase['foundation'][0].skill_name} fundamentals" if tasks_by_phase['foundation'] else "Begin core skills",
        "Schedule consistent weekly learning blocks",
        "Combine courses with hands-on projects"
    ]
    
    recommendations = []
    if timeline_confidence <= 0.5:
        recommendations.append("Timeline is ambitious - consider extending or reducing scope")
    if sum(1 for t in tasks if t.must_complete) > 5:
        recommendations.append("Many critical skills to learn - prioritize foundation phase")
    if user_profile.hours_per_week_available < 5:
        recommendations.append("Limited weekly availability - extend timeline accordingly")
    
    reasoning_parts = [
        f"Total effort: {total_hours} hours across {len(tasks)} skills",
        f"Timeline: {timeline_weeks:.1f} weeks ({timeline_months:.1f} months) at {hours_per_week_needed:.1f}h/week",
        f"User availability: {user_profile.hours_per_week_available}h/week",
        f"Timeline confidence: {timeline_confidence:.2f}",
        f"Initial confidence (from gaps): {skill_gap_analysis.confidence_score:.2f}",
        f"Adjusted feasibility: {adjusted_confidence:.2f} → {feasibility_rating}",
    ]
    
    return CareerLearningPlan(
        user_name=user_profile.name,
        current_role=user_profile.current_role,
        target_role=skill_gap_analysis.target_role,
        normalized_target_role=skill_gap_analysis.normalized_target_role,
        phases=phase_plans,
        all_tasks=tasks,
        total_hours_required=total_hours,
        total_weeks_recommended=timeline_weeks,
        total_months_recommended=timeline_months,
        initial_confidence=skill_gap_analysis.confidence_score,
        timeline_confidence=timeline_confidence,
        adjusted_confidence=adjusted_confidence,
        feasibility_rating=feasibility_rating,
        key_actions=key_actions,
        recommendations=recommendations,
        reasoning="\n".join(reasoning_parts)
    )


# ============================================================================
# PUBLIC TESTING INTERFACE (Phase 1, 2 & 3)
# ============================================================================

if __name__ == "__main__":
    """
    Test of role normalization (Phase 1) and skill gap analysis (Phase 2).
    """
    print("=" * 80)
    print("CAREER ASSISTANT - PHASE 2: SKILL GAP ANALYSIS TEST")
    print("=" * 80)
    
    # Test case: Software Engineer wants to become Data Scientist
    from app.schemas.career import Skill
    
    user = UserProfile(
        name="Alice Chen",
        current_role="Software Engineer",
        years_in_role=3,
        total_experience_years=5,
        current_skills=[
            Skill("Python", "advanced", 3),
            Skill("SQL", "intermediate", 2),
            Skill("Git", "advanced", 3),
            Skill("Testing", "intermediate", 2),
            Skill("Communication", "intermediate", 2),
        ],
        hours_per_week_available=10,
        learning_style="balanced"
    )
    
    goal = CareerGoal(
        target_role="Data Scientist",
        reason="Want to work with data insights",
        timeline_months=12
    )
    
    # Phase 1: Normalize role
    print(f"\n{'─' * 80}")
    print("PHASE 1: ROLE NORMALIZATION")
    print(f"{'─' * 80}")
    
    normalized = normalize_role(goal.target_role, user.current_role, user.total_experience_years)
    print(f"Input: {normalized.original_input}")
    print(f"Normalized: {normalized.normalized_name}")
    print(f"Category: {normalized.category}")
    print(f"Confidence: {normalized.confidence:.2f}")
    print(f"\nReasoning:")
    for line in normalized.reasoning.split("\n"):
        print(f"  • {line}")
    
    # Phase 2: Skill gap analysis
    print(f"\n{'─' * 80}")
    print("PHASE 2: SKILL GAP ANALYSIS")
    print(f"{'─' * 80}")
    
    gap_analysis = analyze_skill_gaps(user, normalized.normalized_name, goal.target_role)
    
    print(f"\nUser: {gap_analysis.user_name}")
    print(f"Current Role: {gap_analysis.current_role}")
    print(f"Target Role: {gap_analysis.target_role}")
    print(f"Total Required Skills: {gap_analysis.total_required_skills}")
    print(f"Overall Confidence Score: {gap_analysis.confidence_score:.2f}")
    
    print(f"\nGaps by Severity:")
    for severity, count in gap_analysis.gaps_by_severity.items():
        print(f"  • {severity.upper()}: {count}")
    
    print(f"\nTransferable Skills (user already has):")
    for skill in gap_analysis.transferable_skills:
        print(f"  ✓ {skill}")
    if not gap_analysis.transferable_skills:
        print("  (none)")
    
    print(f"\nSkill Gaps by Learning Phase:")
    print(f"\n  FOUNDATION PHASE:")
    foundation_gaps = [g for g in gap_analysis.all_gaps if g.learning_phase == "foundation"]
    if foundation_gaps:
        for gap in foundation_gaps:
            print(f"    • {gap.skill_name}")
            print(f"      Current: {gap.current_level.value} → Required: {gap.required_level.value}")
            print(f"      Severity: {gap.gap_severity} | Complexity: {gap.learning_complexity}")
            print(f"      Gap Score: {gap.normalized_gap_score:.2f}")
    else:
        print("    (no foundation skills needed)")
    
    print(f"\n  CORE PHASE:")
    core_gaps = [g for g in gap_analysis.all_gaps if g.learning_phase == "core"]
    if core_gaps:
        for gap in core_gaps:
            print(f"    • {gap.skill_name}")
            print(f"      Current: {gap.current_level.value} → Required: {gap.required_level.value}")
            print(f"      Severity: {gap.gap_severity} | Complexity: {gap.learning_complexity}")
            print(f"      Gap Score: {gap.normalized_gap_score:.2f}")
    else:
        print("    (no core skills needed)")
    
    print(f"\n  ADVANCED PHASE:")
    advanced_gaps = [g for g in gap_analysis.all_gaps if g.learning_phase == "advanced"]
    if advanced_gaps:
        for gap in advanced_gaps:
            print(f"    • {gap.skill_name}")
            print(f"      Current: {gap.current_level.value} → Required: {gap.required_level.value}")
            print(f"      Severity: {gap.gap_severity} | Complexity: {gap.learning_complexity}")
            print(f"      Gap Score: {gap.normalized_gap_score:.2f}")
    else:
        print("    (no advanced skills needed)")
    
    # Phase 3: Learning Timeline
    print(f"\n{'─' * 80}")
    print("PHASE 3: LEARNING TIMELINE & PLAN")
    print(f"{'─' * 80}")
    
    learning_plan = generate_learning_timeline(gap_analysis, user)
    
    print(f"\nCareer Transition Plan")
    print(f"From: {learning_plan.current_role} → To: {learning_plan.target_role}")
    print(f"\nTimeline Estimate:")
    print(f"  • Total hours required: {learning_plan.total_hours_required}h")
    print(f"  • Recommended duration: {learning_plan.total_weeks_recommended:.1f} weeks ({learning_plan.total_months_recommended:.1f} months)")
    print(f"  • At pace: ~{learning_plan.total_hours_required / learning_plan.total_weeks_recommended:.1f}h/week")
    
    print(f"\nFeasibility Assessment:")
    print(f"  • Initial confidence (from gaps): {learning_plan.initial_confidence:.2f}")
    print(f"  • Timeline confidence: {learning_plan.timeline_confidence:.2f}")
    print(f"  • Adjusted feasibility: {learning_plan.adjusted_confidence:.2f}")
    print(f"  • Rating: {learning_plan.feasibility_rating.upper()}")
    
    print(f"\nLearning Phases:")
    for phase in learning_plan.phases:
        print(f"\n  {phase.phase_number}. {phase.phase_name.upper()} (Weeks {phase.start_week}-{phase.end_week})")
        print(f"     Total: {phase.total_hours}h | Recommended: {phase.recommended_weeks:.1f} weeks")
        print(f"     Critical tasks: {phase.critical_task_count} | Optional: {phase.nice_to_have_count}")
        print(f"     Tasks:")
        for task in phase.tasks:
            print(f"       • {task.skill_name}")
            print(f"         {task.current_level.value} → {task.required_level.value} | {task.estimated_hours}h ({task.estimated_weeks:.1f}w)")
            print(f"         Resource: {task.resource_type} | Effort: {task.effort_hours_per_week}h/week")
    
    print(f"\nKey Actions:")
    for i, action in enumerate(learning_plan.key_actions, 1):
        print(f"  {i}. {action}")
    
    if learning_plan.recommendations:
        print(f"\nRecommendations:")
        for rec in learning_plan.recommendations:
            print(f"  • {rec}")
    
    print(f"\n{'─' * 80}")
    print("END OF TEST")
    print(f"{'─' * 80}\n")
