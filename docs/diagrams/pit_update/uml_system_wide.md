# UML: System-Wide Integration — Progressive PIT Changes

This page shows the **diff** from the original upstream system architecture. It highlights
which components are modified, added, or unchanged by the progressive PIT update.

Compare with the [upstream system-wide diagram](../upstream_model/uml_system_wide.md).

---

## 1. Change overview — components affected

```mermaid
flowchart LR
    subgraph NEW ["🆕 New Components"]
        pit_schedule[PITSchedule<br/>macro_data/readers/taxation/]
        bc_pit[BC_PIT_2014.csv<br/>spoof_data/freda/]
        bc_cpi[bc_cpi_inflation.csv<br/>spoof_data/freda/]
    end

    subgraph MODIFIED ["Modified Components"]
        cg_config[CentralGovernmentConfiguration<br/>+ pit_brackets<br/>+ pit_basic_deduction]
        cg_agent[CentralGovernment<br/>+ step_pit_brackets()<br/>+ pit_base_thresholds<br/>+ pit_base_basic_deduction]
        country[Country<br/>+ pre-calibration at t=0]
        run_sim[run_simulation.py<br/>+ CAN_BC region support<br/>+ posthook registration]
    end

    subgraph UNCHANGED ["Unchanged Components"]
        individuals[Individuals]
        firms[Firms]
        banks[Banks]
        central_bank[CentralBank]
        government_entities[GovernmentEntities]
        labour_market[LabourMarket]
        housing_market[HousingMarket]
        credit_market[CreditMarket]
        goods_market[GoodsMarket]
        economy[Economy]
        exogenous[Exogenous]
    end

    cg_config --> cg_agent
    pit_schedule --> cg_agent
    pit_schedule --> bc_pit
    pit_schedule --> bc_cpi
    cg_agent --> country
    run_sim --> country
```

---

## 2. Cross-agent class diagram — changes highlighted

Only `CentralGovernment` and `Country` are modified. All other agents unchanged.

```mermaid
classDiagram
    direction TB

    class Simulation {
        +countries: dict[str, Country]
        +goods_market: GoodsMarket
        +prehooks: list[Callable]
        +posthooks: list[Callable]
        +iterate(t)
        +run()
    }

    class Country {
        +country_name: str
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
        +initialisation_phase()
        +estimation_phase()
        +target_setting_phase()
        +clear_labour_market()
        +update_planning_metrics()
        +clear_housing_market()
        +clear_credit_market()
        +prepare_goods_market_clearing()
    }

    class CentralGovernment {
        +functions: dict
        +pit_base_thresholds: ndarray
        +pit_base_basic_deduction: float
        +compute_taxes(...)
        +step_pit_brackets(tax_year, cpi_map, base_year)
        +compute_revenue(...)
        +compute_deficit(...)
        +compute_debt()
    }

    class PITSchedule {
        +brackets_df: DataFrame
        +cpi_rates: dict
        +base_year: int
        +from_name_with_cpi(name)$ PITSchedule
        +get_brackets(tax_year) tuple
    }

    class compute_progressive_tax {
        +compute_progressive_tax(incomes, thresholds, rates) ndarray
    }

    Simulation *-- "*" Country
    Country *-- CentralGovernment
    CentralGovernment ..> PITSchedule : loads brackets + CPI
    CentralGovernment ..> compute_progressive_tax : uses in compute_taxes
```

---

## 3. Sequence diagram — one timestep with PIT changes highlighted

```mermaid
sequenceDiagram
    participant Sim as Simulation
    participant C as Country
    participant CG as CentralGovernment
    participant PIT as compute_progressive_tax
    participant GM as GoodsMarket

    Sim->>Sim: run_prehooks()
    loop Each country
        Sim->>C: initialisation_phase()
        Sim->>C: estimation_phase()
        Sim->>C: target_setting_phase()
        Sim->>C: clear_labour_market()
        Sim->>C: update_planning_metrics()
        C->>CG: update_benefits(...)
        C->>CG: compute_taxes(...)

        rect rgb(255, 245, 220)
            Note over CG,PIT: 🆕 Progressive PIT path
            alt pit_thresholds configured
                CG->>PIT: compute_progressive_tax(wages_after_si,<br/>pit_thresholds, pit_rates)
                PIT-->>CG: tax_by_individual
                CG->>CG: Apply basic_deduction credit
            else flat tax fallback
                CG->>CG: Flat Income_Tax on wages
            end
        end
    end

    loop Each country
        Sim->>C: clear_housing_market()
        Sim->>C: clear_credit_market()
        Sim->>C: prepare_goods_market_clearing()
    end

    Sim->>GM: prepare() / clear() / record()

    loop Each country
        Sim->>C: update_realised_metrics()
        Sim->>C: update_population_structure()
    end

    alt January (month==1)
        rect rgb(220, 235, 255)
            Note over Sim,CG: 🆕 Annual CPI indexation
            Sim->>CG: step_pit_brackets(tax_year, cpi_map, base_year)
            CG->>CG: Compound-inflate thresholds & deduction
        end
    end

    Sim->>Sim: run_posthooks(t, year, month)
```

---

## 4. Configuration diff — PIT fields added to `CentralGovernmentConfiguration`

```mermaid
classDiagram
    class CentralGovernmentConfiguration {
        +functions: CentralGovernmentFunctions
        +pit_brackets: Optional[list[tuple[float, float]]]
        +pit_basic_deduction: Optional[float]
    }

    class CentralGovernmentFunctions {
        +social_benefits: SocialBenefits
        +social_housing: SocialHousing
    }

    class SocialBenefits {
        +name: str
        +path_name: str
        +parameters: dict
    }

    class SocialHousing {
        +name: str
        +path_name: str
        +parameters: dict
    }

    CentralGovernmentConfiguration *-- CentralGovernmentFunctions
    CentralGovernmentFunctions *-- SocialBenefits
    CentralGovernmentFunctions *-- SocialHousing
```

> **🆕 Fields added** to `CentralGovernmentConfiguration`:
> - `pit_brackets: Optional[list[tuple[float, float]]]` — `None` = flat tax (backward compatible)
> - `pit_basic_deduction: Optional[float]` — Non-refundable basic personal amount

---

## 5. Key design invariants (unchanged by PIT update)

| Invariant | Description |
|-----------|-------------|
| **Behavioural code uses scalar `Income Tax`** | Wage-setting, after-tax income, saving rates all read `states["Income Tax"]` |
| **Dual tracking** | `pit_thresholds`/`pit_rates` for progressive calc; `Income Tax` updated to effective rate each period |
| **Employee-only progressivity** | Only wages use brackets; rental & financial income stay flat |
| **Backward compatible** | `pit_brackets=None` → flat tax (original behaviour preserved) |
| **CPI indexation is compound** | `threshold = nominal × ∏(1+CPI_y)` — preserves nominal base for safe repeated calls |
| **Non-refundable credit** | Credit = `basic_deduction × lowest_marginal_rate`; tax cannot go below zero |
