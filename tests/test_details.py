"""Tests for detail handlers."""

import pytest
from gcalcli.details import Attachments
from gcalcli.exceptions import ReadonlyCheckError


class TestAttachmentsHandler:
    """Tests for Attachments handler."""

    def test_get_with_no_attachments(self):
        """Test get() returns empty string for events without attachments."""
        event = {}
        result = Attachments.get(event)
        assert result == ['']

    def test_get_with_single_attachment(self):
        """Test get() returns formatted string for single attachment."""
        event = {
            'attachments': [
                {
                    'title': 'Notes by Gemini',
                    'fileUrl': 'https://docs.google.com/document/d/123/edit'
                }
            ]
        }
        result = Attachments.get(event)
        assert result == ['Notes by Gemini|https://docs.google.com/document/d/123/edit']

    def test_get_with_multiple_attachments(self):
        """Test get() returns formatted string for multiple attachments."""
        event = {
            'attachments': [
                {
                    'title': 'Document 1',
                    'fileUrl': 'https://docs.google.com/document/d/123/edit'
                },
                {
                    'title': 'Document 2',
                    'fileUrl': 'https://docs.google.com/document/d/456/edit'
                }
            ]
        }
        result = Attachments.get(event)
        expected = (
            'Document 1|https://docs.google.com/document/d/123/edit\f'
            'Document 2|https://docs.google.com/document/d/456/edit'
        )
        assert result == [expected]

    def test_get_with_missing_fields(self):
        """Test get() handles missing title/fileUrl fields gracefully."""
        event = {
            'attachments': [
                {
                    'title': 'Document 1'
                    # missing fileUrl
                },
                {
                    'fileUrl': 'https://docs.google.com/document/d/456/edit'
                    # missing title
                }
            ]
        }
        result = Attachments.get(event)
        expected = 'Document 1|\f|https://docs.google.com/document/d/456/edit'
        assert result == [expected]

    def test_data_with_no_attachments(self):
        """Test data() returns empty list for events without attachments."""
        event = {}
        result = Attachments.data(event)
        assert result == []

    def test_data_with_single_attachment(self):
        """Test data() returns properly formatted dict for single attachment."""
        event = {
            'attachments': [
                {
                    'title': 'Notes by Gemini',
                    'fileUrl': 'https://docs.google.com/document/d/123/edit'
                }
            ]
        }
        result = Attachments.data(event)
        expected = [
            {
                'attachment_title': 'Notes by Gemini',
                'attachment_url': 'https://docs.google.com/document/d/123/edit'
            }
        ]
        assert result == expected

    def test_data_with_multiple_attachments(self):
        """Test data() returns formatted dict list for attachments."""
        event = {
            'attachments': [
                {
                    'title': 'Document 1',
                    'fileUrl': 'https://docs.google.com/document/d/123/edit'
                },
                {
                    'title': 'Document 2',
                    'fileUrl': 'https://docs.google.com/document/d/456/edit'
                }
            ]
        }
        result = Attachments.data(event)
        expected = [
            {
                'attachment_title': 'Document 1',
                'attachment_url': 'https://docs.google.com/document/d/123/edit'
            },
            {
                'attachment_title': 'Document 2',
                'attachment_url': 'https://docs.google.com/document/d/456/edit'
            }
        ]
        assert result == expected

    def test_data_with_missing_fields(self):
        """Test data() handles missing title/fileUrl fields gracefully."""
        event = {
            'attachments': [
                {
                    'title': 'Document 1'
                    # missing fileUrl
                },
                {
                    'fileUrl': 'https://docs.google.com/document/d/456/edit'
                    # missing title
                }
            ]
        }
        result = Attachments.data(event)
        expected = [
            {
                'attachment_title': 'Document 1',
                'attachment_url': ''
            },
            {
                'attachment_title': '',
                'attachment_url': 'https://docs.google.com/document/d/456/edit'
            }
        ]
        assert result == expected

    def test_get_with_semicolons(self):
        """Test get() handles semicolons in titles and URLs correctly."""
        event = {
            'attachments': [
                {
                    'title': 'Meeting Notes; Q4 2025',
                    'fileUrl': 'https://example.com/doc;jsessionid=ABC123'
                },
                {
                    'title': 'Agenda',
                    'fileUrl': 'https://docs.google.com/document/d/456/edit'
                }
            ]
        }
        result = Attachments.get(event)
        # Semicolons should be preserved, form feed used as separator
        expected = 'Meeting Notes; Q4 2025|https://example.com/doc;jsessionid=ABC123\fAgenda|https://docs.google.com/document/d/456/edit'
        assert result == [expected]

    def test_get_with_form_feed_in_data(self):
        """Test get() escapes existing form feed characters in data."""
        event = {
            'attachments': [
                {
                    'title': 'Document\fwith\fformfeeds',
                    'fileUrl': 'https://example.com/doc'
                }
            ]
        }
        result = Attachments.get(event)
        # Form feeds in data should be escaped as r'\f'
        expected = r'Document\fwith\fformfeeds|https://example.com/doc'
        assert result == [expected]

    def test_fieldnames(self):
        """Test fieldnames are correctly defined."""
        assert Attachments.fieldnames == ['attachments']

    def test_patch_with_unchanged_value(self):
        """Test patch doesn't error when value hasn't changed."""
        event = {
            'attachments': [
                {
                    'title': 'Notes by Gemini',
                    'fileUrl': 'https://docs.google.com/document/d/123/edit'
                }
            ]
        }
        current_value = 'Notes by Gemini|https://docs.google.com/document/d/123/edit'
        # Should not raise an error when value hasn't changed
        Attachments.patch(None, event, 'attachments', current_value)

    def test_patch_with_changed_value(self):
        """Test patch raises error when trying to change value."""
        event = {
            'attachments': [
                {
                    'title': 'Notes by Gemini',
                    'fileUrl': 'https://docs.google.com/document/d/123/edit'
                }
            ]
        }
        new_value = 'Different|https://example.com'
        # Should raise ReadonlyCheckError when trying to change value
        with pytest.raises(ReadonlyCheckError):
            Attachments.patch(None, event, 'attachments', new_value)

    def test_patch_with_no_attachments(self):
        """Test patch handles events without attachments."""
        event = {}
        # Should not raise an error for empty value
        Attachments.patch(None, event, 'attachments', '')
