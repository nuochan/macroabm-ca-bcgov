# Progressive PIT Update — UML Diagrams

These diagrams document the model **after** the progressive Personal Income Tax
(PIT) update. Each agent diagram explains whether and how that agent was affected.
Compare with the [upstream flat-tax design](../upstream_model/).

## What Changed

| Change | Upstream | PIT Update |
|--------|----------|------------|
| **Income Tax on wages** | Flat scalar | Progressive multi-bracket |
| **Income Tax on rent/financial** | Flat scalar | Flat scalar (unchanged) |
| **Brackets** | None | 6 brackets (BC 2014 example) |
| **CPI Indexation** | None | Annual compound inflation of thresholds |
| **Basic Deduction** | None | Non-refundable credit |
| **Pre-calibration at t=0** | None | Effective rate computed from initial income distribution |
| **New files** | — | `pit_schedule.py`, `BC_PIT_2014.csv`, `bc_cpi_inflation.csv` |
| **Modified files** | — | `central_government.py`, `central_government_configuration.py`, `country.py`, `run_simulation.py` |

## Agent Diagrams — with PIT impact

| File | Agent | PIT Impact |
|------|-------|------------|
| [`uml_individuals.md`](uml_individuals.md) | Individuals | 🟢 Unchanged |
| [`uml_households.md`](uml_households.md) | Households | 🟢 Unchanged |
| [`uml_firms.md`](uml_firms.md) | Firms | 🟢 Unchanged |
| [`uml_banks.md`](uml_banks.md) | Banks | 🟢 Unchanged |
| [`uml_central_bank.md`](uml_central_bank.md) | CentralBank | 🟢 Unchanged |
| [`uml_central_government.md`](uml_central_government.md) | CentralGovernment | 🔴 Modified — progressive brackets, CPI indexation, basic deduction |
| [`uml_government_entities.md`](uml_government_entities.md) | GovernmentEntities | 🟢 Unchanged |

## System & Module Diagrams

| File | Content |
|------|---------|
| [`uml_country.md`](uml_country.md) | Country orchestrator — 🟡 Modified (pre-calibration at t=0) |
| [`uml_pit_module.md`](uml_pit_module.md) | 🆕 PITSchedule module — class, data format, algorithm, CPI flow |
| [`uml_system_wide.md`](uml_system_wide.md) | System-wide diff — which components changed, cross-agent sequence, config diff |
| [`uml_package.md`](uml_package.md) | Package dependencies — new `personal_income_tax` sub-package and modified files highlighted |
| [`uml_object.md`](uml_object.md) | Runtime object snapshot at t=12 — progressive PIT state with 🆕 fields highlighted |

## PIT Impact Summary by Agent

```
Individuals       🟢  No changes — progressive tax applied downstream in CentralGovernment
Households        🟢  No changes — reads scalar effective Income Tax rate
Firms             🟢  No changes — corporate tax unaffected; wage-setting uses effective rate
Banks             🟢  No changes — corporate tax only
CentralBank       🟢  No changes — monetary policy independent of tax structure
CentralGovernment 🔴  MAIN CHANGE — progressive brackets, CPI indexation, basic deduction
GovernmentEntities🟢  No changes — spending side only
Country           🟡  Minor change — pre-calibration of effective rate at t=0
```

## Design Principles

1. **Dual tax rate tracking**: Scalar `Income Tax` (effective rate) + bracket arrays → behavioral code unchanged
2. **Employee-only progressivity**: Only wages use brackets; rent & financial stay flat
3. **Backward compatible**: `pit_brackets=None` → original flat tax behaviour
4. **Compound CPI indexation**: `threshold = nominal × ∏(1+CPI_y)` — safe for repeated calls
5. **Non-refundable credit**: `Credit = basic_deduction × lowest_marginal_rate`

## Configuration Entry Point

```python
config = CentralGovernmentConfiguration(
    pit_brackets=[
        (37606, 0.077),
        (75213, 0.105),
        (86354, 0.1229),
        (104858, 0.147),
        (150000, 0.168),
    ],
    pit_basic_deduction=9869
)
```

## Compare With

See [`../upstream_model/`](../upstream_model/) for the original flat-tax design.
