from shadetruth.adapters.youcam import _redact


def test_task_id_is_redacted_in_logs():
    assert _redact("/s2s/v2.0/task/makeup-vto/abc123") == "/s2s/v2.0/task/makeup-vto/<task_id>"
    assert _redact("/s2s/v2.0/file") == "/s2s/v2.0/file"


def test_palette_gloss_has_required_fields_and_unknown_rejected():
    import pytest
    from shadetruth.adapters.youcam import _palette
    p = _palette("#C2185B", "gloss")
    assert p["texture"] == "gloss" and "gloss" in p and "transparencyIntensity" in p
    assert _palette("#C2185B", "matte")["texture"] == "matte"
    with pytest.raises(ValueError):
        _palette("#C2185B", "holographic")
