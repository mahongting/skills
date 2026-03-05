from pathlib import Path
import json


def test_skill_metadata_is_single_line_json():
    skill = Path(__file__).resolve().parents[1] / "SKILL.md"
    metadata_line = next(line for line in skill.read_text(encoding="utf-8").splitlines() if line.startswith("metadata:"))
    assert metadata_line.startswith("metadata: {")
    assert metadata_line.rstrip().endswith("}")


def test_skill_metadata_declares_sensitive_env_and_bins():
    skill = Path(__file__).resolve().parents[1] / "SKILL.md"
    metadata_line = next(line for line in skill.read_text(encoding="utf-8").splitlines() if line.startswith("metadata:"))
    payload = metadata_line.split("metadata:", 1)[1].strip()
    meta = json.loads(payload)
    requires = meta["openclaw"]["requires"]
    env = set(requires["env"])
    bins = set(requires["bins"])

    expected_env = {
        "ENTRA_TENANT_ID",
        "ENTRA_CLIENT_ID",
        "ENTRA_CLIENT_SECRET",
        "EXCHANGE_DEFAULT_MAILBOX",
        "EXCHANGE_ORGANIZATION",
        "ORGANIZATION_DOMAIN",
        "CLOUDFLARE_API_TOKEN",
        "CLOUDFLARE_ZONE_ID",
    }
    expected_bins = {"bash", "pwsh", "python3", "jq", "rg"}

    assert expected_env.issubset(env)
    assert expected_bins.issubset(bins)
