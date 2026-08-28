"""Tests for theme-neutral content and message contracts."""

from esimu_core.content import (
    build_message_contact_id,
    compact_message_contacts,
    coerce_reply_options,
    framework_concept_for_legacy,
    legacy_id_for_concept,
    normalize_message_payload,
    sanitize_effects,
    select_local_event,
    select_local_forum_post,
    select_message_character,
    theme_term_for_concept,
)


def test_legacy_ids_map_to_framework_content_concepts() -> None:
    terms = {"forum": "星桥论坛", "messenger": "校内信"}

    assert framework_concept_for_legacy("cc98") == "forum"
    assert framework_concept_for_legacy("dingtalk") == "messenger"
    assert legacy_id_for_concept("forum") == "cc98"
    assert legacy_id_for_concept("messenger") == "dingtalk"
    assert theme_term_for_concept("cc98", terms) == "星桥论坛"
    assert theme_term_for_concept("dingtalk", terms) == "校内信"


def test_select_local_event_filters_state_and_seen_history() -> None:
    library = [
        {
            "id": "seen",
            "title": "旧事件",
            "desc": "已经出现过。",
            "sanity_range": [0, 200],
            "stress_range": [0, 200],
            "options": [],
        },
        {
            "id": "match",
            "title": "社团摊位前",
            "description": "有人递来传单。",
            "sanity_range": [80, 120],
            "stress_range": [0, 50],
            "options": [{"text": "看看"}],
        },
    ]

    event = select_local_event(
        library,
        sanity=100,
        stress=20,
        seen_ids={"seen"},
        choose=lambda candidates: candidates[0],
    )

    assert event is not None
    assert event.as_dict() == {
        "id": "match",
        "title": "社团摊位前",
        "desc": "有人递来传单。",
        "options": [{"text": "看看"}],
    }


def test_select_local_forum_post_prefers_trigger_hits() -> None:
    library = [
        {"effect": "positive", "trigger": "闲聊", "content": "普通帖子"},
        {"effect": "positive", "trigger": "校园梗", "content": "校园笑话"},
    ]

    post = select_local_forum_post(
        library,
        effect="positive",
        trigger="校园 梗",
        fallback="fallback",
        choose=lambda candidates: candidates[0],
    )

    assert post is not None
    assert post.content == "校园笑话"
    assert post.effect == "positive"
    assert post.trigger == "校园梗"


def test_message_payload_normalizes_contact_and_reply_options() -> None:
    payload = normalize_message_payload(
        {
            "contact": {"sender": "阿蓝", "role": "室友"},
            "message": {"content": "今晚要不要一起吃饭？"},
            "reply_options": ["好啊", {"option_id": "later", "text": "晚点说"}],
        },
        contact_prefix="dt",
    )

    assert payload.contact.contact_id.startswith("dt_")
    assert payload.contact.sender == "阿蓝"
    assert payload.contact.role == "roommate"
    assert payload.contact.is_replyable is True
    assert payload.content == "今晚要不要一起吃饭？"
    assert [option.as_dict() for option in payload.reply_options] == [
        {"option_id": "opt_1", "text": "好啊"},
        {"option_id": "later", "text": "晚点说"},
    ]


def test_reply_options_and_effects_are_safely_clamped() -> None:
    assert [option.text for option in coerce_reply_options([], "teacher")] == [
        "谢谢老师",
        "我会提前准备",
        "我还有一个问题",
    ]
    assert coerce_reply_options(["收到"], "stranger") == []

    result = sanitize_effects(
        {
            "desc": "聊完之后你振作了一些。",
            "effects": {"sanity": 999, "stress": -999, "bad": 5},
        },
        {"sanity": 5, "stress": 3},
    )

    assert result.desc == "聊完之后你振作了一些。"
    assert result.effects == {"sanity": 5, "stress": -3}


def test_character_selection_balances_new_and_reusable_contacts() -> None:
    characters = [
        {"name": "A", "role": "friend"},
        {"name": "B", "role": "classmate"},
    ]
    contacts = {
        build_message_contact_id("A", "friend"): {
            "sender": "A",
            "role": "friend",
            "round_open": False,
            "last_active_at": 1,
        }
    }
    new_character = select_message_character(
        characters,
        contacts,
        max_contacts=2,
        reuse_probability=0,
        random_value=lambda: 0.9,
        choose=lambda values: values[0],
    )
    reused = select_message_character(
        characters,
        contacts,
        max_contacts=1,
        reuse_probability=0,
        random_value=lambda: 0.9,
        choose=lambda values: values[0],
    )
    assert new_character and new_character["name"] == "B"
    assert reused and reused["name"] == "A"


def test_contact_compaction_keeps_open_rounds() -> None:
    compacted = compact_message_contacts(
        {
            "open": {"round_open": True, "last_active_at": 0},
            "old": {"round_open": False, "last_active_at": 1},
            "new": {"round_open": False, "last_active_at": 2},
        },
        max_contacts=2,
    )
    assert set(compacted) == {"open", "new"}
