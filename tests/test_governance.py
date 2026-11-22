"""Governance checks: the secret scan finds every kind of key it promises (fake keys, built at run time so this
file holds none), skips placeholders, and finds nothing in the tracked files; the PII scan's rules work."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "governance"))

import pii_scan
import provenance_audit
import secret_scan


def fake(prefix: str, n: int, alphabet: str = "aB3dE5gH7jK9mN1pQ") -> str:
    return prefix + (alphabet * 10)[:n]


def test_every_kind_of_secret_is_found() -> None:
    samples = {
        "Anthropic API key": fake("sk-" + "ant-", 40),
        "OpenAI API key": fake("sk-" + "proj-", 40),
        "Google API key": fake("AI" + "za", 35),
        "AWS access key id": "AK" + "IA" + "QWERTYUIOPASDFGH",
        "GitHub token": fake("gh" + "p_", 36),
        "Hugging Face token": fake("h" + "f_", 34),
        "private key": "-----BEGIN RSA " + "PRIVATE KEY-----",
        "JWT": fake("ey" + "J", 20) + "." + fake("ey" + "J", 20) + "." + fake("", 20),
        "password in a connection string": "postgres://admin:" + "S3cretPass" + "@db.internal.lan/x",
        "secret assigned in code": "api_key = '" + fake("", 24) + "'",
    }
    for rule, text in samples.items():
        found = {r for r, _, _ in secret_scan.scan_text(text)}
        assert rule in found, (rule, found)
        assert all(text not in v for _, _, v in secret_scan.scan_text(text))   # never shown in full


def test_placeholders_are_not_secrets() -> None:
    assert not secret_scan.scan_text("api_key = 'your_api_key_goes_here_please'")
    assert not secret_scan.scan_text("USDA_API_KEY = os.environ['USDA_API_KEY_FROM_ENV']")


def test_no_tracked_file_holds_a_secret() -> None:
    findings, files = secret_scan.scan()
    assert files > 100
    assert findings == [], findings


def test_the_pii_rules_find_emails_phones_and_coordinates() -> None:
    kinds = {k for k, _ in pii_scan.scan_text("write to jane.doe@" + "mail.com or call (713) 555-" + "0199")}
    assert {"email", "phone number"} <= kinds
    assert "GPS coordinates" in {k for k, _ in pii_scan.scan_text("at 29.76043, -95.36980 today")}
    assert not pii_scan.scan_text("229228627+med27-coder@users.noreply.github.com")   # GitHub's no-reply address


def test_every_data_file_records_its_provenance() -> None:
    """A data file in data/knowledge/ or data/reference/ says its source and date, or a README names it."""
    gaps = [r["file"] for r in provenance_audit.audit() if not r["ok"]]
    assert gaps == [], gaps
