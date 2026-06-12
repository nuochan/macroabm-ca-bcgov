# UML: CentralGovernment Agent — Progressive PIT Update

This page documents the `CentralGovernment` agent **after** the progressive Personal Income
Tax (PIT) update. Compare with the [upstream flat-tax design](../upstream_model/uml_central_government.md).

**Key changes from upstream**:
- ✅ Progressive multi-bracket tax schedule on employee wages
- ✅ CPI indexation of brackets via `step_pit_brackets()`
- ✅ Non-refundable basic personal amount (deduction × lowest marginal rate)
- ✅ Dual tax rate tracking: scalar `Income Tax` (effective rate) + `pit_thresholds`/`pit_rates`
- ✅ Pre-calibration at t=0 in `Country` to eliminate calibration shock
- ✅ New `pit_basic_deduction` and `pit_base_thresholds` snapshot fields

Reference: Bersini, H. (2012). [*UML for ABM*](https://www.jasss.org/15/1/9.html). JASSS 15(1)9.

---

## 1. Class diagram — changes highlighted

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
        +step_pit_brackets(cpi_map, base_year)
        +compute_taxes_on_products() float
        +compute_revenue(household_rent_paid) float
        +compute_deficit(activity, social_transfers, spending, rates)
        +compute_debt() ndarray
        +save_to_h5(group)
    }

    class ActivityStatus {
        <<enumeration>>
        EMPLOYED
        UNEMPLOYED
        NOT_ECONOMICALLY_ACTIVE
    }

    class PITSchedule {
        +brackets_df: DataFrame
        +cpi_rates: dict
        +base_year: int
        +from_name_with_cpi(name)$ PITSchedule
        +get_brackets(tax_year) tuple
        +get_basic_deduction(tax_year) float
    }

    class compute_progressive_tax {
        <<function>>
        +compute_progressive_tax(incomes, thresholds, rates) ndarray
        +compute_progressive_tax_quick(incomes, thresholds, quick_adds) ndarray
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
    CentralGovernment ..> PITSchedule : loads brackets + CPI
    CentralGovernment ..> compute_progressive_tax : applies in compute_taxes
    CentralGovernment "1" o-- "1" SocialBenefitsFunction : functions["social_benefits"]
    CentralGovernment "1" o-- "1" SocialHousingFunction : functions["social_housing"]
```

**`states` — progressive PIT additions highlighted 🆕:**

| State | Type | Purpose | Status |
|-------|------|---------|--------|
| `Value-added Tax` | float | VAT rate | unchanged |
| `Income Tax` | float | **Effective** flat rate (updated each period) | modified |
| `pit_thresholds` 🆕 | ndarray | Progressive bracket thresholds (CPI-indexed) | NEW |
| `pit_rates` 🆕 | ndarray | Marginal rates per bracket | NEW |
| `pit_basic_deduction` 🆕 | float | Non-refundable basic personal amount (CPI-indexed) | NEW |
| `Profit Tax` | float | Corporate tax rate | unchanged |
| `Employer Social Insurance Tax` | float | Employer SI | unchanged |
| `Employee Social Insurance Tax` | float | Employee SI | unchanged |
| `Capital Formation Tax` | float | Investment tax | unchanged |
| `Export Tax` | float | Export tax | unchanged |
| `Taxes Less Subsidies Rates` | ndarray | Net tax rates by sector | unchanged |
| `unemployment_benefits_model` | object | Benefit model | unchanged |
| `other_benefits_model` | object | Transfer model | unchanged |

---

## 2. Sequence diagram — `compute_taxes()` with progressive PIT

```mermaid
sequenceDiagram
    participant Country
    participant CG as CentralGovernment
    participant PIT as compute_progressive_tax

    Country->>CG: compute_taxes(employee_income, rent_paid,<br/>financial_income, activity, consumption, ...)

    rect rgb(240, 248, 255)
        Note over CG: Production & product taxes (unchanged)
        CG->>CG: taxes_production = sum(subsidies_rates * production * price)
        CG->>CG: taxes_vat = VAT_rate * sum(consumption)
        CG->>CG: taxes_cf = CF_tax_rate * sum(new_wealth)
        CG->>CG: taxes_exports = Export_Tax * total_exports
    end

    rect rgb(255, 235, 220)
        Note over CG,PIT: 🆕 Progressive PIT on employee wages
        CG->>CG: tot_wages = sum(employee_income[EMPLOYED])
        CG->>CG: wages_after_si = (1 - Employee_SI) * employee_income[EMPLOYED]
        CG->>PIT: compute_progressive_tax(wages_after_si, pit_thresholds, pit_rates)
        PIT-->>CG: tax_by_individual
        CG->>CG: Apply basic_deduction credit<br/>(credit = basic_deduction × lowest_marginal_rate)
        CG->>CG: pit_total = sum(tax_by_individual) - total_credits
    end

    rect rgb(255, 248, 240)
        Note over CG: Flat tax on rental & financial income (unchanged)
        CG->>CG: taxes_income = pit_total<br/>  + Income_Tax * rent_paid<br/>  + Income_Tax * sum(financial_income)
        CG->>CG: taxes_rental_income = Income_Tax * rent_paid
    end

    rect rgb(240, 255, 240)
        Note over CG: Corporate & SI taxes (unchanged)
        CG->>CG: taxes_corporate = Profit_Tax * sum(max(profits, 0))
        CG->>CG: taxes_employer_si = Employer_SI * tot_wages
        CG->>CG: taxes_employee_si = Employee_SI * tot_wages
    end

    rect rgb(255, 255, 220)
        Note over CG: 🆕 Update effective rate for behavioural code
        CG->>CG: effective_rate = total_tax / total_taxable_base
        CG->>CG: states["Income Tax"] = effective_rate
    end
```

---

## 3. Sequence diagram — annual CPI bracket indexation

```mermaid
sequenceDiagram
    participant Sim as Simulation
    participant PostHook as posthook(year==1)
    participant CG as CentralGovernment
    participant CPI as CPI data (bc_cpi_inflation.csv)

    Note over Sim: Fires each January (month=1)

    PostHook->>CG: step_pit_brackets(tax_year, cpi_map, base_year)

    rect rgb(220, 235, 255)
        Note over CG,CPI: 🆕 Compound CPI inflation
        CG->>CPI: Get CPI rates for each year since base_year
        CG->>CG: compound_inflation = ∏(1 + CPI_y) for y in [base_year+1 .. tax_year]
        CG->>CG: pit_thresholds = pit_base_thresholds * compound_inflation
        CG->>CG: pit_basic_deduction = pit_base_basic_deduction * compound_inflation
    end

    Note over CG: Preserves nominal base values<br/>in pit_base_thresholds for<br/>safe repeated calls
```

---

## 4. Activity diagram — tax computation with progressive PIT

```mermaid
flowchart TD
    A[Start compute_taxes] --> B[Compute production taxes<br/>unchanged]
    B --> C[Compute VAT<br/>unchanged]
    C --> D[Compute capital formation tax<br/>unchanged]
    D --> E[Compute corporate income tax<br/>unchanged]
    E --> F[Compute export taxes<br/>unchanged]
    F --> G[Sum employed wages]
    G --> H{"Progressive PIT<br/>configured?"}
    H -->|Yes| I["🆕 Apply progressive brackets:<br/>tax = compute_progressive_tax(<br/>  wages × (1-EmpSI),<br/>  pit_thresholds,<br/>  pit_rates)"]
    I --> J["🆕 Subtract non-refundable credit:<br/>credit = min(tax, basic_deduction × lowest_rate)"]
    J --> K["🆕 Sum progressive PIT total"]
    H -->|No| L[Apply flat Income_Tax rate]
    L --> K
    K --> M["Add flat tax on rent:<br/>Income_Tax × rent_paid"]
    M --> N["Add flat tax on financial income:<br/>Income_Tax × sum(financial_income)"]
    N --> O["🆕 Update effective rate:<br/>Income_Tax = total / total_taxable_base"]
    O --> P[Compute employer & employee SI]
    P --> Q[End]
```

---

## 5. Configuration class — with PIT fields 🆕

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
        +name: Literal["GrowthSocialBenefitsSetter"]
        +path_name: "social_benefits"
        +parameters: dict
    }

    class SocialHousing {
        +name: Literal["DefaultSocialHousing"]
        +path_name: "social_housing"
        +parameters: dict
    }

    CentralGovernmentConfiguration *-- CentralGovernmentFunctions : functions
    CentralGovernmentFunctions *-- SocialBenefits : social_benefits
    CentralGovernmentFunctions *-- SocialHousing : social_housing
```

| Field | Type | Default | Purpose |
|-------|------|---------|---------|
| `pit_brackets` 🆕 | `Optional[list[tuple[float, float]]]` | `None` | List of (upper_bound, marginal_rate) tuples. `None` = flat tax fallback |
| `pit_basic_deduction` 🆕 | `Optional[float]` | `None` | Non-refundable basic personal amount |

---

## 6. Pre-calibration at t=0 (in `Country`)

```mermaid
sequenceDiagram
    participant C as Country.__init__()
    participant CG as CentralGovernment
    participant PIT as compute_progressive_tax

    Note over C: After all agents constructed

    alt Progressive schedule configured
        C->>C: Generate synthetic initial employee<br/>income distribution
        C->>PIT: compute tax on initial distribution
        PIT-->>C: initial_progressive_tax
        C->>C: effective_rate = initial_tax / initial_income
        C->>CG: states["Income Tax"] = effective_rate
        Note over C: 🆕 Eliminates calibration shock<br/>Wage-setting & after-tax<br/>calculations aligned at t=0
    else Flat tax
        Note over C: No pre-calibration needed<br/>scalar already correct
    end
```
