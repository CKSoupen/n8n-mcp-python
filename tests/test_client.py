import pytest

from n8n_mcp.client import N8nApiError


def test_license_gated_403_with_feat_message():
    e = N8nApiError(403, "Your license does not allow for feat:variables. Please upgrade.")
    assert e.is_license_gated is True


def test_license_gated_501_with_license_word():
    e = N8nApiError(501, "License required for this endpoint")
    assert e.is_license_gated is True


def test_not_license_gated_for_other_403():
    e = N8nApiError(403, "Forbidden")
    assert e.is_license_gated is False


def test_not_license_gated_for_404():
    e = N8nApiError(404, "Your license does not allow this")
    assert e.is_license_gated is False
