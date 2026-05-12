import numpy as np
import pytest


def test_calculate_principal_basic():
    from calculations import calculate_principal
    # £1200/month, 5% annual rate, 25-year term, 10% down
    # Loan = 1200 * ((1+r)^n - 1) / (r*(1+r)^n) ≈ 205272; house = loan / 0.9 ≈ 228080
    result = calculate_principal(1200, 0.05, 25, 10)
    assert abs(float(result) - 228_080) < 1000


def test_calculate_principal_zero_rate():
    from calculations import calculate_principal
    # At 0% rate: loan = payment * n_payments; house_value = loan (0% down)
    result = calculate_principal(1000, 0.0, 25, 0)
    assert float(result) == pytest.approx(1000 * 25 * 12)


def test_calculate_principal_down_payment():
    from calculations import calculate_principal
    # 10% down means house_value = loan / 0.9
    no_down = calculate_principal(1000, 0.05, 25, 0)
    with_down = calculate_principal(1000, 0.05, 25, 10)
    assert float(with_down) == pytest.approx(float(no_down) / 0.9, rel=1e-6)


def test_calculate_principal_array_inputs():
    from calculations import calculate_principal
    rates = np.array([0.03, 0.05, 0.07])
    terms = np.array([20.0, 25.0, 30.0])
    result = calculate_principal(1200, rates, terms, 10)
    assert result.shape == (3,)
    assert all(result > 0)
    # Lower rate should afford more
    assert result[0] > result[1] > result[2]


def test_calculate_principal_meshgrid():
    from calculations import calculate_principal
    rates = np.linspace(0.03, 0.07, 10)
    terms = np.arange(15, 36)
    R, T = np.meshgrid(rates, terms)
    result = calculate_principal(1200, R, T, 10)
    assert result.shape == R.shape
    assert np.all(result > 0)


def test_generate_amortization_schedule_basic():
    from calculations import generate_amortization_schedule
    schedule, payment = generate_amortization_schedule(300_000, 10, 0.05, 25)
    assert len(schedule) > 0
    assert payment > 0
    assert schedule[0]["Month"] == 1


def test_generate_amortization_schedule_zero_rate():
    from calculations import generate_amortization_schedule
    # At 0% every payment is equal principal, no interest
    schedule, payment = generate_amortization_schedule(300_000, 0, 0.0, 25)
    assert payment == pytest.approx(300_000 / (25 * 12), rel=1e-6)
    assert schedule[0]["Interest"] == "£0.00"


def test_generate_amortization_schedule_balance_reaches_zero():
    from calculations import generate_amortization_schedule
    schedule, _ = generate_amortization_schedule(200_000, 10, 0.04, 20)
    final_balance = float(schedule[-1]["Balance"].replace("£", "").replace(",", ""))
    assert final_balance == pytest.approx(0.0, abs=1.0)


def test_take_home_zero():
    from calculations import calculate_take_home_pay
    assert calculate_take_home_pay(0) == pytest.approx(0)


def test_take_home_below_personal_allowance():
    from calculations import calculate_take_home_pay
    # £10,000 — below personal allowance and NI threshold, no deductions
    assert calculate_take_home_pay(10_000) == pytest.approx(10_000)


def test_take_home_basic_rate_only():
    from calculations import calculate_take_home_pay
    # £30,000 gross
    # IT:  (30000 - 12570) * 0.20 = 17430 * 0.20 = 3486.00
    # NI:  (30000 - 12570) * 0.08 = 17430 * 0.08 = 1394.40
    # Net: 30000 - 3486 - 1394.40 = 25119.60
    assert calculate_take_home_pay(30_000) == pytest.approx(25_119.60, abs=1)


def test_take_home_higher_rate():
    from calculations import calculate_take_home_pay
    # £60,000 gross
    # IT:  37700 * 0.20 + 9730 * 0.40 = 7540 + 3892 = 11432.00
    # NI:  37700 * 0.08 + 9730 * 0.02 = 3016 + 194.60 = 3210.60
    # Net: 60000 - 11432 - 3210.60 = 45357.40
    assert calculate_take_home_pay(60_000) == pytest.approx(45_357.40, abs=1)


def test_take_home_additional_rate():
    from calculations import calculate_take_home_pay
    # £130,000 gross
    # IT:  37700*0.20 + 74870*0.40 + 4860*0.45 = 7540 + 29948 + 2187 = 39675.00
    # NI:  37700*0.08 + 79730*0.02 = 3016 + 1594.60 = 4610.60
    # Net: 130000 - 39675 - 4610.60 = 85714.40
    assert calculate_take_home_pay(130_000) == pytest.approx(85_714.40, abs=1)
