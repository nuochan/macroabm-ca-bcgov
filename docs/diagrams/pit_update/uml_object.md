# UML: Object Diagram — Progressive PIT Update

This page shows a concrete snapshot of instances at tick $t = 12$ under the
**progressive PIT design**. Compare with the [upstream flat-tax object diagram](../upstream_model/uml_object.md).

The key difference: `CentralGovernment` now holds 🆕 `pit_thresholds`, `pit_rates`,
and `pit_basic_deduction`, and the scalar `Income Tax` reflects the *effective* rate.

---

```mermaid
flowchart TD
    subgraph Simulation["sim : Simulation (t = 12)"]
        country_ca["ca : Country\ncountry_name = 'CA'"]
    end

    subgraph Economy["economy : Economy"]
        ppi["ppi_inflation[12] = 1.02"]
        growth["total_growth[12] = 1.03"]
        good_prices["good_prices[12] ↓"]
    end

    subgraph FirmsLayer["firms : Firms"]
        firm0["firm[0]\nindustry = 'Mining'\nproduction = 104.2\nprice = 1.04\nn_employees = 47"]
        firm1["firm[1]\nindustry = 'Manufacturing'\nproduction = 312.7\nprice = 0.98\nn_employees = 182"]
    end

    subgraph HouseholdsLayer["households : Households"]
        hh0["hh[0]\ntenure = OWNER\nwealth = 52000\nconsumption = 3400"]
        hh1["hh[1]\ntenure = RENTER\nwealth = 8700\nconsumption = 2100"]
    end

    subgraph IndividualsLayer["individuals : Individuals"]
        ind0["ind[0]\nactivity = EMPLOYED\nemployee_income = 5200\nage = 34"]
        ind1["ind[1]\nactivity = EMPLOYED\nemployee_income = 8200\nage = 28"]
        ind2["ind[2]\nactivity = EMPLOYED\nemployee_income = 12800\nage = 45"]
        indU["ind[3]\nactivity = UNEMPLOYED\nincome_from_benefits = 1400"]
    end

    subgraph CentralBankLayer["central_bank : CentralBank"]
        cb["policy_rate[12] = 0.035"]
    end

    subgraph CentralGovLayer["central_government : CentralGovernment 🆕"]
        cg["Income Tax = 0.098  ← EFFECTIVE rate<br/>🆕 pit_thresholds = [37606, 75213, ...]<br/>🆕 pit_rates = [0.077, 0.105, ...]<br/>🆕 pit_basic_deduction = 9869<br/>🆕 pit_base_thresholds = [37606, ...] snapshot<br/>🆕 pit_base_basic_deduction = 9869 snapshot<br/>VAT = 0.05<br/>Employee SI = 0.046<br/>Profit Tax = 0.20"]
    end

    subgraph BanksLayer["banks : Banks"]
        bank0["bank[0]\noverdraft_rate = 0.045\nmortgage_rate = 0.055"]
    end

    Simulation --> country_ca
    country_ca --> Economy
    country_ca --> FirmsLayer
    country_ca --> HouseholdsLayer
    country_ca --> IndividualsLayer
    country_ca --> CentralBankLayer
    country_ca --> CentralGovLayer
    country_ca --> BanksLayer

    firm0 -.->|employs| ind0
    firm0 -.->|employs| ind1
    firm1 -.->|employs| ind2
    hh0 -.->|contains| ind0
    hh1 -.->|contains| ind1
    hh1 -.->|contains| indU
    bank0 -.->|lends to| firm0
    bank0 -.->|lends to| hh0
```

---

## Progressive tax calculation for employees at t=12

For each employed individual, the progressive PIT is computed:
1. `taxable_wage = employee_income × (1 - Employee SI)`
2. Apply `compute_progressive_tax(taxable_wage, pit_thresholds, pit_rates)`
3. Subtract non-refundable credit: `min(tax, pit_basic_deduction × lowest_marginal_rate)`

| Individual | Gross Wage | Taxable (after SI) | Bracket(s) hit | Marginal rate(s) | Tax before credit | Credit (9869×0.0506) | Final Tax | Effective rate |
|------------|------------|-------------------|----------------|------------------|-------------------|----------------------|-----------|----------------|
| ind[0] | 5,200 | 4,960.8 | 1st bracket only | 5.06% | 251.0 | 499.4 | 0 | 0.0% |
| ind[1] | 8,200 | 7,822.8 | straddles 1st–2nd | 5.06% / 7.7% | 470.2 | 499.4 | 0 | 0.0% |
| ind[2] | 12,800 | 12,211.2 | straddles 1st–2nd | 5.06% / 7.7% | 831.7 | 499.4 | 332.3 | 2.6% |

> **Note**: Low-income workers (ind[0], ind[1]) pay **zero** PIT after the non-refundable
> credit — the credit exceeds their computed bracket tax.

---

## PIT snapshot values — what changed from upstream

| Attribute | Upstream (flat) | PIT Update (progressive) |
|-----------|-----------------|--------------------------|
| `Income Tax` | 0.25 (statutory flat rate) | 0.098 (effective rate from progressive calc) |
| `pit_thresholds` | ❌ absent | 🆕 `[37606, 75213, 86354, 104858, 150000]` (CPI-inflated) |
| `pit_rates` | ❌ absent | 🆕 `[0.0506, 0.077, 0.105, 0.1229, 0.147, 0.168]` |
| `pit_basic_deduction` | ❌ absent | 🆕 9869 (CPI-inflated) |
| `pit_base_thresholds` | ❌ absent | 🆕 nominal snapshots for repeated CPI indexation |
| `pit_base_basic_deduction` | ❌ absent | 🆕 nominal snapshot |
| All other states | Same | Same |

---

## How to read this

| Notation | UML meaning | Example |
|---|---|---|
| Box with `name : Class` | An object instance | `ca : Country` |
| `attr = value` inside box | Current attribute values (snapshot) | `policy_rate[12] = 0.035` |
| Solid arrow | Composition link (strong ownership) | `Country → Economy` |
| Dashed arrow `-.->` | Runtime association / usage | `firm[0] -.-> ind[0]` |
