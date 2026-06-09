# UML Demo: Use Case Diagram

Bersini (2012, §4.5) dismissed use case diagrams as "of minor importance for
most ABM modelling endeavours." However, Kravari & Bassiliades (2015) and
Collins et al. (2015) pushed back, arguing that ABMs with **multiple user
personas** benefit from explicitly documenting *who does what*.

This repo has three distinct user roles — each with different entry points,
expectations, and output needs.

```mermaid
graph TD
    DE[("Data Engineer\n(ingests raw data)")]
    CAL[("Calibrator\n(tunes model parameters)")]
    AN[("Policy Analyst\n(runs scenarios)")]

    subgraph system[macroabm-ca]
        UC1["Prepare Synthetic Country\n- Read raw macro data (OECD, IMF, WB, …)\n- Generate synthetic firms, banks, population\n- Validate coherence"]
        UC2["Calibrate Parameters\n- Run sampler over parameter space\n- Train against historical time series\n- Select best-fit configuration"]
        UC3["Run Simulation\n- Load calibrated configuration\n- Execute Simulation.run()\n- Save outputs to HDF5"]
        UC4["Analyse Results\n- Read HDF5 output\n- Compute statistics (Gini, growth, CPI)\n- Visualise time series / maps"]
        UC5["Extend Model\n- Add new agent type or behavior\n- Implement new market mechanism\n- Add new data reader"]
    end

    DE  --> UC1
    DE  --> UC5
    CAL --> UC2
    CAL --> UC3
    AN  --> UC3
    AN  --> UC4
    DE  --> UC5
    CAL --> UC5

    UC1 -.->|«include»| UC2 : valid data required
    UC2 -.->|«include»| UC3 : calibration tested via short runs
    UC3 -.->|«include»| UC4 : output needed for analysis
```

## Use case narratives

### UC1: Prepare Synthetic Country

| Field | Detail |
|---|---|
| **Actor** | Data Engineer |
| **Precondition** | Raw data files available in expected format |
| **Flow** | 1. Run `macro_data` readers → 2. Generate synthetic firms, households, individuals, etc. → 3. Validate inter-component coherence |
| **Postcondition** | One or more `SyntheticCountry` objects ready for simulation |
| **Entry point** | `DataWrapper` / `SyntheticCountry.from_readers()` |

### UC2: Calibrate Parameters

| Field | Detail |
|---|---|
| **Actor** | Calibrator |
| **Precondition** | Synthetic country exists; historical target series available |
| **Flow** | 1. Define parameter ranges → 2. Run `macrocalib.sampler` across parameter space → 3. For each sample, run short simulation → 4. Score against historical data → 5. Select best-fit params |
| **Postcondition** | Calibrated `SimulationConfiguration` written to disk |
| **Entry point** | `macrocalib/training/` |

### UC3: Run Simulation

| Field | Detail |
|---|---|
| **Actor** | Calibrator or Policy Analyst |
| **Precondition** | Calibrated simulation configuration; valid synthetic data |
| **Flow** | 1. `Simulation.from_datawrapper()` → 2. Optional: attach pre/post hooks → 3. `Simulation.run()` |
| **Postcondition** | HDF5 file with per-agent, per-tick time series |
| **Entry point** | `Simulation.iterate()` / `Simulation.run()` |

### UC4: Analyse Results

| Field | Detail |
|---|---|
| **Actor** | Policy Analyst |
| **Precondition** | HDF5 output exists |
| **Flow** | 1. Open HDF5 → 2. Read time series (per country, per agent) → 3. Compute aggregates / Gini / CPI trajectories → 4. Plot |
| **Postcondition** | Charts, tables, or report ready for policy discussion |
| **Entry point** | `test_run/summary_and_viz.py`, `test_run/compare_can_bc.py` |

### UC5: Extend Model

| Field | Detail |
|---|---|
| **Actor** | Data Engineer or Calibrator (developer hat) |
| **Precondition** | Working codebase; understanding of `Agent` base class and `functions` injection |
| **Flow** | 1. Add new agent class or behavior function → 2. Add corresponding data reader/processor → 3. Wire into `Country` → 4. Test with existing configurations |
| **Postcondition** | New feature available for calibration and simulation |
| **Entry point** | Any file under `macromodel/agents/`, `macromodel/markets/`, or `macro_data/readers/` |

## Why a use case diagram here?

Bersini was right that many ABMs have one user (the researcher who wrote it).
But this repo was built for **others to extend and reuse** — it has a
`SCM Providers` badge, a full `mkdocs` site, and pluggable function injection.
Those are the hallmarks of a multi-user system, where use case diagrams pay off.

## References

- Kravari, K., & Bassiliades, N. (2015). A Survey of Agent Platforms. *Journal
  of Artificial Societies and Social Simulation* 18(1)11.
- Collins, A., Petty, M., Vernon-Bido, D., & Sherfey, S. (2015). A Call to Arms:
  Standards for Agent-Based Modeling and Simulation. *JASSS* 18(3)12.
- Bersini, H. (2012). UML for ABM. *JASSS* 15(1)9. (see §4.5 for the original
  dismissal of use case diagrams.)
