# UML Demo: Object Diagram

An **object diagram** is a snapshot of instances at a single point in time.
While a class diagram says "a Firm *has* a price," an object diagram says
"Firm #3's price = 1.04 at `t=12`." This follows Collins et al. (2015) who
recommend object diagrams for ABM verification: *"does the state at tick n
actually match what the sequence diagram predicted?"*

Bersini does not cover object diagrams, but they are the fourth diagram in the
"structural" family alongside class, package, and component diagrams. They are
invaluable for debugging and onboarding — a new contributor can see what a
"healthy" simulation state looks like.

## Snapshot: mid-simulation tick (t=12, Country=CA)

This shows 2 Firms, 1 Household, 2 Individuals, and their concrete state
values. Arrows represent runtime links (instance-level associations, not UML
associations).

```mermaid
graph TB
    subgraph Country["Country: CA"]
        subgraph Firms["Firms sector"]
            F3["Firm #3 (Industry: Manufacturing)<br/>production=142.7  price=1.04<br/>employees=18  capital_stock=2_340"]
            F7["Firm #7 (Industry: Services)<br/>production=89.2  price=0.98<br/>employees=12  capital_stock=1_100"]
        end

        subgraph Households["Households"]
            HH2["Household #2<br/>tenure=OWNER  wealth=45_200<br/>consumption_budget=3.8k"]
        end

        subgraph Individuals["Individuals"]
            I4["Individual #4<br/>age=38  gender=MALE  edu=Bachelor<br/>activity=EMPLOYED  income=62.4k<br/>corr_household=2  corr_firm=3"]
            I9["Individual #9<br/>age=27  gender=FEMALE  edu=Master<br/>activity=EMPLOYED  income=58.1k<br/>corr_household=2  corr_firm=7"]
        end

        subgraph Markets["Market objects"]
            LM["LabourMarket<br/>cleared=true  avg_wage=1.02"]
            CM["CreditMarket<br/>cleared=true  avg_loan_rate=0.037"]
            HM["HousingMarket<br/>properties=1_240  price_index=1.08"]
        end
    end

    F3 -.-> |"corresponding_firm"| I4
    F7 -.-> |"corresponding_firm"| I9
    I4 -.-> |"corr_household"| HH2
    I9 -.-> |"corr_household"| HH2
    HH2 --> |"holds mortgage"| CM
    F3 --> |"borrows"| CM
    F7 --> |"borrows"| CM
    I4 --> |"labour supply"| LM
    I9 --> |"labour supply"| LM
    HH2 --> |"owns property"| HM

    style F3 fill:#e1f5fe
    style F7 fill:#e1f5fe
    style HH2 fill:#fff3e0
    style I4 fill:#e8f5e9
    style I9 fill:#e8f5e9
    style LM fill:#fce4ec
    style CM fill:#fce4ec
    style HM fill:#fce4ec
```

**Key observations:**

- `Individual #4` works at `Firm #3` in Manufacturing. `Individual #9` works at
  `Firm #7` in Services. Both belong to `Household #2`.
- This is the pattern the class diagram prescribes: each `Individual` has
  one `corresponding_firm` and one `corresponding_household`. The object
  diagram proves those links exist at runtime.
- The household participates in both the credit market (mortgage) and the
  housing market (property ownership), while firms only participate in the
  credit market.

---

## Second snapshot: pre/post labour-market clearing

Sometimes the most useful object diagram is **before-and-after** — the same
two objects at two moments.

```mermaid
graph LR
    subgraph Before["Before clearing (t=12)"]
        I5["Individual #5<br/>activity=UNEMPLOYED<br/>reservation_wage=0.92"]
        F2["Firm #2<br/>vacancies=3<br/>offered_wage=0.98"]
    end

    subgraph After["After clearing (t=12)"]
        I5b["Individual #5<br/>activity=EMPLOYED<br/>started_new_job=True<br/>offered_wage_of_accepted_job=0.98"]
        F2b["Firm #2<br/>vacancies=2<br/>employees+=1"]
    end

    Before --> After
```

This is the exact scenario traced by the Individuals state diagram
(`UNEMPLOYED → EMPLOYED`) and by the labour-market sequence in the system-wide
sequence diagram. It answers: *did the matching logic actually place this
unemployed individual into this firm?*

---

## Why object diagrams matter for ABM

Collins et al. (2015) note that ABMs are uniquely suited to object diagrams
because:

1. Every agent is a discrete instance with a unique ID — the diagram mirrors
   the runtime reality 1:1.
2. Before/after snapshots are the fastest way to verify a market-clearing
   or state-transition logic.
3. They bridge the gap between the class diagram (what *can* exist) and the
   debugger (what *does* exist at a given tick).

For this repo, an object diagram is especially useful when debugging the
labour market (`LabourMarket.clear`) or tracing an individual's income
computation (`compute_income`).

## References

- Collins, A. et al. (2015). *UML for agent-based modelling and simulation.*
- UML 2.5 Specification, §9 — Object diagrams.
