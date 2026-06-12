# UML: Country Orchestrator — Progressive PIT Update

This page documents the `Country` class in the progressive PIT branch.

**PIT impact**: 🟡 **Modified.** The `Country.__init__()` now includes a **pre-calibration step**
at t=0 that computes the effective tax rate from the initial income distribution when a
progressive PIT schedule is configured. This eliminates a calibration shock at simulation start.

---

## 1. Class diagram

```mermaid
classDiagram
    direction TB

    class Country {
        +country_name: str
        +scale: int
        +individuals: Individuals
        +households: Households
        +firms: Firms
        +central_government: CentralGovernment
        +government_entities: GovernmentEntities
        +banks: Banks
        +central_bank: CentralBank
        +economy: Economy
        +labour_market: LabourMarket
        +housing_market: HousingMarket
        +credit_market: CreditMarket
        +exogenous: Exogenous
        +from_pickled_country(...)$
        +reset(config)
        +initialisation_phase(exchange_rate)
        +estimation_phase()
        +target_setting_phase()
        +clear_labour_market()
        +update_planning_metrics()
        +prepare_housing_market_clearing()
        +clear_housing_market()
        +prepare_credit_market_clearing()
        +clear_credit_market()
        +prepare_goods_market_clearing()
        +update_realised_metrics()
        +update_population_structure()
    }

    class CentralGovernment {
        +functions: dict
        +pit_base_thresholds: ndarray
        +pit_base_basic_deduction: float
        +compute_taxes(...)
        +step_pit_brackets(tax_year, cpi_map, base_year)
    }

    Country *-- CentralGovernment
```

---

## 2. PIT change: Pre-calibration at t=0 🆕

```mermaid
sequenceDiagram
    participant Sim as Simulation.from_datawrapper()
    participant C as Country.__init__()
    participant CG as CentralGovernment

    Sim->>C: from_pickled_country(...)
    C->>CG: from_pickled_agent(config)

    alt Progressive schedule configured 🆕
        Note over C: Generate synthetic initial employee<br/>income distribution from Individuals
        C->>C: Compute progressive tax on initial distribution<br/>using pit_thresholds / pit_rates
        C->>C: effective_rate = initial_progressive_tax / initial_income
        C->>CG: states["Income Tax"] = effective_rate
        Note over C: Eliminates calibration shock:<br/>wage-setting & after-tax<br/>calculations aligned at t=0
    else Flat tax
        Note over C: No pre-calibration needed<br/>scalar already correct from TaxData
    end
```

**Why this matters**: Without pre-calibration, the scalar `Income Tax` (e.g., 20% flat)
would be used for wage-setting while progressive brackets compute actual tax. This mismatch
would cause a one-time shock at t=0. Pre-calibration computes the effective rate that the
progressive schedule would produce on the initial income distribution, and writes that back
into the scalar.
