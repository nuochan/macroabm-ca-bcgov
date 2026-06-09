# UML Demo: The `GovernmentEntities` Agent

This page applies Bersini's four-diagram UML subset to the [`GovernmentEntities`](../../macromodel/agents/government_entities/government_entities.py)
agent — government organizations that consume and invest. See the [Individuals UML demo](uml_individual_agent_demo.md)
for methodology references.

Reference: Bersini, H. (2012). [*UML for ABM*](https://www.jasss.org/15/1/9.html). JASSS 15(1)9.

---

## 1. Class diagram

`GovernmentEntities` inherits from `Agent`, aggregates a single `consumption` strategy,
and participates in goods markets as a buyer only (seller side is inactive).

```mermaid
classDiagram
    class Agent {
        <<abstract>>
        +country_name: str
        +states: dict
        +ts: TimeSeries
        +prepare()
        +set_goods_to_buy()
        +set_goods_to_sell()
    }

    class GovernmentEntities {
        +functions: dict
        +from_pickled_agent(...)$
        +reset(config)
        +prepare_buying_goods(exogenous_before, exogenous_during, ...)
        +prepare_selling_goods(n_industries)
        +prepare_goods_market_clearing(...)
        +save_to_h5(group)
    }

    class ConsumptionFunction {
        +compute_target_consumption(previous_desired, model, historic, ...)
    }

    Agent <|-- GovernmentEntities
    GovernmentEntities "1" o-- "*" ConsumptionFunction : functions["consumption"]
```

---

## 2. Sequence diagram

A single dominant flow: preparing for goods market clearing.

```mermaid
sequenceDiagram
    autonumber
    participant Country
    participant GE as GovernmentEntities
    participant ConsFn as functions["consumption"]
    participant TS as TimeSeries

    Country->>GE: prepare_goods_market_clearing(exchange_rate, exogenous, ...)
    GE->>GE: set_exchange_rate(usd_to_lcu)
    GE->>GE: prepare_buying_goods(exogenous, initial_prices, current_prices, ...)
    GE->>TS: historic("total_consumption")
    TS-->>GE: historic_cons
    GE->>ConsFn: compute_target_consumption(prev_desired, model, historic, prices, ...)
    ConsFn-->>GE: desired_consumption_in_lcu
    GE->>GE: set_goods_to_buy(desired_consumption / n_entities)
    GE->>GE: prepare_selling_goods(n_industries)
    GE->>GE: set_goods_to_sell(zeros), set_prices(zeros)
```

---

## 3. State diagram

Government entities have no complex lifecycle; their state is captured by exogenous path vs. model-driven consumption.

```mermaid
stateDiagram-v2
    [*] --> Active : simulation start

    state "Consumption mode" as MODE {
        Exogenous : exogenous path provided
        ModelDriven : consumption model active
        ZeroGrowth : assume_zero_growth = true

        ModelDriven --> Exogenous : exogenous path supplied
        Exogenous --> ModelDriven : exogenous path exhausted
        ModelDriven --> ZeroGrowth : assume_zero_growth flag
        ZeroGrowth --> ModelDriven : flag cleared
    }

    Active --> MODE : each tick
```

---

## 4. Activity diagram

```mermaid
flowchart TD
    Start([Start of tick]) --> A[Set exchange rate]
    A --> B{Exogenous consumption?}
    B -- yes --> C[Use exogenous path for historic consumption]
    B -- no --> D[Use time series historic consumption]
    C --> E{Assume zero growth?}
    D --> E
    E -- yes --> F[Use initial consumption as target]
    E -- no --> G[Compute target consumption via model]
    F --> H[Convert to USD and divide across entities]
    G --> H
    H --> I[Set goods_to_buy per entity]
    I --> J[Set goods_to_sell = zeros (buyer only)]
    J --> End([End of tick])
```

---

*See also:* [Central Government UML demo](uml_central_government_agent_demo.md), [Bersini (2012)](https://www.jasss.org/15/1/9.html).
