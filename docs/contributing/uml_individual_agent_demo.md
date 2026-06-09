# UML Demo: Agent Diagrams

This page applies UML to the agents in this repository, following the
four-diagram subset advocated by Bersini (2012),
[*UML for ABM*, JASSS 15(1)9](https://www.jasss.org/15/1/9.html):

1. **Class diagram** — static structure (what the agent *is*, what it is *related to*).
2. **Sequence diagram** — interactions over time (who calls whom, in what order).
3. **State diagram** — the agent's life-cycle.
4. **Activity diagram** — the procedural flow of one tick.

We start with a small, fully-worked example on the [`Individuals`](../../macromodel/agents/individuals/individuals.py)
agent, then cover each of the other agent types more compactly. As Bersini
notes, *"draw as much of the diagram as is needed to help your programming,
but no more"*.

All diagrams below are written in [Mermaid](https://mermaid.js.org/), so they
render in GitHub, in MkDocs Material, and in most modern Markdown previewers.

## 0. Agent hierarchy overview

A single class diagram of how every agent in
[`macromodel/agents/`](../../macromodel/agents/) relates to the abstract base
`Agent`. This is the entry-point map for the rest of the page.

```mermaid
classDiagram
    class Agent {
        <<abstract>>
        +country_name: str
        +states: dict
        +ts: TimeSeries
        +prepare()
    }

    class Individuals {
        +functions
        +compute_income(...)
        +compute_labour_inputs()
    }
    class Households {
        +functions
        +consumption_weights
        +compute_consumption(...)
        +compute_investment(...)
    }
    class Firms {
        +functions
        +intermediate_inputs_productivity_matrix
        +produce(...)
        +set_prices(...)
        +hire(...)
    }
    class Banks {
        +functions
        +parameters
        +set_interest_rates(...)
        +compute_profits(...)
    }
    class CentralBank {
        +functions
        +set_policy_rate(...)
    }
    class CentralGovernment {
        +functions
        +collect_taxes(...)
        +pay_benefits(...)
    }
    class GovernmentEntities {
        +functions
        +plan_consumption(...)
    }

    Agent <|-- Individuals
    Agent <|-- Households
    Agent <|-- Firms
    Agent <|-- Banks
    Agent <|-- CentralBank
    Agent <|-- CentralGovernment
    Agent <|-- GovernmentEntities

    Households ..> Individuals : aggregates members
    Households ..> Banks       : holds deposits, takes loans
    Firms ..> Individuals      : employs
    Firms ..> Banks            : borrows from
    Banks ..> CentralBank      : policy rate
    CentralGovernment ..> Individuals : taxes / benefits
    CentralGovernment ..> Firms       : taxes / subsidies
    GovernmentEntities ..> Firms      : buys goods
```

---

# Part A — Worked example: `Individuals`

---

## 1. Class diagram

The class diagram shows the structural skeleton: the `Individuals` agent
inherits from the abstract base `Agent`, holds a `TimeSeries`, references
`IndividualsConfiguration`, and aggregates a set of pluggable *behaviour*
classes (the "function" objects under
[`macromodel/agents/individuals/func/`](../../macromodel/agents/individuals/func/)).

This mirrors Bersini's Figure 2 pattern — keep agents and their behaviours in
separate classes so behaviours can be swapped without touching the agent.

```mermaid
classDiagram
    class Agent {
        <<abstract>>
        +country_name: str
        +states: dict
        +ts: TimeSeries
        +initiate_ts()
        +prepare()
        +set_prices(sell_price)
    }

    class Individuals {
        +functions: dict
        +n_individuals: int
        +from_pickled_agent(...)$
        +reset(config)
        +compute_labour_inputs()
        +compute_reservation_wages(benefits)
        +compute_expected_income(...)
        +compute_income(...)
        +update_demography()
        +save_to_h5(group)
    }

    class TimeSeries {
        +current(name)
        +historic(name)
        +append(value)
    }

    class IndividualsConfiguration {
        +functions
    }

    class ActivityStatus {
        <<enumeration>>
        EMPLOYED
        UNEMPLOYED
        NOT_ECONOMICALLY_ACTIVE
        FIRM_INVESTOR
        BANK_INVESTOR
    }

    class Education {
        <<enumeration>>
        NONE
        PRIMARY
        ...
        DOCTORAL
    }

    class Gender {
        <<enumeration>>
        MALE
        FEMALE
    }

    class IndividualLabourInputsSetter {
        <<abstract>>
        +update_labour_inputs(prev, status)
    }

    class ReservationWageSetter {
        <<abstract>>
        +compute_reservation_wages(...)
    }

    class IncomeFunction {
        +compute_expected_income(...)
        +compute_income(...)
    }

    class DemographyFunction {
        +update(n_individuals)
    }

    Agent <|-- Individuals
    Individuals "1" *-- "1" TimeSeries : owns
    Individuals ..> IndividualsConfiguration : configured by
    Individuals "1" o-- "*" IndividualLabourInputsSetter : functions["labour_inputs"]
    Individuals "1" o-- "*" ReservationWageSetter      : functions["reservation_wages"]
    Individuals "1" o-- "*" IncomeFunction             : functions["income"]
    Individuals "1" o-- "*" DemographyFunction         : functions["demography"]
    Individuals ..> ActivityStatus : uses
    Individuals ..> Education      : uses
    Individuals ..> Gender         : uses
```

**Reading notes (following Bersini §2.1–2.11):**

- The **filled diamond** between `Individuals` and `TimeSeries` is *composition*:
  the time series dies with its owning agent.
- The **open diamonds** to the behaviour classes are *aggregation*: the strategy
  objects are injected from configuration and can be swapped.
- The **dashed arrows** to the enums are *dependency*: enums appear only as
  values inside `states`, not as owned objects.
- `Agent` is *abstract* (italic in UML convention); no plain `Agent` is ever
  instantiated.

---

## 2. Sequence diagram

A single simulation tick triggers many interactions. The sequence diagram
focuses on **one slice**: how an individual's income for the current period is
computed. This is the most common scenario one would want to trace when
debugging or onboarding.

```mermaid
sequenceDiagram
    autonumber
    participant Sim as Simulation
    participant Country
    participant Ind as Individuals
    participant IncomeFn as functions["income"]
    participant TS as TimeSeries

    Sim->>Country: step(t)
    Country->>Ind: compute_income(firm_profits, bank_profits, cpi, taxes, tau_firm)
    Ind->>TS: current("employee_income")
    TS-->>Ind: wages_t
    Ind->>TS: current("income_from_unemployment_benefits")
    TS-->>Ind: benefits_t
    Ind->>IncomeFn: compute_income(activity, wages_t, benefits_t, ...)
    IncomeFn-->>Ind: income_per_individual
    Ind-->>Country: income_per_individual
    Country->>Ind: update_demography()
    Ind->>TS: append n_individuals_{t+1}
```

A second slice — labour-market participation — is short enough to share the
same diagram style:

```mermaid
sequenceDiagram
    participant Country
    participant Ind as Individuals
    participant LabFn as functions["labour_inputs"]
    participant ResFn as functions["reservation_wages"]
    participant TS as TimeSeries

    Country->>Ind: compute_labour_inputs()
    Ind->>TS: current("labour_inputs")
    TS-->>Ind: prev_inputs
    Ind->>LabFn: update_labour_inputs(prev_inputs, activity)
    LabFn-->>Ind: new_inputs

    Country->>Ind: compute_reservation_wages(benefits)
    Ind->>TS: historic("employee_income")
    TS-->>Ind: wage_history
    Ind->>ResFn: compute_reservation_wages(history, activity, benefits)
    ResFn-->>Ind: reservation_wages
```

Per Bersini §2.13–2.16, we keep the diagram deliberately shallow: no nested
`loop`/`alt` frames. The goal is to make the *responsibilities* visible, not to
reproduce the source code.

---

## 3. State diagram

The most useful state machine for an individual in this model is their
**activity status** life-cycle. It comes straight from the
[`ActivityStatus`](../../macromodel/agents/individuals/individual_properties.py)
enum, and transitions are driven by labour-market matching, retirement /
demographic updates, and investment events.

```mermaid
stateDiagram-v2
    [*] --> NotEconomicallyActive : born / pre-working age

    state "Active in labour market" as ACTIVE {
        UNEMPLOYED --> EMPLOYED : job offer accepted\n(offered_wage >= reservation_wage)
        EMPLOYED --> UNEMPLOYED : layoff / firm exit
        NotEconomicallyActive --> UNEMPLOYED : enters labour force
        UNEMPLOYED --> NotEconomicallyActive : discouraged / retires
        EMPLOYED --> NotEconomicallyActive : retires
    }

    ACTIVE --> FIRM_INVESTOR  : acquires firm equity
    ACTIVE --> BANK_INVESTOR  : acquires bank equity
    FIRM_INVESTOR --> ACTIVE  : divests
    BANK_INVESTOR --> ACTIVE  : divests

    ACTIVE --> [*] : death
    FIRM_INVESTOR --> [*] : death
    BANK_INVESTOR --> [*] : death
```

**Notes (Bersini §2.17–2.19):**

- The composite state `Active in labour market` lets us draw the *death*
  transition once, rather than from every leaf state.
- Guards on the `UNEMPLOYED → EMPLOYED` transition correspond to the
  `Started New Job` / `Offered Wage of Accepted Job` flags that the model
  already tracks in `states`.

---

## 4. Activity diagram

Finally, the activity diagram captures the *procedural* flow of what
`Individuals` does within one simulation step. This is the diagram to draw
when you want to explain "what happens in a tick" without showing call sites.

```mermaid
flowchart TD
    Start([Start of tick]) --> A[compute_labour_inputs]
    A --> B[compute_reservation_wages]
    B --> C{Labour market<br/>matching outcome}
    C -- matched --> D[states: Activity Status := EMPLOYED]
    C -- unmatched --> E[states: Activity Status := UNEMPLOYED]
    D --> F[compute_expected_income]
    E --> F
    F --> G[compute_income]
    G --> H[update_demography]
    H --> End([End of tick])

    subgraph PARALLEL [concurrent within compute_income]
        direction LR
        I1[wage component]
        I2[social benefits]
        I3[firm dividends]
        I4[bank dividends]
    end
    G --- PARALLEL
```

The forked block inside `compute_income` is the Bersini "concurrent activities"
construct (§2.21) — these income components are computed jointly per
individual and summed.

---

# Part B — Other agent types

For each of the remaining agents we show two diagrams: a **class diagram**
(structure and behaviour strategies) and an **activity diagram** (what the
agent does in one tick). State diagrams are added only where the agent has a
non-trivial state machine; the same goes for sequence diagrams.

## 5. `Firms`

[`Firms`](../../macromodel/agents/firms/firms.py) is by far the
behaviour-richest agent — production, pricing, hiring, investment, credit,
emissions. The class diagram emphasises the strategy injection pattern in
[`firms/func/`](../../macromodel/agents/firms/func/).

### Class diagram

```mermaid
classDiagram
    class Agent {
        <<abstract>>
    }

    class Firms {
        +functions: dict
        +configuration: FirmsConfiguration
        +intermediate_inputs_productivity_matrix
        +capital_inputs_productivity_matrix
        +capital_inputs_depreciation_matrix
        +goods_criticality_matrix
        +depreciation_rates
        +average_initial_price
        +industries: list~str~
        +bundle_matrix
        +emission_fractions
    }

    class FirmTimeSeries
    class FirmsConfiguration
    class CreditMarket
    class EmissionFractions

    class TargetProduction { <<strategy>> }
    class TargetIntermediateInputs { <<strategy>> }
    class TargetCapitalInputs { <<strategy>> }
    class DesiredLabour { <<strategy>> }
    class Production { <<strategy>> }
    class Prices { <<strategy>> }
    class WageSetter { <<strategy>> }
    class OfferedWageSetter { <<strategy>> }
    class TargetCredit { <<strategy>> }
    class ProductivityInvestmentPlanner { <<strategy>> }
    class ProductivityGrowth { <<strategy>> }
    class DemandEstimator { <<strategy>> }
    class GrowthEstimator { <<strategy>> }
    class ProfitEstimator { <<strategy>> }
    class ExcessDemand { <<strategy>> }
    class BoughtGoodsDistributor { <<strategy>> }
    class Demography { <<strategy>> }

    Agent <|-- Firms
    Firms "1" *-- "1" FirmTimeSeries
    Firms ..> FirmsConfiguration
    Firms ..> CreditMarket
    Firms ..> EmissionFractions
    Firms "1" o-- "*" TargetProduction
    Firms "1" o-- "*" TargetIntermediateInputs
    Firms "1" o-- "*" TargetCapitalInputs
    Firms "1" o-- "*" DesiredLabour
    Firms "1" o-- "*" Production
    Firms "1" o-- "*" Prices
    Firms "1" o-- "*" WageSetter
    Firms "1" o-- "*" OfferedWageSetter
    Firms "1" o-- "*" TargetCredit
    Firms "1" o-- "*" ProductivityInvestmentPlanner
    Firms "1" o-- "*" ProductivityGrowth
    Firms "1" o-- "*" DemandEstimator
    Firms "1" o-- "*" GrowthEstimator
    Firms "1" o-- "*" ProfitEstimator
    Firms "1" o-- "*" ExcessDemand
    Firms "1" o-- "*" BoughtGoodsDistributor
    Firms "1" o-- "*" Demography
```

### State diagram

A firm's solvency status drives its life cycle.

```mermaid
stateDiagram-v2
    [*] --> Active : created from synthetic data

    state Active {
        Producing --> Producing : equity >= 0
        Producing --> Distressed : equity < 0 (one period)
    }

    Active --> Insolvent : equity stays < threshold
    Insolvent --> Active : recapitalised / re-entry
    Insolvent --> [*] : exits
    Active --> [*] : exits (demography)
```

### Activity diagram (one tick)

```mermaid
flowchart TD
    S([Start of tick]) --> EXP[Estimate demand & growth]
    EXP --> PLAN[Set target production]
    PLAN --> INPUTS[Plan intermediate & capital inputs]
    INPUTS --> LAB[Plan desired labour]
    LAB --> CREDIT[Set target credit -> CreditMarket]
    CREDIT --> WAGE[Set wages and offered wages]
    WAGE --> PRICE[Set prices]
    PRICE --> PROD[Produce goods]
    PROD --> SELL[Goods market: sell]
    SELL --> EMIT[Update emissions]
    EMIT --> PROFIT[Estimate profit & update equity]
    PROFIT --> DEM[Demography update / insolvency check]
    DEM --> E([End of tick])
```

---

## 6. `Households`

[`Households`](../../macromodel/agents/households/households.py) handles
consumption, investment, savings, housing, and credit. It is parameterised by
consumption / investment weights and uses a `HouseholdType` enum from
[`household_properties.py`](../../macromodel/agents/households/household_properties.py).

### Class diagram

```mermaid
classDiagram
    class Agent { <<abstract>> }

    class Households {
        +functions
        +consumption_weights
        +consumption_weights_by_income
        +investment_weights
        +use_consumption_weights_by_income
        +independents
        +substitution_bundles
        +emission_fractions
    }

    class HouseholdType {
        <<enumeration>>
        TWO_ADULTS_YOUNGER_THAN_65
        TWO_ADULTS_ONE_AT_LEAST_65
        THREE_OR_MORE_ADULTS
        SINGLE_PARENT_WITH_CHILDREN
        TWO_ADULTS_WITH_ONE_CHILD
        ...
    }

    class Consumption     { <<strategy>> }
    class SavingRates     { <<strategy>> }
    class FinancialAssets { <<strategy>> }
    class Investment      { <<strategy>> }
    class Property        { <<strategy>> }
    class Rent            { <<strategy>> }
    class Wealth          { <<strategy>> }
    class Insolvency      { <<strategy>> }
    class TargetCredit    { <<strategy>> }
    class SocialTransfers { <<strategy>> }

    class CreditMarket
    class Banks
    class Individuals
    class HouseholdsConfiguration

    Agent <|-- Households
    Households ..> HouseholdsConfiguration
    Households ..> HouseholdType : states["Type"]
    Households ..> Individuals : composed of members
    Households ..> Banks       : deposits, loans
    Households ..> CreditMarket
    Households "1" o-- "*" Consumption
    Households "1" o-- "*" SavingRates
    Households "1" o-- "*" FinancialAssets
    Households "1" o-- "*" Investment
    Households "1" o-- "*" Property
    Households "1" o-- "*" Rent
    Households "1" o-- "*" Wealth
    Households "1" o-- "*" Insolvency
    Households "1" o-- "*" TargetCredit
    Households "1" o-- "*" SocialTransfers
```

### Activity diagram (one tick)

```mermaid
flowchart TD
    S([Start of tick]) --> INC[Receive income from member individuals]
    INC --> TRX[Receive social transfers]
    TRX --> SAVE[Compute saving rate]
    SAVE --> CONS[Allocate consumption across industries]
    CONS --> RENT[Pay rent / housing services]
    RENT --> INV[Decide real & financial investment]
    INV --> CRED[Set target credit -> CreditMarket]
    CRED --> WEALTH[Update wealth & financial assets]
    WEALTH --> SOLV{Insolvent?}
    SOLV -- yes --> WRITE[Write down assets / restructure]
    SOLV -- no --> NEXT
    WRITE --> NEXT
    NEXT([End of tick])
```

---

## 7. `Banks`

[`Banks`](../../macromodel/agents/banks/banks.py) intermediate deposits and
loans, set rates as a markup over the central bank's policy rate, and may
become insolvent.

### Class diagram

```mermaid
classDiagram
    class Agent { <<abstract>> }

    class Banks {
        +parameters: BankParameters
        +functions
        +policy_rate_markup: float
        +states["corr_firms"]
        +states["corr_households"]
        +states["is_insolvent"]
    }

    class BankParameters
    class BanksConfiguration
    class CreditMarket
    class CentralBank
    class Firms
    class Households

    class Demography      { <<strategy>> }
    class InterestRates   { <<strategy>> }
    class ProfitEstimator { <<strategy>> }

    Agent <|-- Banks
    Banks ..> BankParameters
    Banks ..> BanksConfiguration
    Banks ..> CreditMarket
    Banks ..> CentralBank : reads policy rate
    Banks ..> Firms       : lends to / takes deposits from
    Banks ..> Households  : lends to / takes deposits from
    Banks "1" o-- "*" Demography
    Banks "1" o-- "*" InterestRates
    Banks "1" o-- "*" ProfitEstimator
```

### State diagram

```mermaid
stateDiagram-v2
    [*] --> Solvent
    Solvent --> Insolvent : equity < threshold
    Insolvent --> Solvent : recapitalised
    Solvent --> [*] : exits
    Insolvent --> [*] : exits
```

### Activity diagram (one tick)

```mermaid
flowchart TD
    S([Start of tick]) --> POL[Read policy rate from CentralBank]
    POL --> RATES[Set loan & deposit interest rates<br/>= policy_rate + markup]
    RATES --> LEND[CreditMarket: extend loans / take deposits]
    LEND --> INT[Accrue interest income & expense]
    INT --> PROF[Compute profits and update equity]
    PROF --> SOLV{Equity below threshold?}
    SOLV -- yes --> INSOLV[Mark insolvent]
    SOLV -- no --> END
    INSOLV --> END([End of tick])
```

---

## 8. `CentralBank`

[`CentralBank`](../../macromodel/agents/central_bank/central_bank.py)
implements a Taylor-style monetary policy rule.

### Class diagram

```mermaid
classDiagram
    class Agent { <<abstract>> }

    class CentralBank {
        +functions
        +states["targeted_inflation_rate"]
        +states["rho"]
        +states["r_star"]
        +states["xi_pi"]
        +states["xi_gamma"]
    }

    class PolicyRate { <<strategy>> }
    class CentralBankConfiguration
    class Banks

    Agent <|-- CentralBank
    CentralBank ..> CentralBankConfiguration
    CentralBank "1" o-- "1" PolicyRate
    CentralBank ..> Banks : sets policy rate consumed by Banks
```

### Activity diagram (one tick)

```mermaid
flowchart TD
    S([Start of tick]) --> OBS[Observe inflation pi_t and output growth gamma_t]
    OBS --> GAP[Compute inflation gap and growth gap]
    GAP --> RULE["Apply Taylor rule:<br/>r_t = rho * r_{t-1} + (1 - rho) * (r_star + pi_target + xi_pi * gap_pi + xi_gamma * gap_gamma)"]
    RULE --> PUB[Publish policy rate for Banks]
    PUB --> E([End of tick])
```

---

## 9. `CentralGovernment`

[`CentralGovernment`](../../macromodel/agents/central_government/central_government.py)
collects taxes (including a progressive PIT) and pays social benefits.

### Class diagram

```mermaid
classDiagram
    class Agent { <<abstract>> }

    class CentralGovernment {
        +functions
        +pit_base_thresholds
        +pit_base_basic_deduction
        +states["pit_thresholds"]
        +states["pit_rates"]
        +states["pit_basic_deduction"]
        +states["tau_firm"]
        +states["tau_vat"]
        +states["tau_sic"]
        +step_pit_brackets(cpi)
        +collect_taxes(...)
        +pay_benefits(...)
    }

    class CentralGovernmentConfiguration
    class TaxData
    class SocialBenefits { <<strategy>> }
    class SocialHousing  { <<strategy>> }
    class ProgressivePIT { <<function>> }
    class Individuals
    class Firms
    class Households

    Agent <|-- CentralGovernment
    CentralGovernment ..> CentralGovernmentConfiguration
    CentralGovernment ..> TaxData
    CentralGovernment "1" o-- "*" SocialBenefits
    CentralGovernment "1" o-- "*" SocialHousing
    CentralGovernment ..> ProgressivePIT : uses compute_progressive_tax
    CentralGovernment ..> Individuals : taxes income, pays benefits
    CentralGovernment ..> Firms       : corporate tax, subsidies
    CentralGovernment ..> Households  : transfers
```

### Activity diagram (one tick)

```mermaid
flowchart TD
    S([Start of tick]) --> CPI[Read current CPI]
    CPI --> IDX[step_pit_brackets:<br/>inflation-index thresholds & basic deduction]
    IDX --> VAT[Collect VAT from goods-market sales]
    VAT --> CORP[Collect corporate tax from Firms]
    CORP --> PIT[Compute PIT per Individual<br/>via compute_progressive_tax]
    PIT --> SIC[Collect social insurance contributions]
    SIC --> BEN[Pay unemployment & other social benefits<br/>via SocialBenefits / SocialHousing]
    BEN --> BAL[Update revenue, expenditure, deficit, debt]
    BAL --> E([End of tick])
```

---

## 10. `GovernmentEntities`

[`GovernmentEntities`](../../macromodel/agents/government_entities/government_entities.py)
models the public sector as a goods-market buyer (government consumption and
investment).

### Class diagram

```mermaid
classDiagram
    class Agent { <<abstract>> }

    class GovernmentEntities {
        +functions
        +n_transactors: int
        +states["consumption_model"]
        +emission tracking
    }

    class Consumption { <<strategy>> }
    class GovernmentEntitiesConfiguration
    class Firms

    Agent <|-- GovernmentEntities
    GovernmentEntities ..> GovernmentEntitiesConfiguration
    GovernmentEntities "1" o-- "*" Consumption
    GovernmentEntities ..> Firms : buys goods (goods market)
```

### Activity diagram (one tick)

```mermaid
flowchart TD
    S([Start of tick]) --> EXP[Form expectations:<br/>growth + inflation]
    EXP --> PLAN[Plan nominal consumption per entity]
    PLAN --> ALLOC[Allocate spending across industries]
    ALLOC --> BUY[Goods market: place buy orders]
    BUY --> EMIT[Update emissions from consumption]
    EMIT --> E([End of tick])
```

---

## Why these four diagrams?

Bersini's central argument is that **UML pays off as model complexity grows**.
We picked the four diagrams (class, sequence, state, activity) that have the
highest signal-to-effort ratio for ABM work, and added the simplest cuts that
match each agent: every agent gets a class + activity diagram; we add a state
diagram only where the agent really has a state machine (`Individuals`,
`Firms`, `Banks`) and a sequence diagram only where the call flow benefits
from being traced (`Individuals`).

If a follow-up is needed, natural extensions are:

- A sequence diagram of one **goods-market clearing** round across
  `Firms`, `Households`, and `GovernmentEntities`.
- A sequence diagram of one **credit-market round** across `Firms`,
  `Households`, and `Banks`.
- An activity diagram of one **full `Simulation.step()`**.

## Reference

Bersini, H. (2012). *UML for ABM*. Journal of Artificial Societies and Social
Simulation 15 (1) 9. <https://www.jasss.org/15/1/9.html>
