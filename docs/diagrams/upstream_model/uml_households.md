# UML: Households Agent — Original Upstream Design

This page documents the `Households` agent from the original upstream
[`uvic-sesit/macroabm-ca`](https://github.com/uvic-sesit/macroabm-ca) design.

`Households` aggregate individuals, make consumption/investment decisions,
interact with housing and credit markets, and manage wealth.

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

    class Households {
        +functions: dict
        +consumption_weights: ndarray
        +consumption_weights_by_income: ndarray
        +investment_weights: ndarray
        +use_consumption_weights_by_income: bool
        +independents: list[str]
        +bundle_matrix: ndarray
        +from_pickled_agent(...)$
        +reset(config)
        +compute_employee_income(individual_income, corr) ndarray
        +compute_expected_social_transfer_income(total, cpi, inflation) ndarray
        +compute_social_transfer_income(total, cpi) ndarray
        +compute_rental_income(housing_data, income_taxes) ndarray
        +compute_consumption_demand(...)
        +compute_investment_demand(...)
        +compute_wealth_allocation(...)
        +compute_saving_rates(...)
    }

    class HouseholdType {
        <<enumeration>>
        OWNER
        RENTER
    }

    Agent <|-- Households
    Households ..> HouseholdType : uses
```

**Key `states` attributes:**

| State | Type | Purpose |
|-------|------|---------|
| `Type` | ndarray | OWNER or RENTER |
| `Corresponding Bank ID` | ndarray | Bank relationship |
| `Corresponding Inhabited House ID` | ndarray | Primary residence |
| `Corresponding Property Owner` | ndarray | Landlord ID |
| `Tenure Status of the Main Residence` | ndarray | Ownership status |
| `corr_individuals` | list | Individuals per household |
| `Number of Adults` | ndarray | Adult count |
| `corr_renters` | list | Renter relationships |
| `saving_rates_model` | object | Saving behaviour model |
| `social_transfers_model` | object | Transfer allocation model |
| `wealth_distribution_model` | object | Wealth allocation model |
| `average_saving_rate` | float | Mean saving rate |
| `coefficient_fa_income` | float | Financial asset income coefficient |
| `investment_rate` | ndarray | Investment rate per household |

---

## 2. Sequence diagram — income aggregation

```mermaid
sequenceDiagram
    participant Country
    participant HH as Households
    participant Ind as Individuals

    Country->>HH: compute_employee_income(individual_income, corr_households)
    HH->>HH: np.bincount(corr, weights=income)

    Country->>HH: compute_social_transfer_income(total_other, cpi)
    HH->>HH: Use social_transfers_model (CPI-adjusted)

    Country->>HH: compute_rental_income(housing_data, income_taxes)
    HH->>HH: Aggregate rent from owned properties
```
