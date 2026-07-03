"""Fresh-process reference backend smoke for the demo-campus theme."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import textwrap
from pathlib import Path


def test_demo_campus_drives_reference_backend_minimal_startup() -> None:
    """Run a minimal reference startup path with demo-campus selected first."""
    backend_root = Path(__file__).resolve().parents[2]
    lab_root = backend_root.parents[2]
    core_root = lab_root / "simulator-core" / "backend"
    env = os.environ.copy()
    env["SIMULATOR_LAB_ROOT"] = str(lab_root)
    env["SIMULATOR_THEME"] = "demo-campus"
    env["PYTHONPATH"] = (
        os.pathsep.join([str(backend_root), str(core_root)])
        if not env.get("PYTHONPATH")
        else os.pathsep.join([str(backend_root), str(core_root), env["PYTHONPATH"]])
    )
    code = textwrap.dedent(
        r"""
        import asyncio
        import json

        from app.api.auth import get_majors
        from app.content.event_library import pick_cc98_post, pick_random_event
        from app.game.engine import GameEngine
        from app.schemas.dingtalk import DingTalkState
        from app.schemas.game_state import GameStateSnapshot
        from app.services.game_service import GameService
        from app.services.world_service import WorldService
        from esimu_core.world.items import items


        class MemoryRepo:
            def __init__(self):
                self.stats = {}
                self.courses = {}
                self.states = {}
                self.achievements = []
                self.items_state = {"version": 1, "owned": [], "updated_at": 0}

            async def set_game_data(
                self,
                stats=None,
                courses=None,
                states=None,
                achievements=None,
            ):
                self.stats = dict(stats or {})
                self.courses = dict(courses or {})
                self.states = dict(states or {})
                self.achievements = list(achievements or [])

            async def get_snapshot(self):
                return GameStateSnapshot.from_redis_data(
                    self.stats,
                    self.courses,
                    self.states,
                    self.achievements,
                )

            async def get_items_state(self):
                return dict(self.items_state)

            async def get_dingtalk_state(self):
                return DingTalkState()

            async def get_cooldown_timestamp(self, action):
                del action
                return None


        async def main():
            majors = await get_majors()
            repo = MemoryRepo()
            world = WorldService()
            service = GameService("demo-user", repo, world)
            assigned = await service.assign_major_and_init(
                "GEN",
                stat_overrides={"iq": 100, "eq": 100, "luck": 50, "charm": 50},
                username="demo-player",
            )
            engine = GameEngine(
                "demo-user",
                repo=repo,
                save_service=None,
                game_service=service,
            )
            emitted = []

            async def capture(*args):
                emitted.append(args)

            engine.emit = capture
            await engine._emit_current_init()
            await engine._push_update("demo tick")
            achievements = engine._load_achievement_config()
            event = pick_random_event(sanity=100, stress=0)
            post = pick_cc98_post(effect="positive", trigger="校园梗")

            print(json.dumps({
                "major_count": len(majors),
                "major_abbr": majors[0].abbr,
                "assigned_major": assigned["major"],
                "assigned_course": assigned["courses"][0]["id"],
                "initial_gold": repo.stats["gold"],
                "item_ids": [item["id"] for item in items.public_items],
                "achievement": achievements["first_step"]["name"],
                "event": event["title"] if event else None,
                "forum": post,
                "emitted_types": [entry[0] for entry in emitted],
                "init_course_keys": sorted(emitted[0][1]["courses"].keys()),
                "tick_course_keys": sorted(emitted[1][1]["courses"].keys()),
                "tick_message": emitted[1][2],
            }, ensure_ascii=False))

        asyncio.run(main())
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

    assert payload["major_count"] == 1
    assert payload["major_abbr"] == "GEN"
    assert payload["assigned_major"] == "通识探索"
    assert payload["assigned_course"] == "intro"
    assert payload["initial_gold"] == 120
    assert payload["item_ids"] == ["planner", "campus_badge"]
    assert payload["achievement"] == "迈出第一步"
    assert payload["event"] == "社团摊位前"
    assert "校园笑话" in payload["forum"]
    assert payload["emitted_types"] == ["init", "tick"]
    assert payload["init_course_keys"] == ["intro", "methods", "writing"]
    assert payload["tick_course_keys"] == ["intro", "methods", "writing"]
    assert payload["tick_message"] == "demo tick"
