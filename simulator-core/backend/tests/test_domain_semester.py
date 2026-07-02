"""Regression tests for pure semester-domain rules."""

from esimu_core.domain.semester import (
    CourseExamInput,
    calculate_cumulative_gpa,
    calculate_term_gpa,
    calculate_term_totals,
    exam_modifier,
    grade_points_for_score,
    recover_toward_baseline,
    settle_course_exam,
    settle_semester_exam,
)


def test_grade_points_follow_reference_linear_scale() -> None:
    assert grade_points_for_score(100) == 5.0
    assert grade_points_for_score(95) == 4.5
    assert grade_points_for_score(79.3) == 2.93
    assert grade_points_for_score(50) == 0.0


def test_exam_modifier_uses_sanity_and_stress_ranges() -> None:
    assert exam_modifier(85, 55) == 12
    assert exam_modifier(40, 10) == -13
    assert exam_modifier(65, 30) == -3.2


def test_course_settlement_is_deterministic_when_luck_delta_is_supplied() -> None:
    result = settle_course_exam(
        CourseExamInput(id="math", name="Math", credits=4, mastery=80),
        modifier=4,
        luck_delta=1.5,
        fail_threshold=60,
    )
    assert result.final_score == 87.5
    assert result.grade_points == 3.75
    assert result.passed is True


def test_term_and_cumulative_gpa_are_credit_weighted() -> None:
    courses = (
        settle_course_exam(
            CourseExamInput("a", "A", 4, 100),
            modifier=0,
            luck_delta=0,
        ),
        settle_course_exam(
            CourseExamInput("b", "B", 2, 70),
            modifier=0,
            luck_delta=0,
        ),
    )
    points, credits, failed = calculate_term_totals(courses)

    assert credits == 6
    assert failed == 0
    assert calculate_term_gpa(points, credits) == 4.1

    cumulative = calculate_cumulative_gpa(
        {"gpa_points_total": 20, "gpa_credits_total": 5},
        points,
        credits,
        4.1,
    )
    assert cumulative.cgpa == 4.05
    assert cumulative.gpa_points_total == 44.6
    assert cumulative.gpa_credits_total == 11


def test_cumulative_gpa_approximates_legacy_visible_gpa() -> None:
    cumulative = calculate_cumulative_gpa(
        {"gpa": "3.6", "semester_idx": "3"},
        term_points=24,
        term_credits=6,
        term_gpa=4.0,
    )

    assert cumulative.gpa_credits_total == 18
    assert cumulative.gpa_points_total == 67.2
    assert cumulative.cgpa == 3.73


def test_settle_semester_exam_keeps_highest_single_term_gpa() -> None:
    courses = (
        settle_course_exam(CourseExamInput("a", "A", 2, 100), 0, 0),
        settle_course_exam(CourseExamInput("b", "B", 2, 100), 0, 0),
    )

    result = settle_semester_exam(
        courses,
        {"gpa_points_total": 10, "gpa_credits_total": 2},
        previous_highest_gpa=4.8,
    )

    assert result.term_gpa == 5.0
    assert result.cgpa == 5.0
    assert result.failed_count == 0
    assert result.highest_gpa == 5.0


def test_recover_toward_baseline_preserves_high_values() -> None:
    assert recover_toward_baseline("20", baseline=100, minimum=0) == 60
    assert recover_toward_baseline(99, baseline=100, minimum=0) == 100
    assert recover_toward_baseline(120, baseline=100, minimum=0) == 120
    assert recover_toward_baseline("bad", baseline=100, minimum=0) == 100
    assert recover_toward_baseline(-10, baseline=100, minimum=0) == 50

