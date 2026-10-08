import bot.core.embed_builder as embed_builder


def test_build_embed_sets_basic_fields():
    embed = embed_builder.build_embed({"title": "Hi", "description": "Desc", "color": "#5865F2"})
    assert embed.title == "Hi"
    assert embed.description == "Desc"
    assert embed.color.value == 0x5865F2


def test_build_embed_sets_author_footer_image_thumbnail():
    spec = {
        "author": {"name": "Author", "url": "https://a.example", "icon_url": "https://a.example/i.png"},
        "footer": {"text": "Footer", "icon_url": "https://f.example/i.png"},
        "image": {"url": "https://img.example/1.png"},
        "thumbnail": {"url": "https://thumb.example/1.png"},
    }
    embed = embed_builder.build_embed(spec)
    assert embed.author.name == "Author"
    assert embed.footer.text == "Footer"
    assert embed.image.url == "https://img.example/1.png"
    assert embed.thumbnail.url == "https://thumb.example/1.png"


def test_build_embed_sets_fields():
    embed = embed_builder.build_embed({"fields": [{"name": "N1", "value": "V1", "inline": True}]})
    assert len(embed.fields) == 1
    assert embed.fields[0].name == "N1"
    assert embed.fields[0].value == "V1"
    assert embed.fields[0].inline is True


def test_build_embed_sets_timestamp():
    embed = embed_builder.build_embed({"timestamp": "2026-07-02T12:00:00Z"})
    assert embed.timestamp is not None
    assert embed.timestamp.year == 2026


def test_embed_to_spec_round_trips_build_embed():
    original = {
        "title": "Hi",
        "description": "Desc",
        "color": "#5865f2",
        "author": {"name": "Author", "url": "", "icon_url": ""},
        "footer": {"text": "Footer", "icon_url": ""},
        "image": {"url": "https://img.example/1.png"},
        "thumbnail": {"url": ""},
        "fields": [{"name": "N1", "value": "V1", "inline": True}],
    }
    embed = embed_builder.build_embed(original)
    spec = embed_builder.embed_to_spec(embed)
    assert spec["title"] == "Hi"
    assert spec["description"] == "Desc"
    assert spec["color"] == "#5865f2"
    assert spec["author"]["name"] == "Author"
    assert spec["footer"]["text"] == "Footer"
    assert spec["image"]["url"] == "https://img.example/1.png"
    assert spec["fields"] == [{"name": "N1", "value": "V1", "inline": True}]


def test_validate_embed_spec_rejects_empty():
    assert embed_builder.validate_embed_spec({}) == "empty_embed"


def test_validate_embed_spec_accepts_title_only():
    assert embed_builder.validate_embed_spec({"title": "Hi"}) is None


def test_validate_embed_spec_rejects_title_too_long():
    assert embed_builder.validate_embed_spec({"title": "x" * 257}) == "title_too_long"


def test_validate_embed_spec_rejects_description_too_long():
    assert embed_builder.validate_embed_spec({"description": "x" * 4097}) == "description_too_long"


def test_validate_embed_spec_rejects_too_many_fields():
    fields = [{"name": "n", "value": "v"} for _ in range(26)]
    assert embed_builder.validate_embed_spec({"title": "Hi", "fields": fields}) == "too_many_fields"


def test_validate_embed_spec_rejects_field_name_too_long():
    result = embed_builder.validate_embed_spec({"title": "Hi", "fields": [{"name": "x" * 257, "value": "v"}]})
    assert result == "field_name_too_long"


def test_validate_embed_spec_rejects_field_value_too_long():
    result = embed_builder.validate_embed_spec({"title": "Hi", "fields": [{"name": "n", "value": "x" * 1025}]})
    assert result == "field_value_too_long"


def test_validate_embed_spec_rejects_total_budget_exceeded():
    # 2 ("Hi") + 4096 + 1903 = 6001, one over the 6000 budget.
    spec = {"title": "Hi", "description": "x" * 4096, "footer": {"text": "x" * 1903}}
    assert embed_builder.validate_embed_spec(spec) == "embed_too_large"


def test_build_embed_omits_color_when_absent():
    embed = embed_builder.build_embed({"title": "Hi"})
    assert embed.color is None
    assert "color" not in embed.to_dict()


def test_embed_to_spec_returns_empty_color_when_absent():
    embed = embed_builder.build_embed({"title": "Hi"})
    spec = embed_builder.embed_to_spec(embed)
    assert spec["color"] == ""


def test_embed_to_spec_handles_none_author_footer_fields():
    class FakeEmbed:
        def to_dict(self):
            return {
                "title": "T",
                "author": None,
                "footer": None,
                "image": None,
                "thumbnail": None,
                "fields": None,
            }

    spec = embed_builder.embed_to_spec(FakeEmbed())
    assert spec["title"] == "T"
    assert spec["author"] == {"name": "", "url": "", "icon_url": ""}
    assert spec["footer"] == {"text": "", "icon_url": ""}
    assert spec["image"] == {"url": ""}
    assert spec["fields"] == []


def test_message_to_editor_payload_content_only_has_complete_embed():
    from dashboard.backend.tests.fakes import FakeMessage

    payload = embed_builder.message_to_editor_payload(FakeMessage(1, embeds=[], content="just text"))
    assert payload["content"] == "just text"
    assert payload["components_version"] == "v1"
    assert payload["embed"]["author"]["name"] == ""
    assert payload["embed"]["footer"]["text"] == ""
    assert payload["embed"]["fields"] == []


def test_v2_message_to_spec_maps_layout_from_classic_embed():
    import bot.core.components_v2 as components_v2
    from dashboard.backend.tests.fakes import FakeMessage

    embed = embed_builder.build_embed(
        {
            "title": "Hello",
            "description": "World",
            "author": {"name": "Ann"},
            "footer": {"text": "bye"},
        }
    )
    layout = components_v2.build_layout_view(embed=embed, content="hi")
    message = FakeMessage(1, embeds=[], components=layout, content=None, components_v2=True)
    spec, content, saw_v2 = embed_builder.v2_message_to_spec(message)
    assert saw_v2 is True
    assert content == "hi"
    assert spec["title"] == "Hello"
    assert "World" in spec["description"]
    assert spec["author"]["name"] == "Ann"
    assert spec["footer"]["text"] == "bye"
    payload = embed_builder.message_to_editor_payload(message)
    assert payload["components_version"] == "v2"
    assert payload["embed"]["title"] == "Hello"


def test_is_embed_spec_empty_true_for_blank_spec():
    assert embed_builder.is_embed_spec_empty({}) is True


def test_is_embed_spec_empty_false_when_title_present():
    assert embed_builder.is_embed_spec_empty({"title": "Hi"}) is False


def test_validate_embed_spec_accepts_empty_embed_with_content():
    assert embed_builder.validate_embed_spec({}, content="Just text") is None


def test_validate_embed_spec_rejects_empty_embed_and_blank_content():
    assert embed_builder.validate_embed_spec({}, content="   ") == "empty_embed"


# ────────────────────── Шаблоны: per-guild персистентность (settings_db) ──────────────────────

def test_save_and_list_template_round_trips():
    saved = embed_builder.save_template(1, "Welcome", "hi", {"title": "T"}, ["10"])
    assert saved["id"] == "1"
    templates = embed_builder.list_templates(1)
    assert len(templates) == 1
    assert templates[0]["name"] == "Welcome"
    assert templates[0]["embed"] == {"title": "T"}
    assert templates[0]["role_ids"] == ["10"]


def test_templates_are_scoped_per_guild():
    embed_builder.save_template(1, "A", "", {"title": "T"}, [])
    embed_builder.save_template(2, "B", "", {"title": "T"}, [])
    assert [t["name"] for t in embed_builder.list_templates(1)] == ["A"]
    assert [t["name"] for t in embed_builder.list_templates(2)] == ["B"]


def test_save_template_rejects_duplicate_name():
    embed_builder.save_template(1, "Dup", "", {"title": "T"}, [])
    assert embed_builder.save_template(1, "Dup", "", {"title": "T"}, []) == "duplicate_name"
    # то же имя на другом сервере — не дубликат
    assert isinstance(embed_builder.save_template(2, "Dup", "", {"title": "T"}, []), dict)


def test_save_template_enforces_max_limit():
    for i in range(embed_builder.MAX_TEMPLATES):
        embed_builder.save_template(1, f"t{i}", "", {"title": "T"}, [])
    assert embed_builder.save_template(1, "overflow", "", {"title": "T"}, []) == "too_many_templates"


def test_delete_template_removes_only_target_and_guild():
    a = embed_builder.save_template(1, "A", "", {"title": "T"}, [])
    embed_builder.save_template(2, "A", "", {"title": "T"}, [])
    assert embed_builder.delete_template(1, a["id"]) is True
    assert embed_builder.list_templates(1) == []
    assert len(embed_builder.list_templates(2)) == 1


def test_delete_template_missing_returns_false():
    assert embed_builder.delete_template(1, "999") is False


def test_components_version_defaults_and_persists():
    assert embed_builder.get_components_version(1) == "v1"
    assert embed_builder.set_components_version(1, "v2") == "v2"
    assert embed_builder.get_components_version(1) == "v2"
    assert embed_builder.set_components_version(1, "components_v2") == "v2"
    assert embed_builder.set_components_version(1, "bogus") == "v1"
    assert embed_builder.get_components_version(2) == "v1"


# ────────────────────── Несколько эмбедов в одном сообщении ──────────────────────

def test_specs_from_body_prefers_embeds_and_drops_empty():
    body = {"embeds": [{"title": "A"}, {}, {"description": "B"}], "embed": {"title": "legacy"}}
    specs = embed_builder.specs_from_body(body)
    assert [s.get("title") or s.get("description") for s in specs] == ["A", "B"]


def test_specs_from_body_falls_back_to_legacy_embed():
    assert embed_builder.specs_from_body({"embed": {"title": "T"}}) == [{"title": "T"}]
    assert embed_builder.specs_from_body({}) == []
    assert embed_builder.specs_from_body({"embeds": None, "embed": {"title": "T"}}) == [{"title": "T"}]


def test_specs_from_body_rejects_bad_shapes():
    assert embed_builder.specs_from_body({"embeds": "nope"}) is None
    assert embed_builder.specs_from_body({"embeds": [{"title": "A"}, None]}) is None
    assert embed_builder.specs_from_body({"embed": "nope"}) is None


def test_validate_embed_specs_limits():
    one = {"title": "T"}
    assert embed_builder.validate_embed_specs([one] * 10) is None
    assert embed_builder.validate_embed_specs([one] * 11) == "too_many_embeds"
    assert embed_builder.validate_embed_specs([], "") == "empty_embed"
    assert embed_builder.validate_embed_specs([], "text") is None
    assert embed_builder.validate_embed_specs([one, {"title": "x" * 257}]) == "title_too_long"
    big = {"description": "x" * 3001}
    assert embed_builder.validate_embed_specs([big]) is None
    assert embed_builder.validate_embed_specs([big, big]) == "embed_too_large"


def test_message_to_editor_payload_returns_all_embeds():
    from dashboard.backend.tests.fakes import FakeMessage

    embeds = [embed_builder.build_embed({"title": f"E{i}"}) for i in range(3)]
    payload = embed_builder.message_to_editor_payload(FakeMessage(1, embeds=embeds, content="hi"))
    assert [e["title"] for e in payload["embeds"]] == ["E0", "E1", "E2"]
    assert payload["embed"]["title"] == "E0"


def test_message_to_editor_payload_content_only_has_one_blank_embed_slot():
    from dashboard.backend.tests.fakes import FakeMessage

    payload = embed_builder.message_to_editor_payload(FakeMessage(1, embeds=[], content="just text"))
    assert payload["embeds"] == [payload["embed"]]
