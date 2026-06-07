from __future__ import annotations

from ytsum.prompts import build_prompt, detect_format


def test_detect_format_routes_keyword_groups() -> None:
    assert detect_format("Python API tutorial", "Dev", "install the package") == "tech"
    assert detect_format("Fed inflation market update", "Finance", "stocks and bonds") == "finance"
    assert detect_format("Step by step setup", "Tools", "how to configure") == "tutorial"
    assert detect_format("Plain travel notes", "Creator", "a calm walk") == "general"


def test_build_prompt_fills_template_and_returns_type() -> None:
    system, user, video_type = build_prompt(
        "Pricing strategy for SaaS",
        "Founder Channel",
        "This video covers startup revenue and pricing.",
        preset="auto",
        output_language="en",
    )
    assert "only facts present" in system
    assert "Pricing strategy for SaaS" in user
    assert "Write the summary in en" in user
    assert video_type == "business"
