# UML Demo: The `Banks` Agent

This page applies Bersini's four-diagram UML subset to the [`Banks`](../../macromodel/agents/banks/banks.py)
agent — the financial intermediation sector. See the [Individuals UML demo](uml_individual_agent_demo.md) for methodology references.

Reference: Bersini, H. (2012). [*UML for ABM*](https://www.jasss.org/15/1/9.html). JASSS 15(1)9.

---

## 1. Class diagram

`Banks` inherits from `Agent`, holds `BankParameters` and a policy-rate markup,
and aggregates 3 strategy classes: interest-rate setting, profit estimation, and demography.

```mermaid
classDiagram
    class Agent {
        <<abstract>>
        +country_name: str
        +states: dict
        +ts: TimeSeries
    }

    class Banks {
        +functions: dict
        +parameters: BankParameters
        +policy_rate_markup: float
        +from_pickled_agent(...)$
        +reset(config)
        +compute_estimated_profits(growth, inflation)
        +set_interest_rates(policy_rate)
        +compute_interest_received_on_deposits(policy_rate)
        +compute_profits()
        +update_deposits(firm_deposits, hh_deposits, ...)
        +update_loans(credit_market)
        +save_to_h5(group)
    }

    class BankParameters {
        +n_banks: int
    }

    class InterestRateSetter {
        +get_interest_rates_on_short_term_firm_loans(...)
        +get_interest_rates_on_long_term_firm_loans(...)
        +get_interest_rates_on_household_consumption_loans(...)
        +get_interest_rate_on_mortgages(...)
        +compute_interest_rate_on_firm_deposits(...)
        +compute_overdraft_rate_on_firm_deposits(...)
        +compute_interest_rate_on_household_deposits(...)
        +compute_overdraft_rate_on_household_deposits(...)
    }

    class ProfitEstimator {
        +compute_estimated_profits(...)
    }

    class DemographyFunction {
        +update(...)
    }

    Agent <|-- Banks
    Banks "1" *-- "1" BankParameters : parameters
    Banks "1" o-- "*" InterestRateSetter : functions["interest_rates"]
    Banks "1" o-- "*" ProfitEstimator : functions["profit_estimator"]
    Banks "1" o-- "*" DemographyFunction : functions["demography"]
```

---

## 2. Sequence diagram

The primary flow: the central bank sets a policy rate, then each bank passes it through
to its loan and deposit rates using error-correction parameters (PT/ECT).

```mermaid
sequenceDiagram
    autonumber
    participant CB as CentralBank
    participant B as Banks
    participant IRFn as functions["interest_rates"]
    participant CreditM as CreditMarket
    participant TS as TimeSeries

    CB->>B: set_interest_rates(policy_rate)

    Note over B,IRFn: Loan rates
    B->>IRFn: get_interest_rates_on_short_term_firm_loans(policy_rate, prev, pt, ect)
    IRFn-->>B: short_term_firm_rate
    B->>IRFn: get_interest_rates_on_long_term_firm_loans(...)
    IRFn-->>B: long_term_firm_rate
    B->>IRFn: get_interest_rates_on_household_consumption_loans(...)
    IRFn-->>B: hh_consumption_rate
    B->>IRFn: get_interest_rate_on_mortgages(...)
    IRFn-->>B: mortgage_rate

    Note over B,IRFn: Deposit rates
    B->>IRFn: compute_interest_rate_on_firm_deposits(...)
    IRFn-->>B: firm_deposit_rate
    B->>IRFn: compute_overdraft_rate_on_firm_deposits(...)
    IRFn-->>B: firm_overdraft_rate
    B->>IRFn: compute_interest_rate_on_household_deposits(...)
    IRFn-->>B: hh_deposit_rate

    Note over B,CreditM: End of period
    CreditM->>B: update_loans(credit_market)
    B->>B: compute_interest_received_on_deposits(policy_rate)
    B->>B: compute_profits()
```

---

## 3. State diagram

A bank has one critical binary state: solvent vs. insolvent.

```mermaid
stateDiagram-v2
    [*] --> Active : bank created

    Active --> Solvent : equity >= 0
    Solvent --> Insolvent : equity < 0
    Insolvent --> [*] : bank resolution / exit
    Active --> [*] : exit
```

---

## 4. Activity diagram

One bank tick: receive policy rate → set all product rates → receive deposits → service credit market.

```mermaid
flowchart TD
    Start([Start of tick]) --> A[Receive policy_rate from central bank]
    A --> B[Set short-term firm loan rates]
    A --> C[Set long-term firm loan rates]
    A --> D[Set household consumption loan rates]
    A --> E[Set mortgage rates]
    A --> F[Set firm deposit rates]
    A --> G[Set household deposit rates]
    B & C & D & E & F & G --> H[Update deposits from firms & households]
    H --> I[Credit market: update loans]
    I --> J[Compute interest received on loans + deposits]
    J --> K[Compute profits]
    K --> L[Update demography]
    L --> End([End of tick])
```

---

*See also:* [Individuals UML demo](uml_individual_agent_demo.md), [Bersini (2012)](https://www.jasss.org/15/1/9.html).
