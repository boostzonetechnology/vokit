from __future__ import annotations

import pytest

from control_plane.notifications.domain.policies import (
    assert_preference_allowed,
    is_mandatory,
    render_template,
)
from shared_kernel.errors import DomainError


def test_mandatory_notices_cannot_be_disabled() -> None:
    assert is_mandatory("kyc.approved") is True
    assert is_mandatory("announcement.platform") is False
    with pytest.raises(DomainError) as exc:
        assert_preference_allowed("kyc.approved", email=False, in_app=True)
    assert exc.value.code == "mandatory_notice"


def test_template_variables_are_escaped() -> None:
    rendered = render_template(
        "Hello {{email}}",
        {"email": "<script>alert(1)</script>"},
        "invitation.agency",
    )
    assert "<script>" not in rendered
    assert "&lt;script&gt;" in rendered
    with pytest.raises(DomainError):
        render_template("{{token}}", {"token": "x", "password": "nope"}, "invitation.agency")
