# UML Demo: The `Households` Agent

This page applies Bersini's four-diagram UML subset to the [`Households`](../../macromodel/agents/households/households.py)
agent. See the [Individuals UML demo](uml_individual_agent_demo.md) for methodology references.

Reference: Bersini, H. (2012). [*UML for ABM*](https://www.jasss.org/15/1/9.html). JASSS 15(1)9.

---

## 1. Class diagram

The `Households` agent inherits from `Agent`, holds consumption/investment weight matrices,
and aggregates 10 strategy classes. It also depends on the `HouseholdType` enum and the
`Banks` agent for credit-market interactions.

```mermaid
classDiagram
    class Agent {
        <<abstract>>
        +country_name: str
        +states: dict
        +ts: TimeSeries
        +initiate_ts()
        +prepare()
        +set_goods_to_buy()
        +set_goods_to_sell()
    }

    class Households {
        +functions: dict
        +independents: list[str]
        +consumption_weights: ndarray
        +consumption_weights_by_income: ndarray
        +investment_weights: ndarray
        +use_consumption_weights_by_income: bool
        +substitution_bundles: list
        +bundle_matrix: ndarray
        +emission_fractions: EmissionFractions
        +from_pickled_agent(...)$
        +reset(config)
        +compute_employee_income(ind_income, corr_hh)
        +compute_expected_social_transfer_income(...)
        +compute_social_transfer_income(...)
        +compute_rental_income(housing_data, taxes)
        +compute_expected_income_from_financial_assets()
        +compute_income_from_financial_assets()
        +compute_expected_income()
        +compute_income()
        +get_saving_rates_by_household()
        +compute_target_consumption(...)
        +compute_target_investment(...)
        +compute_property_decisions(...)
    }

    class HouseholdType {
        <<enumeration>>
        TYPE_1
        TYPE_2
        ...
    }

    class ConsumptionFunction {
        +compute_target_consumption(...)
    }
    class InvestmentFunction {
        +compute_target_investment(...)
    }
    class SavingRatesFunction {
        +get_saving_rates(...)
    }
    class SocialTransfersFunction {
        +get_social_transfers(...)
    }
    class FinancialAssetsFunction {
        +compute_expected_income(...)
        +compute_income(...)
    }
    class WealthFunction {
        +compute_wealth(...)
    }
    class PropertyFunction {
        +compute_property_decisions(...)
    }
    class RentFunction {
        +compute_rent(...)
    }
    class TargetCreditFunction {
        +compute_target_credit(...)
    }
    class InsolvencyFunction {
        +check_insolvency(...)
    }

    Agent <|-- Households
    Households ..> HouseholdType : uses
    Households "1" o-- "*" ConsumptionFunction : functions["consumption"]
    Households "1" o-- "*" InvestmentFunction : functions["investment"]
    Households "1" o-- "*" SavingRatesFunction : functions["saving_rates"]
    Households "1" o-- "*" SocialTransfersFunction : functions["social_transfers"]
    Households "1" o-- "*" FinancialAssetsFunction : functions["financial_assets"]
    Households "1" o-- "*" WealthFunction : functions["wealth"]
    Households "1" o-- "*" PropertyFunction : functions["property"]
    Households "1" o-- "*" RentFunction : functions["rent"]
    Households "1" o-- "*" TargetCreditFunction : functions["target_credit"]
    Households "1" o-- "*" InsolvencyFunction : functions["insolvency"]
```

---

## 2. Sequence diagram

Two key flows: income aggregation (from the four income sources) and consumption planning.

```mermaid
sequenceDiagram
    autonumber
    participant Country
    participant HH as Households
    participant SaveFn as functions["saving_rates"]
    participant ConsFn as functions["consumption"]
    participant InvFn as functions["investment"]
    participant TSAs TimeSeries

    Note over Country,HH: Income aggregation
    Country->>HH: compute_employee_income(ind_income, corr_hh)
    HH-->>Country: employment_income_per_hh
    Country->>HH: compute_social_transfer_income(budget, cpi)
    HH->>HH: functions["social_transfers"].get_social_transfers(...)
    HH-->>Country: transfers_per_hh
    Country->>HH: compute_rental_income(housing_data, taxes)
    HH-->>Country: rental_income_per_hh
    Country->>HH: compute_income_from_financial_assets()
    HH->>HH: functions["financial_assets"].compute_income(...)
    HH-->>Country: financial_income_per_hh
    Country->>HH: compute_income()
    HH-->>Country: total_income_per_hh

    Note over Country,HH: Consumption & investment planning
    Country->>HH: get_saving_rates_by_household()
    HH->>SaveFn: get_saving_rates(...)
    SaveFn-->>HH: saving_rates
    Country->>HH: compute_target_consumption(inflation, cpi, ...)
    HH->>ConsFn: compute_target_consumption(saving_rates, income, ...)
    ConsFn-->>HH: target_consumption
    Country->>HH: compute_target_investment(inflation, cpi, ...)
    HH->>InvFn: compute_target_investment(...)
    InvFn-->>HH: target_investment
```

---

## 3. State diagram

Household economic states revolve around tenure (owner/renter), wealth, and solvency.

```mermaid
stateDiagram-v2
    [*] --> Active : household formed

    state "Tenure status" as TENURE {
        OwnerOccupier : owner-occupier
        Renter : renter
        OwnerOccupier --> Renter : sells / defaults
        Renter --> OwnerOccupier : buys property
    }

    state "Wealth status" as WEALTH {
        Saver : net saver (wealth > 0)
        Borrower : net borrower (wealth < 0)
        Saver --> Borrower : negative saving
        Borrower --> Saver : positive saving
    }

    Active --> TENURE : each period
    Active --> WEALTH : each period

    Active --> Insolvent : cannot service debt
    Insolvent --> [*] : household exit

    Active --> [*] : demographic exit
```

---

## 4. Activity diagram

One household tick: income → saving → consumption → investment → wealth update.

```mermaid
flowchart TD
    Start([Start of tick]) --> A[Aggregate income: employment + transfers + rental + financial]
    A --> B[Get saving rates by household]
    B --> C[Compute target consumption]
    C --> D[Compute target investment]
    D --> E[Goods market: buy consumption & investment goods]
    E --> F[Housing market: property decisions]
    F --> G[Credit market: borrow / repay]
    G --> H[Update wealth: assets - liabilities]
    H --> I[Check insolvency]
    I --> End([End of tick])

    subgraph PARALLEL [Concurrent income sources]
        direction LR
        S1[employment income]
        S2[social transfers]
        S3[rental income]
        S4[financial asset income]
    end
    A --- PARALLEL
```

---

*See also:* [Individuals UML demo](uml_individual_agent_demo.md), [Firms UML demo](uml_firms_agent_demo.md), [Bersini (2012)](https://www.jasss.org/15/1/9.html).
