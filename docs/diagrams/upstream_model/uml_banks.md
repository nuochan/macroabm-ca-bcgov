# UML: Banks Agent — Original Upstream Design

This page documents the `Banks` agent from the original upstream
[`uvic-sesit/macroabm-ca`](https://github.com/uvic-sesit/macroabm-ca) design.

`Banks` intermediate between savers and borrowers, managing deposits, loans,
interest rates, and financial stability.

Reference: Bersini, H. (2012). [*UML for ABM*](https://www.jasss.org/15/1/9.html). JASSS 15(1)9.

---

## 1. Class diagram

```mermaid
classDiagram
    class Agent {
        <<abstract>>
        +country_name: str
        +states: dict
        +ts: TimeSeries
    }

    class Banks {
        +functions: dict
        +parameters: BankParameters
        +policy_rate_markup: float
        +from_pickled_agent(...)$
        +reset(config)
        +compute_estimated_profits(growth, inflation) ndarray
        +set_interest_rates(central_bank_policy_rate)
        +compute_interest_received_on_deposits(policy_rate) ndarray
        +compute_profits() ndarray
        +update_deposits(firm_deposits, hh_deposits, ...)
        +update_loans(credit_market)
        +compute_market_share() ndarray
        +compute_equity(profit_taxes) ndarray
        +compute_liability() ndarray
        +compute_deposits() ndarray
        +handle_insolvency(credit_market) float
    }

    Agent <|-- Banks
```

**Key `states` attributes:**

| State | Type | Purpose |
|-------|------|---------|
| `corr_firms` | list | Firm-bank mapping |
| `corr_households` | list | Household-bank mapping |
| `is_insolvent` | ndarray | Bankruptcy flag |
| `Firm Pass Through` | float | Interest rate pass-through to firms |
| `Firm ECT` | float | Error correction term (firms) |
| `Household Consumption Pass Through` | float | Rate pass-through (consumption loans) |
| `Household Consumption ECT` | float | ECT (consumption loans) |
| `Household Mortgage Pass Through` | float | Rate pass-through (mortgages) |
| `Household Mortgage ECT` | float | ECT (mortgages) |

---

## 2. Sequence diagram — interest rate setting

```mermaid
sequenceDiagram
    participant CB as CentralBank
    participant B as Banks
    participant Func as functions["interest_rates"]

    CB->>B: set_interest_rates(policy_rate)

    rect rgb(240, 248, 255)
        Note over B,Func: Loan rates
        B->>Func: get_interest_rates_on_short_term_firm_loans(...)
        B->>Func: get_interest_rates_on_long_term_firm_loans(...)
        B->>Func: get_interest_rates_on_household_consumption_loans(...)
        B->>Func: get_interest_rate_on_mortgages(...)
    end

    rect rgb(255, 248, 240)
        Note over B,Func: Deposit rates
        B->>Func: compute_interest_rate_on_firm_deposits(...)
        B->>Func: compute_overdraft_rate_on_firm_deposits(...)
        B->>Func: compute_interest_rate_on_household_deposits(...)
        B->>Func: compute_overdraft_rate_on_household_deposits(...)
    end
```
