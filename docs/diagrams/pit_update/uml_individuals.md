# UML: Individuals Agent — Progressive PIT Update

This page documents the `Individuals` agent in the progressive PIT branch.

**PIT impact**: 🟢 **Unchanged.** The `Individuals` agent has no direct changes from the
PIT update. Individuals continue to supply labor, receive wages, and compute income
identically to the upstream design. The progressive tax computation happens downstream
in `CentralGovernment.compute_taxes()` — individuals are not aware of bracket structures.

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

    class Individuals {
        +functions: dict
        +n_individuals: int
        +from_pickled_agent(...)$
        +reset(config)
        +compute_labour_inputs() ndarray
        +compute_reservation_wages(unemployment_benefits) ndarray
        +compute_expected_income(firm_profits, bank_profits, ...) ndarray
        +compute_income(firm_profits, bank_profits, cpi, taxes) ndarray
        +update_demography()
        +save_to_h5(group)
    }

    class ActivityStatus {
        <<enumeration>>
        EMPLOYED
        UNEMPLOYED
        NOT_ECONOMICALLY_ACTIVE
    }

    Agent <|-- Individuals
    Individuals ..> ActivityStatus : uses
```

**Key `states` attributes:**

| State | Type | Purpose |
|-------|------|---------|
| `Activity Status` | ndarray | Used by CentralGovernment to filter EMPLOYED for progressive PIT |
| `Employee Income` | ndarray | Gross wages before tax — fed to `compute_progressive_tax()` |
| `Income` | ndarray | Total income (wages + benefits + investment returns) |

> **PIT note**: `Activity Status == EMPLOYED` is used by `CentralGovernment` to select which
> individuals' wages are taxed progressively. `Employee Income` flows through `Households` to
> `CentralGovernment.compute_taxes()` where bracket logic applies. Individuals themselves have
> no knowledge of brackets or marginal rates — they only see the effective scalar `Income Tax`.

---

## 2. Sequence diagram — income computation (unchanged)

```mermaid
sequenceDiagram
    participant H as Households
    participant Ind as Individuals
    participant Func as functions["income"]

    H->>Ind: compute_income(firm_profits, bank_profits, cpi, income_taxes, tau_firm)
    Note over Ind: income_taxes = scalar "Income Tax" (effective rate)
    Ind->>Func: compute_income(activity_status, wages, social_benefits, firm_profits, ...)
    Func-->>Ind: total_income
    Ind-->>H: ndarray[n_individuals]
```
