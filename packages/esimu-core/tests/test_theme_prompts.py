"""Tests for theme-owned LLM prompt fragments."""

from esimu_core.world.prompts import ThemePrompts
from esimu_core.world.theme_paths import theme_dir


def test_demo_prompt_fragments_are_theme_neutral() -> None:
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
