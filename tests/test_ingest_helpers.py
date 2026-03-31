from ingest.load_leads_jsonl_to_duckdb import derive_company_name, hash_email


def test_hash_email_normalizes_case_and_whitespace() -> None:
    first = hash_email(" User@Example.com ")
    second = hash_email("user@example.com")
    assert first == second


def test_derive_company_name_prefers_source_field() -> None:
    assert derive_company_name({"company_name": "Acme", "email": "x@y.com"}) == "Acme"


def test_derive_company_name_falls_back_to_email_domain() -> None:
    assert derive_company_name({"email": "owner@contoso.io"}) == "contoso"


def test_derive_company_name_returns_none_when_no_signal() -> None:
    assert derive_company_name({"lead_id": "abc"}) is None
