from app.services.text_cleaning_service import TextCleaningService


def test_text_cleaning_normalizes_whitespace_without_removing_sections() -> None:
    service = TextCleaningService()
    raw_text = "  Eligibility:\r\n\r\n\r\n  Applicants   must attend HIPAA training.\tBring ID.  "

    cleaned = service.clean(raw_text)

    assert cleaned == "Eligibility:\n\nApplicants must attend HIPAA training. Bring ID."
    assert "Eligibility:" in cleaned
    assert "HIPAA training" in cleaned
