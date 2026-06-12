# UML: System-Wide Architecture — Original Upstream Design

This page shows the full model architecture from the original upstream
[`uvic-sesit/macroabm-ca`](https://github.com/uvic-sesit/macroabm-ca) design.
All agents, markets, and their relationships are shown across the three
cross-agent diagram types from Bersini (2012).

Reference: Bersini, H. (2012). [*UML for ABM*](https://www.jasss.org/15/1/9.html). JASSS 15(1)9.

---

## 1. Cross-agent class diagram (structural skeleton)

All agent classes, markets, and the `Country` / `Simulation` orchestrator.

```mermaid
classDiagram
    direction TB

    class Simulation {
        +countries: dict[str, Country]
        +goods_market: GoodsMarket
        +exchange_rates: ExchangeRates
        +rest_of_the_world: RestOfTheWorld
        +timestep: Timestep
        +prehooks: list[Callable]
        +posthooks: list[Callable]
        +iterate(t)
        +run()
    }

    class Country {
        +country_name: str
        +scale: int
        +individuals: Individuals
        +households: Households
        +firms: Firms
        +banks: Banks
        +central_bank: CentralBank
        +central_government: CentralGovernment
        +government_entities: GovernmentEntities
        +economy: Economy
        +labour_market: LabourMarket
        +housing_market: HousingMarket
        +credit_market: CreditMarket
        +exogenous: Exogenous
        +initialisation_phase()
        +estimation_phase()
        +target_setting_phase()
        +clear_labour_market()
        +update_planning_metrics()
        +clear_housing_market()
        +clear_credit_market()
        +prepare_goods_market_clearing()
    }

    class Economy {
        +ts: TimeSeries
        +set_estimates()
    }

    class GoodsMarket {
        +prepare()
        +clear()
        +record()
    }

    class LabourMarket {
        +clear(firms, households, individuals)
    }

    class HousingMarket {
        +clear(...)
    }

    class CreditMarket {
        +clear(...)
    }

    class ExchangeRates {
        +get_current_exchange_rates_from_usd_to_lcu()
    }

    class RestOfTheWorld {
        +update_planning_metrics()
        +record_bought_goods()
    }

    class Exogenous {
        +national_accounts_before
        +national_accounts_during
        +inflation_before
    }

    %% Agent classes (simplified)
    class Individuals {
        +states: dict
        +ts: TimeSeries
    }

    class Households {
        +functions: dict
        +ts: TimeSeries
        +consumption_weights: ndarray
        +investment_weights: ndarray
    }

    class Firms {
        +functions: dict
        +ts: FirmTimeSeries
        +n_industries: int
        +base_intermediate_inputs_productivity_matrix
        +base_capital_inputs_productivity_matrix
    }

    class Banks {
        +ts: TimeSeries
    }

    class CentralBank {
        +ts: TimeSeries
        +policy_rate: float
    }

    class CentralGovernment {
        +functions: dict
        +states: dict
        +compute_taxes(...)
        +compute_revenue(...)
        +compute_deficit(...)
        +compute_debt()
    }

    class GovernmentEntities {
        +ts: TimeSeries
        +n_industries: int
    }

    Simulation *-- "*" Country
    Simulation *-- GoodsMarket
    Simulation *-- ExchangeRates
    Simulation *-- RestOfTheWorld
    Country *-- Individuals
    Country *-- Households
    Country *-- Firms
    Country *-- Banks
    Country *-- CentralBank
    Country *-- CentralGovernment
    Country *-- GovernmentEntities
    Country *-- Economy
    Country *-- LabourMarket
    Country *-- HousingMarket
    Country *-- CreditMarket
    Country *-- Exogenous
```

---

## 2. Cross-agent sequence diagram — one timestep (`iterate`)

```mermaid
sequenceDiagram
    participant Sim as Simulation
    participant ER as ExchangeRates
    participant C as Country
    participant E as Economy
    participant F as Firms
    participant H as Households
    participant Ind as Individuals
    participant LM as LabourMarket
    participant HM as HousingMarket
    participant CM as CreditMarket
    participant CG as CentralGovernment
    participant GE as GovernmentEntities
    participant CB as CentralBank
    participant B as Banks
    participant GM as GoodsMarket
    participant ROW as RestOfTheWorld

    Sim->>Sim: run_prehooks()
    Sim->>ER: get_current_exchange_rates()

    loop Each country
        Sim->>C: initialisation_phase(exchange_rate)
        C->>F: update_number_of_firms()
        Sim->>C: estimation_phase()
        C->>E: set_estimates(...)
        C->>F: set_estimates(growth, prev_prices)
        Sim->>C: target_setting_phase()
        C->>F: set_targets(...)
        C->>H: compute_employee_income(...)
        C->>Ind: update_activity_status(...)
        Sim->>C: clear_labour_market()
        C->>LM: clear(firms, households, individuals)
        Sim->>C: update_planning_metrics()
        C->>CB: set_policy_rate(...)
        C->>F: set_prices(...)
        C->>GE: set_government_quantity_spent(...)
        C->>CG: update_benefits(...)
        C->>CG: compute_taxes(...)
    end

    loop Each country
        Sim->>C: clear_housing_market()
        C->>HM: clear(...)
        Sim->>C: clear_credit_market()
        C->>CM: clear(...)
        Sim->>C: prepare_goods_market_clearing()
        C->>F: compute_demand_for_goods(...)
        C->>H: compute_consumption_demand(...)
    end

    Sim->>GM: prepare()
    Sim->>ROW: update_planning_metrics(...)
    Sim->>GM: clear()
    Sim->>GM: record()

    Sim->>ROW: record_bought_goods()
    loop Each country
        Sim->>C: update_realised_metrics()
        Sim->>C: update_population_structure()
    end

    Sim->>Sim: run_posthooks(t, year, month)
```

---

## 3. Activity diagram — `Country` phase progression

```mermaid
flowchart TD
    subgraph "Per-timestep iteration"
        A[initialisation_phase] --> B[estimation_phase]
        B --> C[target_setting_phase]
        C --> D[clear_labour_market]
        D --> E[update_planning_metrics]
        E --> F[clear_housing_market]
        F --> G[clear_credit_market]
        G --> H[prepare_goods_market_clearing]
    end

    H --> I[GoodsMarket.clear]
    I --> J[update_realised_metrics]
    J --> K[update_population_structure]
    K --> L[Next timestep]
```

---

## 4. Configuration overview — upstream minimal design

The upstream configuration classes are minimal. `CentralGovernmentConfiguration` has
only two sub-configs (`social_benefits` and `social_housing`) with no tax-related fields
(all tax rates come from the data, not configuration).

```mermaid
classDiagram
    class SimulationConfiguration {
        +t_max: int
        +country_configurations: dict
        +goods_market_configuration: GoodsMarketConfiguration
        +exchange_rates_configuration
        +row_configuration
        +seed: Optional[int]
    }

    class CountryConfiguration {
        +individuals: IndividualsConfiguration
        +households: HouseholdsConfiguration
        +firms: FirmsConfiguration
        +banks: BanksConfiguration
        +central_bank: CentralBankConfiguration
        +central_government: CentralGovernmentConfiguration
        +government_entities: GovernmentEntitiesConfiguration
        +economy: EconomyConfiguration
        +labour_market: LabourMarketConfiguration
        +credit_market: CreditMarketConfiguration
        +housing_market: HousingMarketConfiguration
        +forecasting_window: int
        +assume_zero_growth: bool
        +assume_zero_noise: bool
    }

    class CentralGovernmentConfiguration {
        +functions: CentralGovernmentFunctions
    }

    class CentralGovernmentFunctions {
        +social_benefits: SocialBenefits
        +social_housing: SocialHousing
    }

    SimulationConfiguration *-- "*" CountryConfiguration
    CountryConfiguration *-- CentralGovernmentConfiguration
    CentralGovernmentConfiguration *-- CentralGovernmentFunctions
```

> **Tax data flows from `TaxData` not configuration**: Tax rates (`Value-added Tax`,
> `Income Tax`, `Profit Tax`, etc.) are extracted from macro data during
> `CentralGovernment.from_pickled_agent()` and stored in `states`. They are not
> configurable via the configuration system in the upstream design.
