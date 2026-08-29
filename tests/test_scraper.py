from utils.scraper import ProfileScraper, ScrapeError


def test_extract_apple_domains_normalizes_wildcards_and_duplicates():
    page = b"""
    <html><body>
      <table>
        <tr><th>Host</th><th>Port</th></tr>
        <tr><td>*.Push.Apple.com</td><td>443</td></tr>
        <tr><td>certs.apple.com</td><td>80</td></tr>
        <tr><td>certs.apple.com.</td><td>443</td></tr>
      </table>
      <table><tr><th>Other</th></tr><tr><td>ignored.example</td></tr></table>
    </body></html>
    """

    assert ProfileScraper.extract_apple_domains(page) == [
        "certs.apple.com",
        "push.apple.com",
    ]


def test_extract_apple_domains_requires_host_table():
    try:
        ProfileScraper.extract_apple_domains(b"<html><body></body></html>")
    except ScrapeError as exc:
        assert "host tables" in str(exc)
    else:
        raise AssertionError("Expected ScrapeError")


def test_extract_download_link_resolves_relative_url():
    page = b'<html><body><a id="profile" href="dns/profile.mobileconfig">Get</a></body></html>'

    assert ProfileScraper._extract_download_link(
        page,
        '//*[@id="profile"]',
        "https://example.com/base/",
    ) == "https://example.com/base/dns/profile.mobileconfig"
