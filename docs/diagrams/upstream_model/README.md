# Upstream Model UML Diagrams

These diagrams document the **original** upstream model design from
[`uvic-sesit/macroabm-ca`](https://github.com/uvic-sesit/macroabm-ca) — the
baseline before any PIT (Progressive Income Tax) changes.

## Design Summary

| Characteristic | Description |
|---------------|-------------|
| **Income Tax** | Single flat scalar rate applied to all income types |
| **Tax Configuration** | No tax fields in config — all rates come from data |
| **Brackets** | None — no progressive schedule |
| **CPI Indexation** | None |
| **Basic Deduction** | None |
| **Pre-calibration** | None — scalar rate loaded directly from data |

## Agent Diagrams

| File | Agent | Description |
|------|-------|-------------|
| [`uml_individuals.md`](uml_individuals.md) | Individuals | Class, sequence, activity — labor supply and income |
| [`uml_households.md`](uml_households.md) | Households | Class, sequence — consumption, investment, wealth |
| [`uml_firms.md`](uml_firms.md) | Firms | Class, sequence — production, pricing, employment |
| [`uml_banks.md`](uml_banks.md) | Banks | Class, sequence — deposits, loans, interest rates |
| [`uml_central_bank.md`](uml_central_bank.md) | CentralBank | Class, activity — monetary policy (Taylor-type rule) |
| [`uml_central_government.md`](uml_central_government.md) | CentralGovernment | Class, sequence, activity, config — flat-tax fiscal authority |
| [`uml_government_entities.md`](uml_government_entities.md) | GovernmentEntities | Class, activity — public consumption and spending |

## System Diagrams

| File | Content |
|------|---------|
| [`uml_country.md`](uml_country.md) | Country orchestrator — class, sequence, activity diagrams |
| [`uml_system_wide.md`](uml_system_wide.md) | Full system architecture — cross-agent class, sequence, activity, config overview |
| [`uml_package.md`](uml_package.md) | Package dependencies and tax data flow |
| [`uml_object.md`](uml_object.md) | Runtime object snapshot at t=12 — flat-tax state verification |

## Compare With

See [`../pit_update/`](../pit_update/) for diagrams showing the progressive PIT update changes.
