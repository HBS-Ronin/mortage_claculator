import numpy as np


def calculate_principal(monthly_payment, annual_rate, term_years, down_payment_pct):
    """Return max house value affordable at the given monthly payment.

    Supports scalar and numpy array inputs for annual_rate and term_years.
    Uses np.where to handle zero-rate edge case without branching on arrays.
    """
    n_payments = term_years * 12
    monthly_rate = annual_rate / 12
    safe_rate = np.where(monthly_rate == 0, np.finfo(float).eps, monthly_rate)
    principal = np.where(
        monthly_rate == 0,
        monthly_payment * n_payments,
        monthly_payment
        * ((1 + safe_rate) ** n_payments - 1)
        / (safe_rate * (1 + safe_rate) ** n_payments),
    )
    return principal / (1 - down_payment_pct / 100)


def generate_amortization_schedule(house_value, down_payment_pct, annual_rate, term_years):
    """Return (schedule, monthly_payment) for the given mortgage.

    schedule is a list of dicts with Month, Payment, Principal, Interest, Balance.
    Capped at 360 months (30 years) for display.
    """
    principal = house_value * (1 - down_payment_pct / 100)
    monthly_rate = annual_rate / 12
    n_payments = int(term_years * 12)

    if monthly_rate == 0:
        monthly_payment = principal / n_payments
    else:
        monthly_payment = (
            principal
            * (monthly_rate * (1 + monthly_rate) ** n_payments)
            / ((1 + monthly_rate) ** n_payments - 1)
        )

    schedule = []
    remaining_balance = principal

    for month in range(1, min(n_payments + 1, 361)):
        interest_payment = remaining_balance * monthly_rate
        principal_payment = monthly_payment - interest_payment
        remaining_balance -= principal_payment
        schedule.append({
            "Month": month,
            "Payment": f"£{monthly_payment:.2f}",
            "Principal": f"£{principal_payment:.2f}",
            "Interest": f"£{interest_payment:.2f}",
            "Balance": f"£{max(0, remaining_balance):.2f}",
        })
        if remaining_balance <= 0:
            break

    return schedule, monthly_payment


def calculate_take_home_pay(gross_salary):
    """Return annual take-home pay after UK Income Tax and NI (2024/25 rates).

    Uses England/Wales/Northern Ireland rates. Scalar inputs only.
    """
    _PA = 12_570
    _BR_LIMIT = 50_270
    _HR_LIMIT = 125_140

    income_tax = 0.0
    if gross_salary > _PA:
        income_tax += (min(gross_salary, _BR_LIMIT) - _PA) * 0.20
    if gross_salary > _BR_LIMIT:
        income_tax += (min(gross_salary, _HR_LIMIT) - _BR_LIMIT) * 0.40
    if gross_salary > _HR_LIMIT:
        income_tax += (gross_salary - _HR_LIMIT) * 0.45

    _NI_LOWER = 12_570
    _NI_UPPER = 50_270

    ni = 0.0
    if gross_salary > _NI_LOWER:
        ni += (min(gross_salary, _NI_UPPER) - _NI_LOWER) * 0.08
    if gross_salary > _NI_UPPER:
        ni += (gross_salary - _NI_UPPER) * 0.02

    return gross_salary - income_tax - ni
