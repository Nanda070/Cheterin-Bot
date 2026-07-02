import embed_builder


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
    spec = {"title": "Hi", "description": "x" * 4096, "footer": {"text": "x" * 1900}}
    assert embed_builder.validate_embed_spec(spec) == "embed_too_large"
