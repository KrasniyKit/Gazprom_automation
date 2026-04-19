from app.services.extract import _normalize_raw_data


def test_normalize_llm_payload_for_schema() -> None:
    normalized = _normalize_raw_data(
        {
            "equipment_name": "",
            "manufacturer": None,
            "purpose": None,
            "technical_specs": None,
            "normative_docs": None,
            "passport_number": None,
            "completeness": None,
            "service_life": None,
            "warranty": None,
            "issue_date": "",
            "uncertain_fields": None,
        }
    )

    assert normalized["equipment_name"] == "UNKNOWN"
    assert normalized["manufacturer"] == "UNKNOWN"
    assert normalized["purpose"] == ""
    assert normalized["technical_specs"] == ""
    assert normalized["normative_docs"] == ""
    assert normalized["passport_number"] == ""
    assert normalized["completeness"] == ""
    assert normalized["service_life"] == ""
    assert normalized["warranty"] == ""
    assert normalized["issue_date"] is None
    assert normalized["uncertain_fields"] == []
