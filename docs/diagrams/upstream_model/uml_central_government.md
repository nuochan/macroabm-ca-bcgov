# UML: CentralGovernment Agent — Original Upstream Design

This page applies Bersini's four-diagram UML subset to the `CentralGovernment` agent
as designed in the original upstream [`uvic-sesit/macroabm-ca`](https://github.com/uvic-sesit/macroabm-ca).

**Key design characteristic**: Flat income tax only — a single scalar `Income Tax` rate
applied uniformly to wages, rental income, and financial asset income. No progressive brackets,
no CPI indexation, no basic deduction.

Reference: Bersini, H. (2012). [*UML for ABM*](https://www.jasss.org/15/1/9.html). JASSS 15(1)9.

---

## 1. Class diagram

`CentralGovernment` inherits from `Agent` and aggregates two strategy classes:
`social_benefits` and `social_housing`. It depends on `ActivityStatus`.
All taxes use flat scalar rates stored in `states`.

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
        +from_pickled_agent(...)$
        +reset(config)
        +update_benefits(historic_ppi, exogenous_ppi, ...)
        +distribute_unemployment_benefits_to_individuals(status)
        +compute_taxes(income, rent, financial_income, ...)
        +compute_taxes_on_products() float
        +compute_revenue(household_rent_paid) float
        +compute_deficit(activity, social_transfers, spending, rates)
        +compute_debt() ndarray
        +total_taxes() float
        +save_to_h5(group)
    }

    class ActivityStatus {
        <<enumeration>>
        EMPLOYED
        UNEMPLOYED
        NOT_ECONOMICALLY_ACTIVE
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
    CentralGovernment "1" o-- "1" SocialBenefitsFunction : functions["social_benefits"]
    CentralGovernment "1" o-- "1" SocialHousingFunction : functions["social_housing"]
```

**`states` tax instruments (all flat scalars):**

| State | Type | Purpose |
|-------|------|---------|
| `Value-added Tax` | float | VAT rate |
| `Income Tax` | float | Flat PIT rate (applied to wages, rent, financial income) |
| `Profit Tax` | float | Corporate tax rate |
| `Employer Social Insurance Tax` | float | Employer SI contribution rate |
| `Employee Social Insurance Tax` | float | Employee SI deduction rate |
| `Capital Formation Tax` | float | Investment tax |
| `Export Tax` | float | Tax on exports |
| `Taxes Less Subsidies Rates` | ndarray | Net tax rates by sector |
| `unemployment_benefits_model` | object | Benefit computation model |
| `other_benefits_model` | object | Social transfer model |

---

## 2. Sequence diagram — `compute_taxes()` flow

Shows the tax calculation sequence within a single timestep. All income types
are taxed at the **same flat rate** (`Income Tax`).

```mermaid
sequenceDiagram
    participant Country
    participant CentralGovernment

    Country->>CentralGovernment: compute_taxes(employee_income, rent_paid,<br/>financial_income, activity, consumption,<br/>bank_profits, firm_production, firm_price,<br/>firm_profits, firm_industries, new_wealth,<br/>taxes_less_subsidies_rates, total_exports)

    rect rgb(240, 248, 255)
        Note over CentralGovernment: Production & product taxes
        CentralGovernment->>CentralGovernment: taxes_production = sum(subsidies_rates * production * price)
        CentralGovernment->>CentralGovernment: taxes_vat = VAT_rate * sum(consumption)
        CentralGovernment->>CentralGovernment: taxes_cf = CF_tax_rate * sum(max(0, new_wealth))
        CentralGovernment->>CentralGovernment: taxes_exports = Export_Tax * total_exports
    end

    rect rgb(255, 248, 240)
        Note over CentralGovernment: Flat income tax on ALL sources
        CentralGovernment->>CentralGovernment: tot_wages = sum(employee_income[EMPLOYED])
        CentralGovernment->>CentralGovernment: taxes_income = Income_Tax * (1-EmpSI) * tot_wages<br/>  + Income_Tax * rent_paid<br/>  + Income_Tax * sum(financial_income)
        CentralGovernment->>CentralGovernment: taxes_rental_income = Income_Tax * rent_paid
    end

    rect rgb(240, 255, 240)
        Note over CentralGovernment: Corporate & SI taxes
        CentralGovernment->>CentralGovernment: taxes_corporate = Profit_Tax * sum(max(profits, 0))
        CentralGovernment->>CentralGovernment: taxes_employer_si = Employer_SI * tot_wages
        CentralGovernment->>CentralGovernment: taxes_employee_si = Employee_SI * tot_wages
    end
```

**Key observation**: The single `Income Tax` scalar is applied identically to:
- Employee wages (post-SI deduction)
- Rental income
- Financial asset income

---

## 3. Activity diagram — tax computation procedure

```mermaid
flowchart TD
    A[Start compute_taxes] --> B[Compute production taxes:<br/>taxes_less_subsidies * production * price]
    B --> C[Compute VAT:<br/>VAT_rate * total_consumption]
    C --> D[Compute capital formation tax:<br/>CF_rate * new_real_wealth]
    D --> E[Compute corporate income tax:<br/>Profit_Tax * firm & bank profits]
    E --> F[Compute export taxes:<br/>Export_Tax * total_exports]
    F --> G[Sum employed wages]
    G --> H["Compute INCOME TAX (flat):<br/>Income_Tax * (1-EmpSI) * wages<br/>+ Income_Tax * rent<br/>+ Income_Tax * financial_income"]
    H --> I[Compute employer SI:<br/>Employer_SI * wages]
    I --> J[Compute employee SI:<br/>Employee_SI * wages]
    J --> K[End]
```

---

## 4. Configuration class — upstream minimal design

```mermaid
classDiagram
    class CentralGovernmentConfiguration {
        +functions: CentralGovernmentFunctions
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

> **Note**: The original upstream config has **no** `pit_brackets`, no `pit_basic_deduction`,
> and no CPI indexation fields. All income tax is flat.
