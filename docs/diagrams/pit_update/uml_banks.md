# UML: Banks Agent — Progressive PIT Update

This page documents the `Banks` agent in the progressive PIT branch.

**PIT impact**: 🟢 **Unchanged.** Banks intermediate deposits and loans, set interest
rates, and compute profits. They pay corporate tax at the flat `Profit Tax` rate and
are unaffected by changes to personal income taxation.

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
        +compute_profits() ndarray
        +update_deposits(firm_deposits, hh_deposits, ...)
        +update_loans(credit_market)
        +compute_market_share() ndarray
        +compute_equity(profit_taxes) ndarray
        +handle_insolvency(credit_market) float
    }

    Agent <|-- Banks
```

---

## 2. PIT-related observations

| Aspect | Detail |
|--------|--------|
| **Bank profits** | Taxed at flat `Profit Tax` (corporate) — not PIT |
| **Interest rate setting** | Responds to `CentralBank.policy_rate` — unchanged |
| **Deposit/loan management** | No tax awareness — unchanged |
| **Equity computation** | Uses `profit_taxes` (corporate rate) — unchanged |

> Banks are completely unaffected by the PIT update. Their tax obligation is corporate
> (`Profit Tax`), not personal income tax.
