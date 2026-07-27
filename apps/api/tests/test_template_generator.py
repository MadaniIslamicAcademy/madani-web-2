from types import SimpleNamespace

from app.enums import SocialProvider
from app.services.ai import TemplateContentGenerator


def test_template_generator_respects_fee_source() -> None:
    campaign = SimpleNamespace(
        name="Admissions",
        brief="Please explain the fee for Quran classes",
        content_type="Admissions Campaign",
        language="English",
        tone="Warm Islamic",
        audience="Parents",
        objective="Get enquiries",
        settings={},
    )
    output = TemplateContentGenerator().generate(campaign, [SocialProvider.FACEBOOK])
    assert "fee-structure" in output["facebook"]["body"]
    assert "Two Day Free Trial" in output["facebook"]["body"]
