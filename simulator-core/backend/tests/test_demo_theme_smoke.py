"""Smoke tests for the minimal demo-campus theme."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import textwrap
from pathlib import Path


def test_demo_campus_theme_loads_world_and_runtime_payloads() -> None:
    """Verify a fresh process can boot core loaders with demo-campus selected."""
    backend_root = Path(__file__).resolve().parents[1]
    lab_root = backend_root.parents[1]
    env = os.environ.copy()
    env["SIMULATOR_LAB_ROOT"] = str(lab_root)
    env["SIMULATOR_THEME"] = "demo-campus"
    env["PYTHONPATH"] = (
        str(backend_root)
        if not env.get("PYTHONPATH")
        else f"{backend_root}{os.pathsep}{env['PYTHONPATH']}"
    )
    code = textwrap.dedent(
        r"""
        import json
        from pathlib import Path

        from esimu_core.runtime.snapshot import (
            build_init_payload_from_snapshot,
            build_tick_payload_from_snapshot,
        )
        from esimu_core.runtime.state import RuntimeSnapshot
        from esimu_core.world.balance import GameBalance
        from esimu_core.world.items import ItemCatalog
        from esimu_core.world.prompts import ThemePrompts
        from esimu_core.world.stat_definitions import StatDefinitions
        from esimu_core.world.story import ThemeStory
        from esimu_core.world.theme import ThemeManifest
        from esimu_core.world.theme_paths import active_theme_id, world_dir

        world = world_dir()
        majors = json.loads((world / "majors.json").read_text(encoding="utf-8"))
        course_path = world / "courses" / f"{majors[0]['id']}.json"
        courses = json.loads(course_path.read_text(encoding="utf-8"))

        theme = ThemeManifest().config
        story = ThemeStory().config
        prompts = ThemePrompts().config
        stats = StatDefinitions()
        balance = GameBalance()
        items = ItemCatalog()

        runtime_stats = stats.default_stats()
        runtime_stats.update({"elapsed_game_time": 0, "semester_idx": 0})
        course_mastery = {course["id"]: 0.0 for course in courses}
        course_states = {course["id"]: 0 for course in courses}
        snapshot = RuntimeSnapshot.from_mappings(
            stats=runtime_stats,
            courses=course_mastery,
            course_states=course_states,
            relax_cooldowns={},
            semester_duration=balance.get_semester_duration(0),
            dingtalk_state={"contacts": []},
            items_state=items.state_payload({"owned": []}),
        )

        tick = build_tick_payload_from_snapshot(snapshot)
        init = build_init_payload_from_snapshot(snapshot)
        print(json.dumps({
            "theme": active_theme_id(),
            "display": theme.display_name,
            "forum": theme.terms["forum"],
            "messenger": theme.terms["messenger"],
            "story": story.prologue.diary_title,
            "prompt": prompts.campus_context,
            "major": majors[0]["id"],
            "course_count": len(courses),
            "item_count": len(items.public_items),
            "tick_course_count": len(tick["courses"]),
            "init_has_items": "items_state" in init,
        }, ensure_ascii=False))
        """
    )

    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=backend_root,
        env=env,
        text=True,
        capture_output=True,
        check=True,
    )
    payload = json.loads(result.stdout)

    assert payload == {
        "theme": "demo-campus",
        "display": "Demo Campus Simulator",
        "forum": "星桥论坛",
        "messenger": "校内信",
        "story": "湖边手记",
        "prompt": "星桥学院校园",
        "major": "GEN",
        "course_count": 3,
        "item_count": 2,
        "tick_course_count": 3,
        "init_has_items": True,
    }
