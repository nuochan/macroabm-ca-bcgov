# UML Diagrams for macroabm-ca

This directory contains UML diagrams for the macroabm-ca agent-based macroeconomic
model, organised into two **parallel** folders for comparison:

## Folder Structure

```
docs/diagrams/
├── upstream_model/          ← Original upstream (uvic-sesit) flat-tax design
│   ├── README.md
│   ├── uml_individuals.md
│   ├── uml_households.md
│   ├── uml_firms.md
│   ├── uml_banks.md
│   ├── uml_central_bank.md
│   ├── uml_central_government.md
│   ├── uml_government_entities.md
│   ├── uml_country.md
│   ├── uml_system_wide.md
│   ├── uml_package.md
│   └── uml_object.md
│
├── pit_update/              ← Progressive PIT (Personal Income Tax) update
│   ├── README.md            (includes PIT impact summary per agent)
│   ├── uml_individuals.md
│   ├── uml_households.md
│   ├── uml_firms.md
│   ├── uml_banks.md
│   ├── uml_central_bank.md
│   ├── uml_central_government.md
│   ├── uml_government_entities.md
│   ├── uml_country.md
│   ├── uml_pit_module.md
│   ├── uml_system_wide.md
│   ├── uml_package.md
│   └── uml_object.md
│
├── uml_use_case_diagram.md  ← Shared (identical in both designs)
│
└── (11 agent demos)         ← Superseded — removed in cleanup
```

## Quick Comparison

| Aspect | `upstream_model/` | `pit_update/` |
|--------|-------------------|-----------------|
| **Source** | [uvic-sesit/macroabm-ca](https://github.com/uvic-sesit/macroabm-ca) | PIT feature branch |
| **Income Tax** | Flat scalar on all income | Progressive brackets on wages; flat on rent/financial |
| **CPI Indexation** | None | Annual compound inflation |
| **Basic Deduction** | None | Non-refundable credit |
| **Brackets** | None | 6 brackets (BC example) |
| **Agents modified** | — | CentralGovernment (major), Country (minor) |

## PIT Impact Summary

Only **one agent** is materially modified by the PIT update:

| Agent | Impact |
|-------|--------|
| **CentralGovernment** | 🔴 Major — progressive brackets, CPI indexation, basic deduction |
| **Country** | 🟡 Minor — pre-calibration of effective rate at t=0 |
| All other agents | 🟢 Unchanged |

## Methodology

All diagrams follow Bersini (2012), *UML for ABM*, JASSS 15(1)9.
