"""Testing utilities for gcalcli tests."""

import io
from typing import Dict, Any, Set, Optional, List, Tuple


def create_ics_content(events: List[Dict[str, Any]]) -> io.StringIO:
    """Create ICS content for testing with multiple events.

    Args:
        events: List of event dicts with keys like:
            - summary: Event title
            - has_self_attendee: Boolean, whether current user is an attendee
            - attendee_email: Email for the attendee (optional)
            - uid_suffix: Suffix for the UID (optional, defaults to index)

    Returns:
        io.StringIO object containing the ICS content
    """

    ics_lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Test//Test Events//EN",
    ]

    for i, event in enumerate(events):
        summary = event.get('summary', f'Test Event {i + 1}')
        uid_suffix = event.get('uid_suffix', str(i + 1))

        ics_lines.extend(
            [
                "BEGIN:VEVENT",
                f"UID:test-ical-uid-{uid_suffix}",
                f"DTSTART:2024100{i + 1}T140000Z",
                f"DTEND:2024100{i + 1}T150000Z",
                f"SUMMARY:{summary}",
                f"DESCRIPTION:Test event: {summary}",
            ]
        )

        if event.get('has_self_attendee'):
            attendee_email = event.get('attendee_email', 'test@example.com')
            ics_lines.append(
                f"ATTENDEE;ROLE=REQ-PARTICIPANT;PARTSTAT=ACCEPTED:MAILTO:{attendee_email}"
            )

        ics_lines.append("END:VEVENT")

    ics_lines.append("END:VCALENDAR")

    return io.StringIO('\n'.join(ics_lines) + '\n')


class CallMatcher:
    """Matcher for verifying API calls with specific attributes."""

    def __init__(self, method_name: str,
                 body_has_fields: Optional[Set[str]] = None,
                 body_fields: Optional[Dict[str, Any]] = None):
        self.method_name = method_name
        self.body_has_fields = body_has_fields or set()
        self.body_fields = body_fields or {}

    def matches(self, method_name: str,
                kwargs: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Check if the call matches the expected criteria."""
        if method_name != self.method_name:
            return (
                False,
                f"Expected method '{self.method_name}', got '{method_name}'",
            )

        body = kwargs.get('body', {})

        if self.body_has_fields:
            missing_fields = self.body_has_fields - set(body.keys())
            if missing_fields:
                return False, (
                    f"Body missing required fields: {missing_fields}.\n"
                    f"Available fields: {list(body.keys())}"
                )

        if self.body_fields:
            for field, expected_value in self.body_fields.items():
                if field not in body:
                    return False, (
                        f"Body missing field '{field}' (needed to check value)"
                    )
                actual_value = body[field]
                if actual_value != expected_value:
                    return False, (
                        f"Field '{field}': expected {expected_value!r}, "
                        f"got {actual_value!r}"
                    )

        return True, None


class APICallTracker:
    """Tracks API calls for testing purposes."""

    def __init__(self):
        self.calls: List[Tuple[str, Dict[str, Any]]] = []

    def track_call(self, method_name: str, **kwargs: Any):
        """Record an API call and return a mock request object."""
        self.calls.append((method_name, kwargs))

        class MockRequest:
            def execute(self, http=None):
                # Return appropriate mock data based on the method
                if method_name == 'list':
                    return {'items': []}  # Empty list for search results
                elif method_name == 'quickAdd':
                    return {'id': 'mock_quickadd_event_id',
                            'summary': 'Mock Quick Event'}
                else:
                    return {'id': 'mock_event_id'}

        return MockRequest()

    def verify_calls(self, expected: List[CallMatcher]) -> None:
        """Verify that the expected calls were made."""
        if len(expected) != len(self.calls):
            actual_methods = [call[0] for call in self.calls]
            expected_methods = [e.method_name for e in expected]
            assert False, (
                f"Expected {len(expected)} calls, got {len(self.calls)}.\n"
                f"Expected: {expected_methods}\n"
                f"Actual: {actual_methods}"
            )

        for i, expectation in enumerate(expected):
            method_name, kwargs = self.calls[i]
            matches, error = expectation.matches(method_name, kwargs)
            if not matches:
                assert False, f"Call {i}: {error}"

    def verify_method_called(self, method_name: str) -> None:
        """Verify that a specific method was called at least once."""
        method_calls = [call for call in self.calls if call[0] == method_name]
        assert len(method_calls) > 0, (
            f"Expected method '{method_name}' to be called, but it wasn't. "
            f"Actual calls: {[call[0] for call in self.calls]}"
        )

    def verify_only_mutating_calls(
            self, allowed_mutating_methods: Set[str]) -> None:
        """Verify only specified mutating methods (plus reads) were called."""
        read_only_methods = {'list', 'get', 'watch'}
        allowed_methods = read_only_methods | allowed_mutating_methods

        disallowed_calls = [
            call for call in self.calls if call[0] not in allowed_methods
        ]
        assert len(disallowed_calls) == 0, (
            f"Expected only calls to reads + {allowed_mutating_methods}, "
            f"but found disallowed calls: "
            f"{[call[0] for call in disallowed_calls]}"
        )

    def verify_no_mutating_calls(self) -> None:
        """Verify that no mutating API calls were made (only reads allowed)."""
        self.verify_only_mutating_calls(set())

    def verify_all_mutating_calls(
            self, expected_calls: List[CallMatcher]) -> None:
        """Verify specific calls AND only those mutating methods were called."""
        # First verify the specific calls match
        self.verify_calls(expected_calls)

        # Then verify only the expected mutating methods were called
        expected_mutating_methods = {
            call.method_name for call in expected_calls
        }
        self.verify_only_mutating_calls(expected_mutating_methods)
