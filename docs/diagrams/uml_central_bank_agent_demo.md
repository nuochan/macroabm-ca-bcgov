# UML Demo: The `CentralBank` Agent

This page applies Bersini's four-diagram UML subset to the [`CentralBank`](../../macromodel/agents/central_bank/central_bank.py)
agent — the monetary policy authority. See the [Individuals UML demo](uml_individual_agent_demo.md) for methodology references.

Reference: Bersini, H. (2012). [*UML for ABM*](https://www.jasss.org/15/1/9.html). JASSS 15(1)9.

---

## 1. Class diagram

`CentralBank` is the simplest agent: inherits from `Agent`, holds a single strategy
(`policy_rate`), and tracks a handful of monetary-policy parameters in `states`.

```mermaid
classDiagram
    class Agent {
        <<abstract>>
        +country_name: str
        +states: dict
        +ts: TimeSeries
    }

    class CentralBank {
        +functions: dict
        +from_pickled_agent(...)$
        +reset(config)
        +compute_rate(inflation, growth)
        +save_to_h5(group)
    }

    class PolicyRateFunction {
        +compute_rate(prev_rate, inflation, growth, central_bank_states)
    }

    Agent <|-- CentralBank
    CentralBank "1" o-- "*" PolicyRateFunction : functions["policy_rate"]
```

**Key `states` parameters (Taylor-rule family):**

| State | Role |
|-------|------|
| `targeted_inflation_rate` | π* — inflation target |
| `rho` | Interest-rate smoothing coefficient |
| `r_star` | r* — natural real interest rate |
| `xi_pi` | ξ_π — inflation gap response |
| `xi_gamma` | ξ_γ — output growth response |

---

## 2. Sequence diagram

One method, one flow: the central bank computes the policy rate from inflation and growth.

```mermaid
sequenceDiagram
    autonumber
    participant Country
    participant CB as CentralBank
    participant PRFn as functions["policy_rate"]
    participant TS as TimeSeries

    Country->>CB: compute_rate(inflation, growth)
    CB->>TS: current("policy_rate")
    TS-->>CB: prev_rate
    CB->>PRFn: compute_rate(prev_rate, inflation, growth, states)
    PRFn-->>CB: new_policy_rate
    CB-->>Country: new_policy_rate
```

---

## 3. State diagram

The central bank operates in two policy stances differentiated by the inflation gap.

```mermaid
stateDiagram-v2
    [*] --> Normal : simulation start

    state "Policy stance" as STANCE {
        Tightening : inflation > target
        Easing : inflation < target
        Neutral : inflation ≈ target

        Tightening --> Easing : inflation falls below target
        Easing --> Tightening : inflation rises above target
        Neutral --> Tightening : overshoot
        Neutral --> Easing : undershoot
    }

    Normal --> STANCE : each tick
```

---

## 4. Activity diagram

```mermaid
flowchart TD
    Start([Start of tick]) --> A[Receive inflation & growth from economy]
    A --> B[Retrieve previous policy rate from time series]
    B --> C[Apply monetary policy rule #40;Taylor-type#41;]
    C --> D[Apply interest-rate smoothing #40;rho#41;]
    D --> E[Return new policy_rate]
    E --> End([End of tick])
```

---

*See also:* [Banks UML demo](uml_banks_agent_demo.md), [Bersini (2012)](https://www.jasss.org/15/1/9.html).
