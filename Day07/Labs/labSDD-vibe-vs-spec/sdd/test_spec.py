import pytest

from triage import triage


def test_ac1_60_affected_users_is_p1_and_sla_4():
    result = triage({"title": "Issue", "affected_users": 60})
    assert result == {"priority": "P1", "queue": "General", "sla_hours": 4}


def test_ac2_email_outage_is_p1():
    result = triage({"title": "Email outage"})
    assert result["priority"] == "P1"


def test_ac3_slow_download_speed_is_p4():
    result = triage({"title": "Slow download speed"})
    assert result["priority"] == "P4"


def test_ac4_12_users_is_p2_and_sla_8():
    result = triage({"title": "Issue", "affected_users": 12})
    assert result == {"priority": "P2", "queue": "General", "sla_hours": 8}


def test_ac5_urgent_cannot_print_is_p2():
    result = triage({"title": "URGENT: cannot print"})
    assert result["priority"] == "P2"


def test_ac6_3_users_is_p3_and_sla_24():
    result = triage({"title": "Issue", "affected_users": 3})
    assert result == {"priority": "P3", "queue": "General", "sla_hours": 24}


def test_ac7_laptop_wifi_broken_goes_to_network():
    result = triage({"title": "Laptop wifi broken"})
    assert result["queue"] == "Network"


def test_ac8_password_reset_goes_to_access():
    result = triage({"title": "Password reset"})
    assert result["queue"] == "Access"


def test_ac9_empty_title_and_zero_users_raise_value_error():
    with pytest.raises(ValueError):
        triage({"title": "", "affected_users": 1})

    with pytest.raises(ValueError):
        triage({"title": "Issue", "affected_users": 0})