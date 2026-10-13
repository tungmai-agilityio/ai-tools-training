from app import fees


def test_uninsured_pays_full_fee():
    assert fees.consultation_fee(15000, insured=False, duration_minutes=30) == 15000


def test_insured_gets_20_percent_off():
    assert fees.consultation_fee(15000, insured=True, duration_minutes=30) == 12000


def test_sixty_minute_visit_doubles_fee():
    assert fees.consultation_fee(15000, insured=False, duration_minutes=60) == 30000


def test_late_cancellation_is_half_of_fee():
    assert fees.late_cancellation_fee(15000) == 7500


def test_no_show_is_full_fee():
    assert fees.no_show_fee(15000) == 15000
