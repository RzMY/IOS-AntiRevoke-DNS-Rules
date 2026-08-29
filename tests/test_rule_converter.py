from pathlib import Path

from utils.rule_converter import RuleFileGenerator


def test_enhanced_rule_generator_uses_separate_names(tmp_path: Path):
    generator = RuleFileGenerator(
        str(tmp_path),
        file_prefix="RevokeGuard_Enhanced",
        domain_filename="enhanced-domains.txt",
    )

    generated = generator.generate_all_rules(
        ["ppq.apple.com"],
        author="RzMY",
        updated_utc="2026-08-30 00:00:00 UTC",
        domain_count=1,
    )

    assert Path(generated["Surge"]).name == "RevokeGuard_Enhanced_Surge.txt"
    assert Path(generated["Domain List"]).name == "enhanced-domains.txt"
    assert "DOMAIN,ppq.apple.com,REJECT" in Path(generated["Surge"]).read_text(
        encoding="utf-8"
    )
