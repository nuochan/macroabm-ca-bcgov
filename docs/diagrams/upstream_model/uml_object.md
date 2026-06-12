# UML: Object Diagram — Original Upstream Design

While class diagrams show the abstract structure, an **object diagram** shows
a concrete snapshot of instances at one moment in time — the "debugging
diagram."

This snapshot corresponds to tick $t = 12$ (one year into a quarterly
simulation) for `Country("CA")` under the **original flat-tax design**.

Reference: Collins et al. (2015). A Call to Arms: Standards for ABM. *JASSS* 18(3)12.

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
        ind1["ind[1]\nactivity = UNEMPLOYED\nemployee_income = 0\nincome_from_benefits = 1400\nage = 28"]
    end

    subgraph CentralBankLayer["central_bank : CentralBank"]
        cb["policy_rate[12] = 0.035"]
    end

    subgraph CentralGovLayer["central_government : CentralGovernment"]
        cg["Income Tax = 0.25  ← FLAT rate\nVAT = 0.05\nEmployee SI = 0.046\nEmployer SI = 0.062\nProfit Tax = 0.20\nbenefits_per_unemployed = 1400"]
    end

    subgraph BanksLayer["banks : Banks"]
        bank0["bank[0]\noverdraft_rate = 0.045\nmortgage_rate = 0.055\nis_insolvent = False"]
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
    hh0 -.->|contains| ind0
    hh1 -.->|contains| ind1
    bank0 -.->|lends to| firm0
    bank0 -.->|lends to| hh0
```

## Key flat-tax snapshot values at t=12

| Component | Attribute | Value | Notes |
|-----------|-----------|-------|-------|
| CentralGovernment | `Income Tax` | 0.25 | Single scalar — all income taxed at 25% |
| CentralGovernment | `VAT` | 0.05 | Flat VAT |
| CentralGovernment | `Employee SI` | 0.046 | Deducted before flat tax applied |
| CentralGovernment | `Employer SI` | 0.062 | Paid by firms |
| CentralGovernment | `Profit Tax` | 0.20 | Corporate rate |
| Individuals[0] | `employee_income` | 5200 | Gross wage; after-tax = 5200 × (1-0.046) × (1-0.25) = 3720.15 |
| Individuals[1] | `income_from_benefits` | 1400 | Unemployment benefit (not taxed) |

**Tax calculation for ind[0] (EMPLOYED):**
```
taxable_wage = 5200 × (1 - 0.046) = 4960.8
tax = 4960.8 × 0.25 = 1240.2
after_tax = 4960.8 - 1240.2 = 3720.6
```

---

## How to read this

| Notation | UML meaning | Example |
|---|---|---|
| Box with `name : Class` | An object instance | `ca : Country` |
| `attr = value` inside box | Current attribute values (snapshot) | `policy_rate[12] = 0.035` |
| Solid arrow | Composition link (strong ownership) | `Country → Economy` |
| Dashed arrow `-.->` | Runtime association / usage | `firm[0] -.-> ind[0]` |
