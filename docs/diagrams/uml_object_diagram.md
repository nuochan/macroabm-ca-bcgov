# UML Demo: Object Diagram

While class diagrams show the abstract structure, an **object diagram** shows
a concrete snapshot of instances at one moment in time — the "debugging
diagram." Collins et al. (2015) specifically advocate object diagrams for ABM
verification: "does the state at tick *n* match what the sequence diagram
predicted?"

This snapshot corresponds to tick $t = 12$ (one year into a quarterly
simulation) for `Country("CA")`.

```mermaid
graph TD
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
        firmN["firm[N] ..."]
    end

    subgraph HouseholdsLayer["households : Households"]
        hh0["hh[0]\ntenure = OWNER\nwealth = 52000\nconsumption = 3400"]
        hh1["hh[1]\ntenure = RENTER\nwealth = 8700\nconsumption = 2100"]
    end

    subgraph IndividualsLayer["individuals : Individuals"]
        ind0["ind[0]\nactivity = EMPLOYED\nincome = 5200\nage = 34\ngender = MALE"]
        ind1["ind[1]\nactivity = UNEMPLOYED\nincome = 1800\nage = 28\ngender = FEMALE"]
    end

    subgraph CentralBankLayer["central_bank : CentralBank"]
        cb["policy_rate[12] = 0.035"]
    end

    subgraph CentralGovLayer["central_government : CentralGovernment"]
        cg["Income Tax = 0.25\nVAT = 0.05\nbenefits_per_unemployed = 1400"]
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
    hh0  -.->|contains| ind0
    hh1  -.->|contains| ind1
    bank0 -.->|lends to| firm0
    bank0 -.->|lends to| hh0
```

## How to read this

| Notation | UML meaning | Example |
|---|---|---|
| Box with name:Class | An object instance | `ca : Country` |
| `attr = value` inside box | Current attribute values (snapshot) | `policy_rate[12] = 0.035` |
| Solid arrow | Composition link (strong ownership) | `Country → Economy` |
| Dashed arrow `-.->` | Runtime association / usage | `firm[0] -..-> ind[0]` |

**Why this matters:** Note that at $t = 12$:

- `firm[0]`'s price (1.04) is above `firm[1]`'s (0.98), consistent with good_prices.
- `ind[1]` is `UNEMPLOYED` and receiving ~1,400 in benefits — exactly what
  `CentralGovernment.benefits_per_unemployed` says.
- `bank[0]` is solvent and lending to both a firm and a household (no NPL
  crisis at this tick).

A developer who just ran `Simulation.iterate()` can compare this snapshot to
the simulator's memory dump and verify correctness.

## References

- Collins, A., Petty, M., Vernon-Bido, D., & Sherfey, S. (2015). A Call to Arms:
  Standards for Agent-Based Modeling and Simulation. *JASSS* 18(3)12.
- Bersini, H. (2012). UML for ABM. *JASSS* 15(1)9. (Does not cover object
  diagrams, but §§3.2–3.4 on Schelling describe exactly this kind of snapshot
  for verification.)
