"""Tests for theme-owned LLM prompt fragments."""

from __future__ import annotations

from esimu_core.world.prompts import ThemePrompts
from esimu_core.world.theme_paths import theme_dir


def test_zju_prompt_fragments_render_required_context() -> None:
    prompts = ThemePrompts(theme_dir("zju") / "prompts.json").config

    identity = prompts.player_identity_template.format(
        username="测试玩家",
        major="计算机科学与技术",
        semester="大一秋冬",
        charm_label="魅力",
        charm=120,
    )
    scene = prompts.messenger_scene_template.format(
        semester="大一秋冬",
        scene="随机问候",
    )

    assert "浙江大学" in prompts.campus_context
    assert "CC98" == prompts.forum_name
    assert "钉钉" == prompts.messenger_name
    assert "测试玩家" in identity
    assert "钉钉" in scene


def test_demo_prompt_fragments_are_not_zju_terms() -> None:
    prompts = ThemePrompts(theme_dir("demo-campus") / "prompts.json").config
    rendered = "\n".join(
        [
            prompts.campus_context,
            prompts.forum_name,
            prompts.messenger_name,
            prompts.forum_batch_instruction,
            prompts.messenger_batch_instruction,
            prompts.private_chat_instruction,
            prompts.messenger_open_template.format(username="Alex"),
        ]
    )

    assert "星桥学院" in rendered
    assert "星桥论坛" in rendered
    assert "校内信" in rendered
    assert "浙江大学" not in rendered
    assert "CC98" not in rendered
    assert "钉钉" not in rendered
