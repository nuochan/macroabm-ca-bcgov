# UML Demo: The `CentralGovernment` Agent

This page applies Bersini's four-diagram UML subset to the [`CentralGovernment`](../../macromodel/agents/central_government/central_government.py)
agent — the fiscal authority. See the [Individuals UML demo](uml_individual_agent_demo.md) for methodology references.

Reference: Bersini, H. (2012). [*UML for ABM*](https://www.jasss.org/15/1/9.html). JASSS 15(1)9.

---

## 1. Class diagram

`CentralGovernment` inherits from `Agent` and aggregates two strategy classes:
`social_benefits` and `social_housing`. It depends on the `ActivityStatus` enum
and the `compute_progressive_tax` function for progressive PIT. It holds an
extensive set of tax rates and benefit models in `states`.

```mermaid
classDiagram
    class Agent {
        <<abstract>>
        +country_name: str
        +states: dict
        +ts: TimeSeries
    }

    class CentralGovernment {
        +functions: dict
        +pit_base_thresholds: ndarray
        +pit_base_basic_deduction: float
        +from_pickled_agent(...)$
        +reset(config)
        +update_benefits(historic_ppi, exogenous_ppi, ...)
        +distribute_unemployment_benefits_to_individuals(status)
        +compute_taxes(income, rent, financial_income, ...)
        +step_pit_brackets(cpi_growth)
        +save_to_h5(group)
    }

    class ActivityStatus {
        <<enumeration>>
        EMPLOYED
        UNEMPLOYED
        NOT_ECONOMICALLY_ACTIVE
    }

    class SocialBenefitsFunction {
        +compute_unemployment_benefits(...)
        +compute_regular_transfer_to_households(...)
    }

    class SocialHousingFunction {
        +compute_social_housing(...)
    }

    Agent <|-- CentralGovernment
    CentralGovernment ..> ActivityStatus : uses
    CentralGovernment "1" o-- "*" SocialBenefitsFunction : functions["social_benefits"]
    CentralGovernment "1" o-- "*" SocialHousingFunction : functions["social_housing"]
```

**Key `states` tax instruments:**

| State | Purpose |
|-------|---------|
| `Value-added Tax` | VAT rate |
| `Income Tax` | Flat PIT rate (fallback) |
| `Profit Tax` | Corporate tax rate |
| `Employer Social Insurance Tax` | Employer SI contribution |
| `Employee Social Insurance Tax` | Employee SI deduction |
| `Capital Formation Tax` | Investment tax |
| `Export Tax` | Tax on exports |
| `Taxes Less Subsidies Rates` | Net tax rates by sector |
| `pit_thresholds` | Progressive PIT bracket thresholds |
| `pit_rates` | Progressive PIT marginal rates |
| `pit_basic_deduction` | Non-refundable basic personal amount |
| `unemployment_benefits_model` | Benefit computation model |
| `other_benefits_model` | Social transfer model |

---

## 2. Sequence diagram

Two key flows: updating benefits and computing taxes.

```mermaid
sequenceDiagram
    autonumber
    participant Country
    participant CG as CentralGovernment
    participant SocFn as functions["social_benefits"]
    participant TS as TimeSeries

    Note over Country,CG: Benefit updates
    Country->>CG: update_benefits(historic_ppi, exogenous_ppi, est_inflation, unemployment, growth)
    CG->>SocFn: compute_unemployment_benefits(prev_benefits, ppi, growth, unemployment, model)
    SocFn-->>CG: new_unemployment_benefits
    CG->>SocFn: compute_regular_transfer_to_households(prev_transfers, ppi, growth, unemployment, model)
    SocFn-->>CG: new_other_benefits
    CG->>TS: append unemployment_benefits_by_individual
    CG->>TS: append total_other_benefits

    Note over Country,CG: Tax computation
    Country->>CG: compute_taxes(employee_income, rent, financial_income, ...)
    CG->>CG: Taxes on production = sum(tax_rate * production * price)
    CG->>CG: VAT = vat_rate * sum(consumption)
    CG->>CG: Capital formation tax
    CG->>CG: Corporate income tax
    CG->>CG: Export tax
    CG->>CG: Personal income tax (progressive or flat)
    CG->>TS: append all tax revenues
```

---

## 3. State diagram

The fiscal stance is determined by the budget balance.

```mermaid
stateDiagram-v2
    [*] --> FiscalNeutral : simulation start

    state "Budget balance" as BALANCE {
        Surplus : revenue > expenditure
        Deficit : revenue < expenditure
        Balanced : revenue ≈ expenditure

        Surplus --> Deficit : spending rises / revenue falls
        Deficit --> Surplus : spending cut / revenue rises
    }

    FiscalNeutral --> BALANCE : each tick
```

---

## 4. Activity diagram

One government tick: update benefits → distribute to individuals → collect taxes.

```mermaid
flowchart TD
    Start([Start of tick]) --> A[Update unemployment benefits]
    A --> B[Update other social transfers]
    B --> C[Distribute unemployment benefits to eligible individuals]
    C --> D[Compute production taxes]
    D --> E[Compute VAT]
    E --> F[Compute capital formation tax]
    F --> G[Compute corporate income tax]
    G --> H[Compute export tax]
    H --> I[Compute personal income tax]
    I --> J[Optionally: inflate PIT bracket thresholds]
    J --> End([End of tick])

    subgraph PARALLEL [Tax components computed concurrently]
        direction LR
        T1[production]
        T2[VAT]
        T3[capital formation]
        T4[corporate]
        T5[export]
        T6[personal income]
    end
    D & E & F & G & H & I --- PARALLEL
```

---

*See also:* [Individuals UML demo](uml_individual_agent_demo.md), [Bersini (2012)](https://www.jasss.org/15/1/9.html).
