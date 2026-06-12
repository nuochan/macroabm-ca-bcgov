# UML: Country Orchestrator — Original Upstream Design

This page documents the `Country` class from the original upstream
[`uvic-sesit/macroabm-ca`](https://github.com/uvic-sesit/macroabm-ca) design.
`Country` is the central orchestrator that wires together all agents and markets
for a single national economy.

Reference: Bersini, H. (2012). [*UML for ABM*](https://www.jasss.org/15/1/9.html). JASSS 15(1)9.

---

## 1. Class diagram — `Country` and owned components

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
        +credit_market: CreditMarket
        +housing_market: HousingMarket
        +exchange_rate_usd_to_lcu: float
        +exogenous: Exogenous
        +forecasting_window: int
        +configuration: CountryConfiguration
        +from_pickled_country(...)$
        +reset(config)
        +initialisation_phase(exchange_rate)
        +estimation_phase()
        +target_setting_phase()
        +clear_labour_market()
        +update_planning_metrics()
        +prepare_housing_market_clearing()
        +clear_housing_market()
        +process_housing_market_clearing()
        +prepare_credit_market_clearing()
        +clear_credit_market()
        +process_credit_market_clearing()
        +prepare_goods_market_clearing()
        +update_realised_metrics()
        +update_population_structure()
        +save_to_h5(f)
    }

    class Individuals {
        +country_name: str
        +states: dict
        +ts: TimeSeries
        +reset(config)
        +update_activity()
        +set_wages_income(wages)
        +set_unemployment_benefits(benefits)
    }

    class Households {
        +functions: dict
        +ts: TimeSeries
        +consumption_weights: ndarray
        +investment_weights: ndarray
        +reset(config)
        +compute_employee_income(individual_income)
        +compute_social_transfer_income(total_transfers, cpi)
        +compute_rental_income(housing_data, income_taxes)
        +compute_consumption_demand(...)
    }

    class Firms {
        +functions: dict
        +ts: FirmTimeSeries
        +n_industries: int
        +reset(config)
        +update_number_of_firms()
        +set_estimates(growth, prev_prices)
        +set_targets(...)
        +set_prices(...)
        +compute_demand_for_goods(...)
    }

    class CentralGovernment {
        +functions: dict
        +states: dict
        +pt_schedule: Optional[PITSchedule]
        +reset(config)
        +update_benefits(...)
        +distribute_unemployment_benefits(...)
        +compute_taxes(...)
        +compute_revenue(rent) float
        +compute_deficit(...)
        +compute_debt()
    }

    class GovernmentEntities {
        +ts: TimeSeries
        +reset(config)
        +set_government_quantity_spent(...)
    }

    class Banks {
        +ts: TimeSeries
        +reset(config)
    }

    class CentralBank {
        +ts: TimeSeries
        +policy_rate: float
        +reset(config)
        +set_policy_rate(...)
    }

    class Economy {
        +ts: TimeSeries
        +reset(config)
        +set_estimates(...)
    }

    class LabourMarket {
        +clear(firms, households, individuals)
    }

    class CreditMarket {
        +clear(...)
    }

    class HousingMarket {
        +clear(...)
    }

    class Exogenous {
        +national_accounts_before
        +national_accounts_during
        +reset()
    }

    Country *-- "1" Individuals
    Country *-- "1" Households
    Country *-- "1" Firms
    Country *-- "1" CentralGovernment
    Country *-- "1" GovernmentEntities
    Country *-- "1" Banks
    Country *-- "1" CentralBank
    Country *-- "1" Economy
    Country *-- "1" LabourMarket
    Country *-- "1" CreditMarket
    Country *-- "1" HousingMarket
    Country *-- "1" Exogenous
```

---

## 2. Sequence diagram — `Country.from_pickled_country()` initialisation

Shows the factory method that constructs a complete country from preprocessed data.

```mermaid
sequenceDiagram
    participant Sim as Simulation.from_datawrapper()
    participant C as Country.from_pickled_country()
    participant Ind as Individuals
    participant HH as Households
    participant F as Firms
    participant CG as CentralGovernment
    participant GE as GovernmentEntities
    participant B as Banks
    participant CB as CentralBank
    participant E as Economy
    participant LM as LabourMarket
    participant CM as CreditMarket
    participant HM as HousingMarket
    participant Exo as Exogenous

    Sim->>C: from_pickled_country(synthetic_country, config, ...)

    C->>Ind: from_pickled_agent(synthetic_population, config)
    C->>HH: from_pickled_agent(synthetic_population, synthetic_country, config)
    C->>F: from_pickled_agent(synthetic_firms, config)
    C->>CG: from_pickled_agent(synthetic_central_government, config,<br/>taxes_net_subsidies, n_unemployed, tax_data)
    C->>GE: from_pickled_agent(synthetic_government_entities, config)
    C->>B: from_pickled_agent(synthetic_banks, config)
    C->>CB: from_pickled_agent(synthetic_central_bank, config)
    C->>Exo: from_pickled_agent(synthetic_country, exchange_rates)
    C->>E: from_agents(individuals, firms, central_government, ...)
    C->>LM: from_agents(individuals, config)
    C->>CM: from_pickled_market(synthetic_credit_market, config)
    C->>HM: from_pickled_market(synthetic_housing_market, config)

    C-->>Sim: Country(...)
```

---

## 3. Activity diagram — `Country` simulation phases

```mermaid
flowchart TD
    subgraph Phase1 ["Phase 1: Initialisation"]
        A1[update_number_of_firms] --> A2[Set exchange_rate_usd_to_lcu]
    end

    subgraph Phase2 ["Phase 2: Estimation"]
        B1[Economy.set_estimates] --> B2[Firms.set_estimates]
    end

    subgraph Phase3 ["Phase 3: Target Setting"]
        C1[Firms.set_targets] --> C2[Households.compute_employee_income]
        C2 --> C3[Individuals.update_activity_status]
    end

    subgraph Phase4 ["Phase 4: Labour Market"]
        D1[LabourMarket.clear]
    end

    subgraph Phase5 ["Phase 5: Planning Update"]
        E1[CentralBank.set_policy_rate] --> E2[Firms.set_prices]
        E2 --> E3[GovernmentEntities.set_quantity_spent]
        E3 --> E4[CentralGovernment.update_benefits]
        E4 --> E5[CentralGovernment.compute_taxes]
    end

    subgraph Phase6 ["Phase 6: Housing & Credit"]
        F1[HousingMarket.clear] --> F2[CreditMarket.clear]
    end

    subgraph Phase7 ["Phase 7: Goods Market Prep"]
        G1[Firms.compute_demand_for_goods] --> G2[Households.compute_consumption_demand]
    end

    Phase1 --> Phase2
    Phase2 --> Phase3
    Phase3 --> Phase4
    Phase4 --> Phase5
    Phase5 --> Phase6
    Phase6 --> Phase7
```
