# UML: Package Diagram — Progressive PIT Update

This page shows high-level package dependencies after the PIT update, highlighting
the new `personal_income_tax` sub-package and modified modules.

Compare with the [upstream package diagram](../upstream_model/uml_package.md).

---

## Package dependency diagram (with PIT changes)

```mermaid
flowchart LR
    subgraph TopLevel ["Top-Level Orchestration"]
        sim[Simulation] --> country[Country]
    end

    subgraph Agents ["Agent Layer"]
        individuals[Individuals 🟢]
        households[Households 🟢]
        firms[Firms 🟢]
        banks[Banks 🟢]
        central_bank[CentralBank 🟢]
        central_gov["CentralGovernment 🔴"]
        gov_entities[GovernmentEntities 🟢]
    end

    subgraph NewModule ["🆕 PIT Module"]
        pit_schedule[PITSchedule]
        pit_compute[compute_progressive_tax]
        pit_schedule --> pit_compute
    end

    subgraph Markets ["Market Layer"]
        labour[LabourMarket]
        housing[HousingMarket]
        credit[CreditMarket]
        goods[GoodsMarket]
    end

    subgraph Economy ["Economy & Support"]
        economy[Economy]
        exogenous[Exogenous]
        exchange_rates[ExchangeRates]
        row[RestOfTheWorld]
    end

    subgraph Config ["Configuration Layer"]
        country_config["CountryConfiguration"]
        cg_config["CentralGovernmentConfiguration<br/>🆕 +pit_brackets<br/>🆕 +pit_basic_deduction"]
    end

    subgraph DataLayer ["Macro Data Layer"]
        macro_data[macro_data package]
        pit_data["🆕 personal_income_tax<br/>sub-package"]
        spoof_data["🆕 spoof_data/freda/<br/>BC_PIT_2014.csv<br/>bc_cpi_inflation.csv"]
    end

    country --> Agents
    country --> Markets
    country --> Economy
    country --> Config
    sim --> goods
    sim --> exchange_rates
    sim --> row
    central_gov --> NewModule
    NewModule --> pit_data
    pit_data --> spoof_data
    central_gov --> cg_config
```

---

## Files added/modified by PIT update

```mermaid
flowchart TD
    subgraph New ["🆕 New files"]
        A1["macro_data/readers/taxation/<br/>personal_income_tax/<br/>pit_schedule.py"]
        A2["spoof_data/freda/<br/>BC_PIT_2014.csv"]
        A3["spoof_data/freda/<br/>bc_cpi_inflation.csv"]
    end

    subgraph Modified ["Modified files"]
        B1["macromodel/agents/central_government/<br/>central_government.py<br/>+ compute_taxes (progressive path)<br/>+ step_pit_brackets<br/>+ pit_base_thresholds/deduction"]
        B2["macromodel/configurations/<br/>central_government_configuration.py<br/>+ pit_brackets: Optional[list[tuple]]<br/>+ pit_basic_deduction: Optional[float]"]
        B3["macromodel/country/<br/>country.py<br/>+ pre-calibration at t=0"]
        B4["test_run/<br/>run_simulation.py<br/>+ CAN_BC region support<br/>+ posthook for annual CPI indexation"]
        B5["test_run/<br/>compare_can_bc.py<br/>+ comparison script"]
        B6["test_run/<br/>inspect_income.py<br/>+ progressive tax inspection"]
    end

    subgraph Unchanged ["Unchanged packages"]
        C1["macromodel/agents/individuals/"]
        C2["macromodel/agents/households/"]
        C3["macromodel/agents/firms/"]
        C4["macromodel/agents/banks/"]
        C5["macromodel/agents/central_bank/"]
        C6["macromodel/agents/government_entities/"]
        C7["macromodel/markets/"]
        C8["macromodel/economy/"]
        C9["macromodel/exogenous/"]
    end
```

---

## Tax data flow — progressive PIT path

```
macro_data/TaxData                           ← Flat rates (from data)
       │
       ▼
CentralGovernment.from_pickled_agent()
       │
       ├── states["Value-added Tax"] = tax_data.value_added_tax          (unchanged)
       ├── states["Income Tax"]       = tax_data.income_tax              (flat fallback)
       ├── states["Profit Tax"]       = tax_data.profit_tax              (unchanged)
       ├── states["Employer SI Tax"]  = tax_data.employer_social_...     (unchanged)
       ├── states["Employee SI Tax"]  = tax_data.employee_social_...     (unchanged)
       ├── states["Capital Formation Tax"] = tax_data.capital_form...    (unchanged)
       └── states["Export Tax"]       = tax_data.export_tax              (unchanged)

🆕 If pit_brackets configured:
       │
       ▼
PITSchedule.from_name_with_cpi("BC_PIT_2014.csv")
       │
       ├── Loads BC_PIT_2014.csv → brackets_df
       ├── Loads/caches bc_cpi_inflation.csv → cpi_rates
       │
       ▼
CentralGovernment.__init__()
       ├── 🆕 pit_base_thresholds = nominal thresholds (snapshot)
       ├── 🆕 pit_base_basic_deduction = nominal deduction (snapshot)
       ├── 🆕 states["pit_thresholds"] = CPI-inflated thresholds
       ├── 🆕 states["pit_rates"] = marginal rates
       └── 🆕 states["pit_basic_deduction"] = CPI-inflated deduction

Each year (posthook):
       │
       ▼
CentralGovernment.step_pit_brackets(tax_year, cpi_map, base_year)
       ├── 🆕 compound_inflation = ∏(1 + CPI_y)
       ├── 🆕 pit_thresholds = pit_base_thresholds × compound_inflation
       └── 🆕 pit_basic_deduction = pit_base_basic_deduction × compound_inflation
```

---

## Component ownership (PIT changes highlighted)

| Component | Changed? | Notes |
|-----------|----------|-------|
| `CentralGovernment` | 🔴 Yes | Progressive brackets, CPI indexation, basic deduction |
| `CentralGovernmentConfiguration` | 🔴 Yes | + `pit_brackets`, + `pit_basic_deduction` |
| `Country` | 🟡 Yes | Pre-calibration at t=0 |
| `pit_schedule.py` | 🆕 New | PITSchedule + compute_progressive_tax |
| `BC_PIT_2014.csv` | 🆕 New | Bracket definitions |
| `bc_cpi_inflation.csv` | 🆕 New | CPI cache (StatCan table 18-10-0005-01) |
| All other agents | 🟢 No | Unchanged |
| All markets | 🟢 No | Unchanged |
| `Economy` | 🟢 No | Unchanged |
| `Exogenous` | 🟢 No | Unchanged |
