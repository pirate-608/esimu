"""Semester, exam, GPA, and period-transition domain rules.

Copyright (c) 2026 pirate-608. Licensed under the MIT License.

The functions in this module are intentionally pure. They do not read Redis,
database rows, world files, or random state. Application adapters pass in the
already-resolved configuration and random deltas, making the rules reusable by
different simulator themes and easy to regression test.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping


@dataclass(frozen=True)
class CourseExamInput:
    """Input data required to settle one course in a final exam."""

    id: str
    name: str
    credits: float
    mastery: float


@dataclass(frozen=True)
class CourseExamResult:
    """Settled score and GPA contribution for one course."""

    id: str
    name: str
    credits: float
    mastery: float
    final_score: float
    grade_points: float
    passed: bool


@dataclass(frozen=True)
class CumulativeGpaResult:
    """Updated cumulative GPA and exact weighted totals."""

    cgpa: float
    gpa_points_total: float
    gpa_credits_total: float


@dataclass(frozen=True)
class SemesterExamResult:
    """Aggregate final-exam result for one academic period."""

    courses: tuple[CourseExamResult, ...]
    term_gpa: float
    cgpa: float
    gpa_points_total: float
    gpa_credits_total: float
    failed_count: int
    highest_gpa: float


def safe_float(value: Any, default: float = 0.0) -> float:
    """Convert a loose persisted value to float with a fallback."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def safe_int(value: Any, default: int = 0) -> int:
    """Convert a loose persisted value to int with a fallback."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def exam_modifier(
    sanity: float,
    stress: float,
    sanity_config: Mapping[str, float] | None = None,
    stress_config: Mapping[str, float] | None = None,
) -> float:
    """Return the final-exam score adjustment from sanity and stress.

    Args:
        sanity: Effective sanity stat used for the exam.
        stress: Effective stress stat used for the exam.
        sanity_config: Theme/balance values for sanity slopes and bonus.
        stress_config: Theme/balance values for stress range bonuses.

    Returns:
        Additive score modifier. This mirrors the ZJU reference rules while
        making every magic number externally configurable.
    """
    sanity_cfg = sanity_config or {}
    stress_cfg = stress_config or {}
    low_slope = sanity_cfg.get("low_slope", 0.3)
    high_slope = sanity_cfg.get("high_slope", 0.12)
    excellent_bonus = sanity_cfg.get("excellent_bonus", 6)

    if sanity < 50:
        sanity_bonus = (sanity - 50) * low_slope
    elif sanity >= 80:
        sanity_bonus = excellent_bonus
    elif sanity > 50:
        sanity_bonus = (sanity - 50) * high_slope
    else:
        sanity_bonus = 0

    optimal_bonus = stress_cfg.get("optimal_bonus", 6)
    suboptimal_penalty = stress_cfg.get("suboptimal_penalty", -5)
    extreme_penalty = stress_cfg.get("extreme_penalty", -10)

    if 40 <= stress <= 70:
        stress_bonus = optimal_bonus
    elif 20 <= stress < 40 or 70 < stress <= 90:
        stress_bonus = suboptimal_penalty
    else:
        stress_bonus = extreme_penalty

    return sanity_bonus + stress_bonus


def final_score_from_mastery(
    mastery: float,
    modifier: float,
    luck_delta: float,
    base_offset: float = 10.0,
    mastery_weight: float = 0.9,
) -> float:
    """Calculate the clamped final-exam score for one course."""
    score = mastery * mastery_weight + modifier + luck_delta + base_offset
    return max(0.0, min(100.0, score))


def grade_points_for_score(score: float) -> float:
    """Convert a 0-100 exam score to the reference 5-point grade scale."""
    return max(0.0, round(score / 10 - 5, 2))


def settle_course_exam(
    course: CourseExamInput,
    modifier: float,
    luck_delta: float,
    fail_threshold: float = 60.0,
) -> CourseExamResult:
    """Settle one course result using resolved balance and random inputs."""
    final_score = final_score_from_mastery(course.mastery, modifier, luck_delta)
    grade_points = grade_points_for_score(final_score)
    return CourseExamResult(
        id=course.id,
        name=course.name,
        credits=course.credits,
        mastery=course.mastery,
        final_score=round(final_score, 1),
        grade_points=round(grade_points, 2),
        passed=final_score >= fail_threshold,
    )


def calculate_term_totals(
    courses: Iterable[CourseExamResult],
) -> tuple[float, float, int]:
    """Return weighted term points, term credits, and failed course count."""
    term_points = 0.0
    term_credits = 0.0
    failed_count = 0
    for course in courses:
        term_credits += course.credits
        term_points += course.grade_points * course.credits
        if not course.passed:
            failed_count += 1
    return term_points, term_credits, failed_count


def calculate_term_gpa(term_points: float, term_credits: float) -> float:
    """Calculate a rounded credit-weighted term GPA."""
    if term_credits <= 0:
        return 0.0
    return round(term_points / term_credits, 2)


def calculate_cumulative_gpa(
    stats: Mapping[str, Any],
    term_points: float,
    term_credits: float,
    term_gpa: float,
) -> CumulativeGpaResult:
    """Return cumulative GPA and updated weighted totals.

    New saves should carry exact weighted totals. Legacy saves may only have a
    visible GPA, so this keeps the ZJU reference fallback: approximate prior
    totals by treating the visible GPA as the previous cumulative GPA across
    completed terms.
    """
    previous_points = safe_float(stats.get("gpa_points_total"))
    previous_credits = safe_float(stats.get("gpa_credits_total"))

    if previous_credits <= 0 and term_credits > 0:
        previous_gpa = safe_float(stats.get("gpa"))
        completed_terms = max(0, safe_int(stats.get("semester_idx"), 1) - 1)
        if previous_gpa > 0 and completed_terms > 0:
            previous_credits = term_credits * completed_terms
            previous_points = previous_gpa * previous_credits

    cumulative_points = previous_points + term_points
    cumulative_credits = previous_credits + term_credits
    if cumulative_credits <= 0:
        return CumulativeGpaResult(term_gpa, cumulative_points, cumulative_credits)
    cumulative_gpa = round(cumulative_points / cumulative_credits, 2)
    return CumulativeGpaResult(
        cumulative_gpa,
        cumulative_points,
        cumulative_credits,
    )


def settle_semester_exam(
    courses: Iterable[CourseExamResult],
    stats: Mapping[str, Any],
    previous_highest_gpa: float = 0.0,
) -> SemesterExamResult:
    """Aggregate settled courses into term and cumulative GPA values."""
    course_results = tuple(courses)
    term_points, term_credits, failed_count = calculate_term_totals(course_results)
    term_gpa = calculate_term_gpa(term_points, term_credits)
    cumulative = calculate_cumulative_gpa(stats, term_points, term_credits, term_gpa)
    highest_gpa = max(previous_highest_gpa, term_gpa)
    return SemesterExamResult(
        courses=course_results,
        term_gpa=term_gpa,
        cgpa=cumulative.cgpa,
        gpa_points_total=cumulative.gpa_points_total,
        gpa_credits_total=cumulative.gpa_credits_total,
        failed_count=failed_count,
        highest_gpa=round(highest_gpa, 2),
    )


def recover_toward_baseline(
    current_value: Any,
    baseline: int,
    minimum: int = 0,
) -> int:
    """Recover a period-transition stat halfway toward its baseline.

    Values already at or above the baseline are preserved. Lower values recover
    with a ceiling half-step, matching the reference new-semester energy rule.
    """
    try:
        value = int(current_value)
    except (TypeError, ValueError):
        return baseline
    if value >= baseline:
        return value
    value = max(minimum, value)
    return min(baseline, (baseline + value + 1) // 2)

