"""Tests for HTML cleaning utilities."""

from cordis_data.data.html_clean import clean_html_to_text


class TestHtmlClean:
    """Tests for clean_html_to_text function."""

    def test_clean_html_simple(self) -> None:
        """Test cleaning simple HTML."""
        html = "<p>Hello world</p>"
        result = clean_html_to_text(html)
        assert result == "Hello world"

    def test_clean_html_entities(self) -> None:
        """Test unescaping HTML entities."""
        html = "&lt;test&gt; &amp; &quot;quoted&quot;"
        result = clean_html_to_text(html)
        assert "<test>" in result
        assert "&" in result
        assert '"quoted"' in result

    def test_clean_html_nested_tags(self) -> None:
        """Test removing nested tags."""
        html = "<div><p>Text <strong>bold</strong> more</p></div>"
        result = clean_html_to_text(html)
        assert result == "Text bold more"

    def test_clean_html_multiple_spaces(self) -> None:
        """Test collapsing multiple spaces."""
        html = "<p>Text    with    spaces</p>"
        result = clean_html_to_text(html)
        assert result == "Text with spaces"

    def test_clean_html_whitespace(self) -> None:
        """Test stripping leading/trailing whitespace."""
        html = "  <p>Content</p>  "
        result = clean_html_to_text(html)
        assert result == "Content"

    def test_clean_html_empty_string(self) -> None:
        """Test with empty string."""
        result = clean_html_to_text("")
        assert result == ""

    def test_clean_html_none(self) -> None:
        """Test with None input."""
        result = clean_html_to_text(None)
        assert result == ""

    def test_clean_html_newlines(self) -> None:
        """Test collapsing newlines."""
        html = "<p>Line1\nLine2\n\nLine3</p>"
        result = clean_html_to_text(html)
        assert result == "Line1 Line2 Line3"

    def test_clean_html_lists(self) -> None:
        """Test cleaning list HTML."""
        html = "<ul><li>Item 1</li><li>Item 2</li></ul>"
        result = clean_html_to_text(html)
        assert "Item 1" in result
        assert "Item 2" in result
