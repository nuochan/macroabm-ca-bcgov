# UML Demo: Package Diagram

This diagram shows the **module-level dependency structure** of the
`macroabm-ca` codebase — a "table of contents" for the repository that
no other UML diagram provides. Package diagrams were the most frequently
recommended addition in the post-Bersini ABM/UML literature (Collins et al.
2015; Niazi & Hussain 2012).

Each box is a top-level Python package in this repo. Arrows indicate
*pacakge dependency* (i.e., `A → B` means `A` imports from `B`).

```mermaid
flowchart LR
    subgraph external[External Python ecosystem]
        numpy
        pandas
        h5py
        numba
        pydantic
    end

    subgraph repo[macroabm-ca]
        direction TB

        subgraph data[macro_data]
            d_readers[readers]
            d_process[processing]
            d_cfg[configuration]
            d_util[util]
            dw[data_wrapper.py]
        end

        subgraph model[macromodel]
            m_country[country]
            m_agents[agents]
            m_markets[markets]
            m_econ[economy]
            m_exo[exogenous]
            m_ex[exchange_rates]
            m_row[rest_of_the_world]
            m_cfg[configurations]
            m_ts[timeseries]
            m_sim[simulation.py]
        end

        subgraph calib[macrocalib]
            c_sampler[sampler]
            c_train[training]
        end

        subgraph tests[tests]
            t_data[test_macro_data]
            t_model[test_macromodel]
            t_calib[test_macrocalib]
        end
    end

    numpy --> model
    numpy --> data
    pandas --> model
    pandas --> data
    h5py --> model
    numba --> model
    pydantic --> model

    d_readers --> d_util
    dw --> d_readers
    dw --> d_process
    dw --> d_cfg

    m_agents --> model
    m_markets --> model
    m_country --> m_agents
    m_country --> m_markets
    m_country --> m_econ
    m_country --> m_exo
    m_country --> m_row
    m_sim --> m_country
    m_sim --> m_ex
    m_sim --> m_row
    m_cfg --> model

    model -->|depends on| data
    calib -->|trains against| model
    calib -->|uses| data
    tests --> model
    tests --> data
    tests --> calib
```

## Reading notes

| Package | Role | Key dependencies |
|---|---|---|
| `macro_data` | Data ingestion, synthetic-country generation, configuration | `pandas`, `numpy` |
| `macromodel` | Simulation engine: agents, markets, country orchestration | `macro_data`, `numpy`, `numba`, `h5py`, `pydantic` |
| `macrocalib` | Calibration: sampling, training routines | `macromodel`, `macro_data` |
| `tests` | Unit/integration tests for all three packages | All three |

The diagram makes explicit what `pyproject.toml` declares via `[tool.setuptools.packages]`
but doesn't visualize: `macromodel` is the central package; everything else
either feeds data in or validates/calibrates the output.

## References

- Collins, A., Petty, M., Vernon-Bido, D., & Sherfey, S. (2015). A Call to Arms:
  Standards for Agent-Based Modeling and Simulation. *JASSS* 18(3)12.
- Niazi, M. A., & Hussain, A. (2012). Cognitive Agent-based Computing-I: A
  Unified Framework for Modeling Complex Adaptive Systems using Agent-based &
  Complex Network-based Methods. Springer.
