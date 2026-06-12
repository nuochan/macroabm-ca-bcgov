# UML: GovernmentEntities Agent — Original Upstream Design

This page documents the `GovernmentEntities` agent from the original upstream
[`uvic-sesit/macroabm-ca`](https://github.com/uvic-sesit/macroabm-ca) design.

`GovernmentEntities` represent multiple government organizations that consume
goods and services, participate in goods markets as buyers, and optionally
track emissions.

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

    class GovernmentEntities {
        +functions: dict
        +from_pickled_agent(...)$
        +reset(config)
        +prepare_buying_goods(...)
        +prepare_selling_goods(n_industries)
        +prepare_goods_market_clearing(...)
        +record_consumption(...)
        +save_to_h5(group)
        +total_consumption() ndarray
        +emissions() ndarray
        +disaggregated_emissions(input_name) ndarray
    }

    Agent <|-- GovernmentEntities
```

**Key `states` attributes:**

| State | Type | Purpose |
|-------|------|---------|
| `government_consumption_model` | object | Consumption forecasting model |

---

## 2. Activity diagram — goods market participation

```mermaid
flowchart TD
    A[prepare_goods_market_clearing] --> B[set_exchange_rate]
    B --> C[prepare_buying_goods]
    C --> D{"exogenous<br/>consumption?"}
    D -->|Yes| E[Use exogenous path]
    D -->|No| F["Compute target consumption<br/>via government_consumption_model"]
    E --> G[Set desired_consumption_in_lcu]
    F --> G
    G --> H[Convert to USD]
    H --> I[Distribute across entities]
    I --> J[set_goods_to_buy]
    J --> K[prepare_selling_goods: empty]
```
