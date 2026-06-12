# UML: Firms Agent — Original Upstream Design

This page documents the `Firms` agent from the original upstream
[`uvic-sesit/macroabm-ca`](https://github.com/uvic-sesit/macroabm-ca) design.

`Firms` represent the productive sector — producing goods using labor,
intermediate inputs, and capital. They set prices, hire workers, manage
inventory, and make investment decisions across multiple industries.

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

    class Firms {
        +functions: dict
        +n_industries: int
        +industries: list[str]
        +base_intermediate_inputs_productivity_matrix: ndarray
        +base_capital_inputs_productivity_matrix: ndarray
        +base_capital_inputs_depreciation_matrix: ndarray
        +goods_criticality_matrix: ndarray
        +depreciation_rates: ndarray
        +capital_inputs_delay: ndarray
        +substitution_bundles: ndarray
        +configuration: FirmsConfiguration
        +average_initial_price: ndarray
        +from_pickled_agent(...)$
        +reset(config)
        +update_number_of_firms()
        +set_estimates(growth, prev_prices)
        +set_targets(bank_rate, ...)
        +set_prices(...)
        +set_wages(...)
        +compute_demand_for_goods(...)
        +compute_production(...)
        +get_effective_intermediate_coefficients() ndarray
        +get_effective_capital_coefficients() ndarray
    }

    class FirmTimeSeries {
        +current(name)
        +historic(name)
        +n_firms
        +n_firms_by_industry
        +estimated_growth_by_firm
        +estimated_demand
        +production
        +price
        +inventory
    }

    Agent <|-- Firms
    Firms *-- FirmTimeSeries : ts
```

**Key `states` attributes:**

| State | Type | Purpose |
|-------|------|---------|
| `Industry` | ndarray | Industry per firm |
| `Corresponding Bank ID` | ndarray | Bank relationship |
| `Employments` | list | Employee IDs per firm |
| `is_insolvent` | ndarray | Bankruptcy flag |
| `Excess Demand` | ndarray | Unmet demand |
| `Labour Productivity by Industry` | ndarray | Productivity |
| `tfp_multiplier` | ndarray | TFP adjustment |
| `intermediate_tech_multipliers` | ndarray | Input efficiency |
| `capital_tech_multipliers` | ndarray | Capital efficiency |

---

## 2. Sequence diagram — production cycle

```mermaid
sequenceDiagram
    participant C as Country
    participant F as Firms
    participant Func as Strategy Functions

    C->>F: set_estimates(growth, prev_prices)
    F->>F: compute_estimated_growth_by_firm(prev_prices)
    F->>F: compute_estimated_demand(growth)

    C->>F: set_targets(bank_rate, ...)
    F->>Func: target_production.compute_target_production(...)
    F->>Func: prices.set_prices(...)
    F->>Func: wages.set_wages(...)
    F->>Func: desired_labour.compute_desired_labour(...)
    F->>Func: demand_for_goods.compute_demand_for_goods(...)
```
