# UML Demo: System-Wide (Cross-Agent) Diagrams

This page extends the [UML for ABM](https://www.jasss.org/15/1/9.html) demo
from individual agents to the **full model architecture**. Bersini's paper
shows three kinds of cross-agent diagrams that sit one level above per-agent
ones:

| Bersini figure | Diagram | What it shows |
|---|---|---|
| Fig 1, 2, 11, 12 | Cross-agent **class diagram** | How agents, markets, world/simulation relate structurally |
| Fig 3, 4, 9, 11 | Cross-agent **sequence diagram** | Who calls whom across agent boundaries during a tick |
| Fig 7 | Cross-agent **activity diagram** | Procedural flow with swimlanes per actor |

All three are provided below for this repository, using the same Mermaid
notation as the per-agent pages.

---

## 1. Cross-agent class diagram (structural skeleton)

This shows every agent class, every market, and the `Country` / `Simulation`
orchestrators — all in one diagram. Compare Bersini's Figures 1 and 12.

```mermaid
classDiagram
    direction TB

    class Simulation {
        +countries: dict[str, Country]
        +goods_market: GoodsMarket
        +exchange_rates: ExchangeRates
        +rest_of_the_world: RestOfTheWorld
        +timestep: Timestep
        +iterate(t)
        +run()
    }

    class Country {
        +country_name: str
        +economy: Economy
        +firms: Firms
        +households: Households
        +individuals: Individuals
        +banks: Banks
        +central_bank: CentralBank
        +central_government: CentralGovernment
        +government_entities: GovernmentEntities
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
        +states
        +ts
        +update_property_value()
        +clear(...)
        +process_housing_market_clearing(...)
    }

    class CreditMarket {
        +clear(banks, firms, households, ...)
    }

    class Agent {
        <<abstract>>
        +country_name: str
        +states: dict
        +ts: TimeSeries
    }

    class Firms {
        +update_number_of_firms()
        +set_estimates()
        +set_targets()
        +compute_estimated_profits()
        +compute_target_credit()
    }

    class Households {
        +prepare_housing_market_clearing()
        +update_rent()
        +compute_target_credit()
    }

    class Individuals {
        +compute_labour_inputs()
        +compute_reservation_wages()
        +compute_income()
        +update_demography()
    }

    class Banks {
        +compute_estimated_profits()
        +set_interest_rates()
    }

    class CentralBank {
        +compute_rate()
    }

    class CentralGovernment {
        +update_benefits()
        +distribute_unemployment_benefits_to_individuals()
    }

    class GovernmentEntities

    class ExchangeRates
    class RestOfTheWorld
    class Timestep

    Simulation "1" *-- "1..*" Country : composes
    Simulation "1" *-- "1" GoodsMarket
    Simulation "1" *-- "1" ExchangeRates
    Simulation "1" *-- "1" RestOfTheWorld
    Simulation "1" *-- "1" Timestep

    Country "1" *-- "1" Economy
    Country "1" *-- "1" LabourMarket
    Country "1" *-- "1" HousingMarket
    Country "1" *-- "1" CreditMarket

    Agent <|-- Individuals
    Agent <|-- Households
    Agent <|-- Firms
    Agent <|-- Banks
    Agent <|-- CentralBank
    Agent <|-- CentralGovernment
    Agent <|-- GovernmentEntities

    Country "1" *-- "1" Individuals
    Country "1" *-- "1" Households
    Country "1" *-- "1" Firms
    Country "1" *-- "1" Banks
    Country "1" *-- "1" CentralBank
    Country "1" *-- "1" CentralGovernment
    Country "1" *-- "1" GovernmentEntities
```

**Key observations:**

- The **black diamonds** (composition) between `Country` and its agents mean
  agents live and die with their parent country — exactly as the paper's
  Figure 1 composes `Site`, `Agent`, and `Resource` into `World`.
- `Agent` is **abstract**: no plain `Agent` is ever instantiated. The concrete
  leaf classes (`Firms`, `Households`, `Individuals`, `Banks`, …) provide the
  real behaviour.
- The architecture cleanly separates *agents* (who make decisions) from
  *markets* (who match supply and demand) — a pattern the paper endorses at
  §2.8.

---

## 2. Cross-agent sequence diagram (one full tick)

This traces the **entire `Simulation.iterate()` call flow** through Country,
every agent type, and every market. It follows the paper's Figures 9 and 11
(which trace Schelling and evolutionary-game ticks).

For readability, only one country is shown. Multi-country `for` loops over
`self.countries.values()` are labelled with `loop [per country]`.

```mermaid
sequenceDiagram
    autonumber

    participant Sim as Simulation
    participant ER as ExchangeRates
    participant C as Country(:CA)
    participant Econ as Economy
    participant Firms
    participant Banks
    participant CB as CentralBank
    participant CG as CentralGovernment
    participant Ind as Individuals
    participant HH as Households
    participant LM as LabourMarket
    participant HM as HousingMarket
    participant CM as CreditMarket
    participant GM as GoodsMarket(global)
    participant ROW as RestOfTheWorld

    Sim->>Sim: run_prehooks(year, month)

    Note over Sim,C: ── Estimation & target-setting phase (per country) ──

    loop per country
        Sim->>ER: get_current_exchange_rates(country)
        ER-->>C: rate_usd_to_lcu
        Sim->>C: initialisation_phase(rate)
        C->>Firms: update_number_of_firms()
        Sim->>C: estimation_phase()
        C->>Econ: set_estimates(exo_growth, exo_infl, …)
        C->>Firms: set_estimates(prices, growth)
        Sim->>C: target_setting_phase()
        C->>Firms: set_targets(deposit_rate, growth, infl, prices)
        C->>Ind: compute_reservation_wages(benefits)
    end

    Note over Sim,C: ── Labour-market clearing (per country) ──

    loop per country
        Sim->>C: clear_labour_market()
        C->>LM: clear(firms, households, individuals)
        LM-->>C: labour_costs
        Sim->>C: update_planning_metrics()
        C->>Firms: compute_estimated_profits()
        C->>Banks: compute_estimated_profits()
        C->>CG: update_benefits(infl, growth, unemployment)
        C->>Ind: compute_labour_inputs()
        C->>CB: compute_rate(infl, growth)
    end

    Note over Sim,C: ── Housing & credit markets (per country) ──

    loop per country
        Sim->>C: prepare_housing_market_clearing()
        C->>HM: update_property_value()
        C->>HH: prepare_housing_market_clearing(data, prices, …)
        Sim->>C: clear_housing_market()
        C->>HM: clear(tenure_status, max_price, max_rent)
        Sim->>C: prepare_credit_market_clearing()
        C->>Firms: compute_target_credit(growth, infl)
        C->>HH: compute_target_credit(rental_sales)
        C->>Banks: set_interest_rates(policy_rate)
        Sim->>C: clear_credit_market()
        C->>CM: clear(banks, firms, households, …)
        Sim->>C: process_housing_market_clearing()
        C->>HM: process_housing_market_clearing(…)
        Sim->>C: process_credit_market_clearing()
    end

    Note over Sim,C: ── Prepare goods market (per country) ──

    loop per country
        Sim->>C: prepare_goods_market_clearing()
    end

    Note over Sim,ROW: ── Global goods-market clearing ──

    Sim->>ROW: update_planning_metrics(price_index)
    Sim->>GM: prepare()
    Sim->>GM: clear()
    Sim->>GM: record()

    Note over Sim,C: ── Post-clearing & population (per country) ──

    Sim->>ROW: record_bought_goods()
    loop per country
        Sim->>C: update_realised_metrics()
        Sim->>C: update_population_structure()
    end

    Sim->>Sim: run_posthooks(t, year, month)
    Sim->>Sim: timestep.step()
```

**Reading notes (Bersini §2.12–2.16):**

- This diagram intentionally stays at the *responsibility* level: it shows which
  agent is asked to do what and in what order, without nested `loop`/`alt`
  frames or parameter passing details.
- The global goods market (bottom section) is Belini's "collaborating elements"
  pattern — the `GoodsMarket` doesn't belong to a single country; it reconciles
  supply and demand across all countries plus the rest-of-world.

---

## 3. Cross-agent activity diagram (swimlane view)

Where the sequence diagram is chronological, the activity diagram groups
actions by **who performs them**. This follows Bersini's Figure 7 pattern and
the final paragraphs of §2.20–2.22, which encourage swimlane partitioning
when behaviour spans multiple actors.

```mermaid
flowchart TB
    %% ============ PRE-HOOKS ============
    subgraph PRE[Pre-hooks]
        direction LR
        Pre1[execute pre-hooks]
    end

    subgraph SIM[Simulation]
        S1[iterate#40;t#41;]
        S2[timestep.step#40;#41;]
    end

    subgraph ER[ExchangeRates]
        E1[get rate per country]
    end

    %% ============ PHASE 1: Estimation ============
    subgraph COUNTRY1[Country — estimation phase]
        direction TB
        C1a[initialisation_phase]
        C1b[estimation_phase]
        C1c[target_setting_phase]
    end

    subgraph AGENTS1[Agents — estimation]
        direction LR
        A1a[Firms: update_number / set_estimates / set_targets]
        A1b[Economy: set_estimates]
        A1c[Individuals: reservation wages]
    end

    %% ============ PHASE 2: Labour market ============
    subgraph LAB[Labour market]
        direction TB
        L1[LabourMarket.clear]
        L2[update_planning_metrics]
    end

    subgraph AGENTS2[Agents — planning]
        direction LR
        A2a[Firms / Banks: expected profits]
        A2b[CentralGovernment: benefits]
        A2c[Individuals: labour_inputs]
        A2d[CentralBank: policy rate]
    end

    %% ============ PHASE 3: Housing & credit ============
    subgraph HCR[Housing & Credit markets]
        direction TB
        H1[prepare → clear → process: HOUSING]
        H2[prepare → clear → process: CREDIT]
    end

    %% ============ PHASE 4: Goods market ============
    subgraph GOODS[Global goods market]
        direction TB
        G1[Countries: prepare_goods_market_clearing]
        G2[ROW: update_planning_metrics]
        G3[GoodsMarket: prepare → clear → record]
    end

    %% ============ PHASE 5: Post ============
    subgraph POST[Post-clearing]
        direction LR
        P1[ROW: record_bought_goods]
        P2[Countries: update_realised_metrics]
        P3[Countries: update_population_structure]
    end

    %% ============ FLOW ============
    PRE     --> COUNTRY1
    COUNTRY1 --- AGENTS1
    AGENTS1 --> LAB
    LAB    --- AGENTS2
    AGENTS2 --> HCR
    HCR    --> GOODS
    GOODS  --> POST
    POST   --> SIM

    %% Make sequential order explicit
    PRE ~~~ COUNTRY1 ~~~ LAB ~~~ HCR ~~~ GOODS ~~~ POST ~~~ SIM
```

In essence, the activity diagram tells the same story as the sequence diagram,
but from the perspective of *what block of work* happens next, rather than
*who calls whom*.

**Swimlanes (logical, not drawn as Mermaid swimlanes):**

| Column | Actor |
|---|---|
| 1 | Pre-hooks (user-defined injection points) |
| 2 | `ExchangeRates` |
| 3 | `Country.initialisation → estimation → target_setting` |
| 4 | Firm / Economy / Individual expectations |
| 5 | `LabourMarket` clearing |
| 6 | Central-government / Central-bank / profit updates |
| 7 | `HousingMarket` + `CreditMarket` (prepare → clear → process) |
| 8 | Global `GoodsMarket` (prepare → clear → record) |
| 9 | `ROW` + per-country post-clearing |
| 10 | `Simulation.run_posthooks()`, then `timestep.step()` |

---

## Why these three together?

Bersini's core claim is that **different diagrams are useful at different
moments** (§1.7, §4.1–4.2):

- The **class diagram** is for architecture discussion and onboarding — you
  draw it once and it stays valid across many ticks.
- The **sequence diagram** is for debugging one specific scenario — you trace
  a tick, or part of a tick, to see if responsibilities are in the right
  place.
- The **activity diagram** is for procedural flow — when you need to explain
  “what happens in a step” to a non-implementer.

Having all three for the same codebase means you can pick whichever one answers
today's question.

## Reference

Bersini, H. (2012). *UML for ABM*. Journal of Artificial Societies and Social
Simulation 15 (1) 9. <https://www.jasss.org/15/1/9.html>
