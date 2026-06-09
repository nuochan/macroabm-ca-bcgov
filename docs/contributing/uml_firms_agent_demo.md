# UML Demo: The `Firms` Agent

This page applies Bersini's four-diagram UML subset to the [`Firms`](../../macromodel/agents/firms/firms.py)
agent — the productive sector of the economy. See the [Individuals UML demo](uml_individual_agent_demo.md) for
methodology references.

Reference: Bersini, H. (2012). [*UML for ABM*](https://www.jasss.org/15/1/9.html). JASSS 15(1)9.

---

## 1. Class diagram

The `Firms` agent inherits from `Agent`, owns a `FirmTimeSeries` (subclass of `TimeSeries`),
and aggregates 21 pluggable strategy classes from
[`macromodel/agents/firms/func/`](../../macromodel/agents/firms/func/). It holds an I/O productivity
table (`base_intermediate_inputs_productivity_matrix`), capital depreciation structure,
and a substitution `bundle_matrix`.

```mermaid
classDiagram
    class Agent {
        <<abstract>>
        +country_name: str
        +states: dict
        +ts: TimeSeries
        +initiate_ts()
        +prepare()
        +set_prices()
        +set_goods_to_buy()
        +set_goods_to_sell()
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
        +emission_fractions: EmissionFractions
        +from_pickled_agent(...)$
        +reset(config)
        +update_number_of_firms()
        +set_estimates(growth, prev_prices)
        +compute_estimated_growth_by_firm(...)
        +compute_estimated_demand(growth)
        +get_effective_intermediate_coefficients()
        +get_effective_capital_coefficients()
    }

    class FirmTimeSeries {
        +current(name)
        +historic(name)
        +append(value)
        +n_firms
        +n_firms_by_industry
        +estimated_growth_by_firm
        +estimated_demand
    }

    class FirmsConfiguration {
        +functions
        +parameters
        +substitution_bundles
    }

    class TargetProduction {
        +compute_target_production(...)
    }
    class Production {
        +compute_production(...)
    }
    class DemandEstimator {
        +compute_estimated_demand(...)
    }
    class GrowthEstimator {
        +compute_estimated_growth(...)
    }
    class PriceSetter {
        +set_prices(...)
    }
    class WageSetter {
        +set_wages(...)
    }
    class OfferedWageSetter {
        +set_offered_wages(...)
    }
    class DesiredLabour {
        +compute_desired_labour(...)
    }
    class DemandForGoods {
        +compute_demand_for_goods(...)
    }
    class TargetIntermediateInputs {
        +compute_target_intermediate_inputs(...)
    }
    class TargetCapitalInputs {
        +compute_target_capital_inputs(...)
    }
    class TargetCredit {
        +compute_target_credit(...)
    }
    class ProfitEstimator {
        +compute_estimated_profits(...)
    }
    class LabourProductivity {
        +compute_labour_productivity(...)
    }
    class ProductivityGrowth {
        +compute_productivity_growth(...)
    }
    class ProductivityInvestmentPlanner {
        +plan_productivity_investment(...)
    }
    class TechnicalCoefficientsGrowth {
        +compute_technical_coefficients_growth(...)
    }
    class BoughtGoodsDistributor {
        +distribute_bought_goods(...)
    }
    class ExcessDemand {
        +compute_excess_demand(...)
    }
    class Demography {
        +update(...)
    }

    Agent <|-- Firms
    Firms "1" *-- "1" FirmTimeSeries : owns
    Firms ..> FirmsConfiguration : configured by
    Firms "1" o-- "*" TargetProduction : functions["target_production"]
    Firms "1" o-- "*" Production : functions["production"]
    Firms "1" o-- "*" DemandEstimator : functions["demand_estimator"]
    Firms "1" o-- "*" GrowthEstimator : functions["growth_estimator"]
    Firms "1" o-- "*" PriceSetter : functions["prices"]
    Firms "1" o-- "*" WageSetter : functions["wages"]
    Firms "1" o-- "*" OfferedWageSetter : functions["offered_wages"]
    Firms "1" o-- "*" DesiredLabour : functions["desired_labour"]
    Firms "1" o-- "*" DemandForGoods : functions["demand_for_goods"]
    Firms "1" o-- "*" TargetIntermediateInputs : functions["target_intermediate_inputs"]
    Firms "1" o-- "*" TargetCapitalInputs : functions["target_capital_inputs"]
    Firms "1" o-- "*" TargetCredit : functions["target_credit"]
    Firms "1" o-- "*" ProfitEstimator : functions["profit_estimator"]
    Firms "1" o-- "*" LabourProductivity : functions["labour_productivity"]
    Firms "1" o-- "*" ProductivityGrowth : functions["productivity_growth"]
    Firms "1" o-- "*" ProductivityInvestmentPlanner : functions["productivity_investment_planner"]
    Firms "1" o-- "*" TechnicalCoefficientsGrowth : functions["technical_coefficients_growth"]
    Firms "1" o-- "*" BoughtGoodsDistributor : functions["bought_goods_distributor"]
    Firms "1" o-- "*" ExcessDemand : functions["excess_demand"]
    Firms "1" o-- "*" Demography : functions["demography"]
```

---

## 2. Sequence diagram

Traces one tick from `set_estimates` through to production and goods-market participation.
The firm estimates demand, plans production, acquires intermediate/capital inputs, sets wages,
hires labour, produces, sets prices, and enters goods market clearing.

```mermaid
sequenceDiagram
    autonumber
    participant Sim
    participant Country
    participant F as Firms
    participant ProdFn as functions["target_production"]
    participant GCFn as functions["demand_for_goods"]
    participant PriceFn as functions["prices"]
    participant WageFn as functions["wages"]
    participant TS as FirmTimeSeries

    Sim->>Country: step(t)
    Country->>F: set_estimates(estimated_growth, prev_prices)
    F->>TS: current("production")
    TS-->>F: prev_production
    Country->>F: compute_estimated_growth_by_firm(prev_prices)
    F->>TS: append estimated_growth_by_firm

    Note over Country,F: Production planning
    Country->>F: compute_estimated_demand(growth)
    F->>ProdFn: compute_target_production(estimated_demand, ...)
    ProdFn-->>F: target_production
    F->>TS: append target_production

    Country->>F: prepare goods market
    F->>GCFn: compute_demand_for_goods(...)
    GCFn-->>F: intermediate_inputs_demand
    F->>F: set_goods_to_buy(inputs_demand)
    F->>F: set_goods_to_sell(target_production + inventory)

    Country->>F: set offered wages
    F->>WageFn: compute_offered_wages(...)
    WageFn-->>F: offered_wages_by_firm

    Note over Country,F: After market clearing
    Country->>F: compute production
    F->>ProdFn: compute_production(realised_inputs, ...)
    ProdFn-->>F: output

    Country->>F: set prices
    F->>PriceFn: compute_prices(costs, target_markup, ...)
    PriceFn-->>F: new_prices
```

---

## 3. State diagram

A firm's life-cycle revolves around its solvency status and market position.
Two key state machines exist: insolvency and production planning mode.

```mermaid
stateDiagram-v2
    [*] --> Active : firm created / simulation starts

    state "Operating modes" as OPS {
        Planning : planning inputs & labour
        Producing : producing goods
        Selling : in goods market
        Investing : capital/tech investment

        Planning --> Producing : inputs acquired
        Producing --> Selling : goods produced
        Selling --> Planning : next tick
        Producing --> Investing : productivity gap detected
        Investing --> Planning : investment made
    }

    Active --> OPS : each tick
    OPS --> Active : completes

    Active --> Insolvent : equity < 0 or unable to service debt
    Insolvent --> [*] : firm exit / liquidation
    Active --> [*] : firm exit
```

---

## 4. Activity diagram

Procedural flow of one firm tick: from estimates through to prices.

```mermaid
flowchart TD
    Start([Start of tick]) --> A[set_estimates: growth, demand]
    A --> B[compute_target_production]
    B --> C[compute_target_intermediate_inputs]
    B --> D[compute_target_capital_inputs]
    C --> E[compute_demand_for_goods]
    D --> E
    E --> F[compute_target_credit]
    F --> G[set offered wages & desired labour]
    G --> H{Labour market clears}
    H --> I[Goods market: buy inputs, sell output]
    I --> J[compute production & profits]
    J --> K[compute excess demand]
    K --> L[set prices for next period]
    L --> M[update demography: firm births/deaths]
    M --> End([End of tick])

    subgraph PARALLEL [Concurrent: Labour & Productivity]
        direction LR
        P1[compute_labour_productivity]
        P2[compute_productivity_growth]
        P3[plan_productivity_investment]
        P4[compute_technical_coefficients_growth]
    end
    J --- PARALLEL
```

---

*See also:* [Individuals UML demo](uml_individual_agent_demo.md), [Bersini (2012)](https://www.jasss.org/15/1/9.html).
