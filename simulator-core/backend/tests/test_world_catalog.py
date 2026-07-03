"""Tests for active-theme world catalog loading."""

from esimu_core.world.catalog import WorldCatalog


def test_zju_catalog_flattens_grouped_majors_and_course_plan() -> None:
    catalog = WorldCatalog("zju")

    majors = catalog.majors()
    assignment = catalog.major_assignment("CS")

    assert any(major["abbr"] == "CS" for major in majors)
    assert assignment is not None
    assert assignment["major_info"]["name"] == "计算机科学与技术"
    assert assignment["initial_courses"]
    assert catalog.courses_for_semester("CS", 2)
    assert catalog.achievements()
    assert catalog.event_library()
    assert catalog.forum_library()


def test_demo_catalog_normalizes_flat_majors_courses_and_achievements() -> None:
    catalog = WorldCatalog("demo-campus")

    majors = catalog.majors()
    assignment = catalog.major_assignment("GEN")
    achievements = catalog.achievements()

    assert majors == [
        {
            "id": "GEN",
            "name": "通识探索",
            "desc": "用于验证框架的最小专业。",
            "category": "demo",
            "difficulty": 1.0,
            "iq_bonus": 0,
            "abbr": "GEN",
            "iq_buff": 0,
            "stress_base": 0,
        }
    ]
    assert assignment is not None
    assert assignment["course_plan"]["plan"][0]["courses"][0]["id"] == "intro"
    assert len(catalog.courses_for_semester("GEN", 1)) == 3
    assert catalog.courses_for_semester("GEN", 2) == []
    assert achievements["first_step"]["name"] == "迈出第一步"
    assert catalog.event_library()[0]["title"] == "社团摊位前"
    assert "校园笑话" in catalog.forum_library()[0]["content"]
