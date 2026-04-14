from bs4 import BeautifulSoup

from app.page_agent.scraper import _detect_client_rendered_shell


def test_detects_client_rendered_shell():
    html = """
    <html>
      <head>
        <title>Example SPA</title>
        <script type="module" src="/assets/main-abc123.js"></script>
      </head>
      <body>
        <div id="root"></div>
      </body>
    </html>
    """

    soup = BeautifulSoup(html, "html.parser")
    reason = _detect_client_rendered_shell(soup)

    assert reason is not None
    assert "browser rendering" in reason
