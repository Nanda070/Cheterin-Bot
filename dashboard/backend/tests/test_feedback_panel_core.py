import feedback_panel_core


def test_resolve_banner_url_uses_custom_setting():
    feedback_panel_core.save_settings(999101, {"banner_url": "https://example.com/banner.png"})
    assert feedback_panel_core.resolve_banner_url(999101) == "https://example.com/banner.png"


def test_resolve_banner_url_returns_empty_when_unset():
    feedback_panel_core.save_settings(999102, {"banner_url": ""})
    assert feedback_panel_core.resolve_banner_url(999102) == ""
