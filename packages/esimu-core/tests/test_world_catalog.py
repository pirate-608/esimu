"""Tests for active-theme world catalog loading."""

from esimu_core.world.catalog import WorldCatalog


def test_demo_catalog_normalizes_two_term_world_data() -> None:
    catalog = WorldCatalog("demo-campus")

    majors = catalog.majors()
    assignment = catalog.major_assignment("GEN")
    achievements = catalog.achievements()

    assert majors[0]["abbr"] == "GEN"
    assert majors[0]["name"] == "通识探索"
    assert assignment is not None
    assert assignment["course_plan"]["plan"][0]["courses"][0]["id"] == "intro"
    assert len(catalog.courses_for_semester("GEN", 1)) == 3
    assert len(catalog.courses_for_semester("GEN", 2)) == 3
    assert achievements["first_step"]["name"] == "迈出第一步"
    assert catalog.event_library()[0]["title"] == "社团摊位前"
    assert "校园笑话" in catalog.forum_library()[0]["content"]
