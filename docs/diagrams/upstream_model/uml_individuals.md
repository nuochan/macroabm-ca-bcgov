# UML: Individuals Agent — Original Upstream Design

This page documents the `Individuals` agent from the original upstream
[`uvic-sesit/macroabm-ca`](https://github.com/uvic-sesit/macroabm-ca) design.

`Individuals` represent the fundamental microeconomic units: they supply labor,
receive income, form households, and hold investments.

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

    class Gender {
        <<enumeration>>
        MALE
        FEMALE
    }

    class Education {
        <<enumeration>>
        LOW
        MEDIUM
        HIGH
    }

    Agent <|-- Individuals
    Individuals ..> ActivityStatus : uses
    Individuals ..> Gender : uses
    Individuals ..> Education : uses
```

**Key `states` attributes:**

| State | Type | Purpose |
|-------|------|---------|
| `Gender` | ndarray | Gender enum per individual |
| `Age` | ndarray | Age per individual |
| `Education` | ndarray | Education level per individual |
| `Activity Status` | ndarray | EMPLOYED/UNEMPLOYED/NOT_ECONOMICALLY_ACTIVE |
| `Employment Industry` | ndarray | Industry sector if employed |
| `Income` | ndarray | Total income per individual |
| `Employee Income` | ndarray | Wage income per individual |
| `Income from Unemployment Benefits` | ndarray | Benefit income |
| `Corresponding Household ID` | ndarray | Household mapping |
| `Corresponding Firm ID` | ndarray | Employer mapping |
| `Corresponding Invested Firm` | ndarray | Firm equity holding |
| `Corresponding Invested Bank` | ndarray | Bank equity holding |
| `Started New Job` | ndarray | Job transition flag |
| `Offered Wage of Accepted Job` | ndarray | Accepted wage |
| `Dividend Payout Ratio` | float | Dividend distribution rate |

---

## 2. Sequence diagram — income computation

```mermaid
sequenceDiagram
    participant H as Households
    participant Ind as Individuals
    participant Func as functions["income"]

    H->>Ind: compute_income(firm_profits, bank_profits, cpi, income_taxes, tau_firm)
    Ind->>Func: compute_income(activity_status, wages, social_benefits, firm_profits, ...)
    Func-->>Ind: total_income
    Ind-->>H: ndarray[n_individuals]
```

---

## 3. Activity diagram — individual lifecycle in a timestep

```mermaid
flowchart TD
    A[Begin timestep] --> B[compute_labour_inputs]
    B --> C[LabourMarket.clear]
    C --> D[update wages: employee_income]
    D --> E[compute_income]
    E --> F[update_demography]
    F --> G[End timestep]
```
