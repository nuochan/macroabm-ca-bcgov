# UML Demo: Package Diagram

A **package diagram** showing the module-level dependency structure of the
repository. This follows the recommendation of Collins et al. (2015) and
Niazi & Hussain (2012) that ABM codebases benefit from a "table of contents"
diagram before diving into per-class detail.

Compare Bersini §1.4: *"UML provides a level of abstraction higher than that
provided by OO programming languages."* The package diagram sits one level
above the class diagram — it shows what depends on what *at the import level*.

## Top-level packages

```mermaid
graph LR
    md[macro_data]
    mm[macromodel]
    mc[macrocalib]
    tests[tests]

    md --> mm
    mm --> mc
    mm --> tests
    mc --> tests
```

`macro_data` has zero dependencies on the other two — it is pure data
preparation. `macromodel` depends on `macro_data` (it consumes the processed
data). `macrocalib` depends on both (it runs `macromodel` simulations and
trains on `macro_data`).

---

## Full package structure

```mermaid
graph TB
    subgraph macro_data["macro_data (data preparation)"]
        direction TB
        md_conf[configuration]
        md_read[readers]
        md_proc[processing]
        md_util[util]
        md_dw[data_wrapper.py]

        md_conf --> md_dw
        md_read --> md_dw
        md_proc --> md_dw
        md_read --> md_proc
    end

    subgraph macromodel["macromodel (simulation engine)"]
        direction TB
        mm_agents[agents]
        mm_markets[markets]
        mm_country[country]
        mm_econ[economy]
        mm_sim[simulation.py]
        mm_conf[configurations]
        mm_er[exchange_rates]
        mm_ts[timeseries.py]
        mm_row[rest_of_the_world]

        mm_agents --> mm_country
        mm_markets --> mm_country
        mm_econ --> mm_country
        mm_er --> mm_sim
        mm_row --> mm_sim
        mm_country --> mm_sim
        mm_conf --> mm_agents
        mm_conf --> mm_markets
        mm_ts --> mm_agents
        mm_ts --> mm_markets
    end

    subgraph macrocalib["macrocalib (calibration)"]
        direction TB
        mc_samp[sampler]
        mc_train[training]

        mc_samp --> mc_train
    end

    macro_data --> macromodel
    macromodel --> macrocalib

    subgraph tests["tests"]
        direction LR
        t_md[test_macro_data]
        t_mm[test_macromodel]
        t_mc[test_macrocalib]
    end

    macromodel --> tests
    macrocalib --> tests
```

---

## Agent sub-packages (inside `macromodel.agents`)

```mermaid
graph LR
    agent[agent]
    firms[firms]
    households[households]
    individuals[individuals]
    banks[banks]
    central_bank[central_bank]
    central_government[central_government]
    government_entities[government_entities]

    agent --> firms
    agent --> households
    agent --> individuals
    agent --> banks
    agent --> central_bank
    agent --> central_government
    agent --> government_entities
```

All agent types inherit from `macromodel.agents.agent.Agent`. There are no
other cross-dependencies: agents interact only through markets and through
the `Country` orchestrator, not by importing each other.

---

## Market sub-packages (inside `macromodel.markets`)

```mermaid
graph LR
    gm[goods_market]
    cm[credit_market]
    hm[housing_market]
    lm[labour_market]

    gm ~~~ cm ~~~ hm ~~~ lm
```

Markets are independent of each other — they are composed into `Country` and
called in sequence. The global `GoodsMarket` is the only market that lives at
the `Simulation` level (not per-country).

---

## Why a package diagram?

Bersini omitted it (§4.5: *"use case, component and deployment diagrams …
should be of minor importance for most ABM modelling endeavours"*), but
subsequent ABM-UML work (Niazi & Hussain 2012; Collins et al. 2015) argues
that package diagrams are the **first diagram a new contributor needs** because:

1. They answer "where is the code I need to touch?"
2. They make circular-dependency violations visually obvious.
3. They cost almost nothing to maintain — the package structure changes far
   less often than class details.

For a codebase of this size (25+ sub-packages), the package diagram is the
single highest-value-per-pixel diagram you can draw.

## References

- Collins, A. et al. (2015). *UML for agent-based modelling and simulation.*
- Niazi, M. & Hussain, A. (2012). *Agent-based tools for modeling and
  simulation.*
