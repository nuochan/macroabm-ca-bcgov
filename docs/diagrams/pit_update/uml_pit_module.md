# UML: PIT (Progressive Income Tax) Module — Architecture

This page documents the new `pit_schedule.py` module introduced by the progressive PIT update.
It lives in `macro_data/readers/taxation/personal_income_tax/` and provides:

- Multi-bracket tax schedule loading from CSV
- CPI inflation indexation of bracket thresholds
- Vectorized progressive tax computation
- Non-refundable basic personal amount support

Compare with the [upstream design](../upstream_model/uml_package.md) which has no such module.

---

## 1. Class diagram — PITSchedule and compute functions

```mermaid
classDiagram
    class PITSchedule {
        +brackets_df: DataFrame
        +cpi_rates: dict[int, float]
        +base_year: int
        +from_name_with_cpi(name)$ PITSchedule
        +from_csv(path, cpi_csv)$ PITSchedule
        +get_brackets(tax_year) tuple[ndarray, ndarray, ndarray, ndarray]
        +get_basic_deduction(tax_year) float
        +get_lowest_marginal_rate() float
        -_inflate_thresholds(tax_year) ndarray
        -_compute_quick_adds(thresholds, rates, lower_bounds) ndarray
    }

    class compute_progressive_tax {
        +compute_progressive_tax(incomes, thresholds, rates) ndarray
    }

    class compute_progressive_tax_quick {
        +compute_progressive_tax_quick(incomes, thresholds, quick_adds) ndarray
    }

    class fetch_bc_cpi_inflation {
        +fetch_bc_cpi_inflation() dict[int, float]
    }

    PITSchedule ..> compute_progressive_tax : used by CentralGovernment
    PITSchedule ..> compute_progressive_tax_quick : optimized path
    PITSchedule ..> fetch_bc_cpi_inflation : loads CPI from StatCan/cache
```

---

## 2. CSV data format — `BC_PIT_2014.csv`

```mermaid
classDiagram
    class BracketsCSV {
        +tax_year: int
        +step: int
        +lower_bound: float
        +marginal_rate: float
        +basic_deduction: float
        +indexing: int
    }
```

| Column | Type | Example | Description |
|--------|------|---------|-------------|
| `tax_year` | int | 2014 | Tax year the bracket applies to |
| `step` | int | 1 | Bracket number (ordered) |
| `lower_bound` | float | 37606 | Lower income bound of bracket |
| `marginal_rate` | float | 0.077 | Marginal tax rate within bracket |
| `basic_deduction` | float | 9869 | Basic personal amount (non-refundable) |
| `indexing` | int | 1 | Whether bracket is CPI-indexed (0 or 1) |

Example brackets for BC 2014:
```
tax_year,step,lower_bound,marginal_rate,basic_deduction,indexing
2014,1,0,0.0506,9869,1
2014,2,37606,0.077,9869,1
2014,3,75213,0.105,9869,1
2014,4,86354,0.1229,9869,1
2014,5,104858,0.147,9869,1
2014,6,150000,0.168,9869,1
```

---

## 3. Activity diagram — `PITSchedule.get_brackets()` for a target year

```mermaid
flowchart TD
    A[Start: get_brackets(tax_year)] --> B{target == base_year?}
    B -->|Yes| C[Return nominal thresholds & rates]
    B -->|No| D["Compute compound inflation:<br/>infl = ∏ (1 + CPI_y)<br/>for y in base_year+1 .. tax_year"]
    D --> E["Inflate thresholds:<br/>threshold = nominal * infl"]
    E --> F["Inflate basic_deduction:<br/>deduction = nominal * infl"]
    F --> G[Return (thresholds, rates, lower_bounds, quick_adds)]
    C --> G
```

---

## 4. `compute_progressive_tax()` algorithm

```mermaid
flowchart TD
    A[Input: incomes, thresholds, rates] --> B[Initialize tax = zeros]
    B --> C[previous = 0]
    C --> D[Loop over brackets]
    D --> E["income_in_bracket =<br/>min(max(incomes - lower_bound, 0),<br/>upper_bound - lower_bound)"]
    E --> F[tax += income_in_bracket * marginal_rate]
    F --> G{More brackets?}
    G -->|Yes| D
    G -->|No| H[Return tax]
```

**Mathematical representation:**

For each individual with taxable income $y$:

$$T(y) = \sum_{b=1}^{B} r_b \cdot \min(\max(y - L_b, 0), U_b - L_b)$$

where:
- $B$ = number of brackets
- $r_b$ = marginal rate for bracket $b$
- $L_b$ = lower bound of bracket $b$
- $U_b$ = upper bound of bracket $b$

After progressive tax calculation, the non-refundable credit is applied:
$$\text{Tax}_{\text{final}} = \max(0, T(y) - D \cdot r_1)$$

where $D$ is the basic deduction and $r_1$ is the lowest marginal rate.

---

## 5. CPI data flow

```mermaid
sequenceDiagram
    participant User as Run simulation (CAN_BC)
    participant PIT as PITSchedule.from_name_with_cpi()
    participant CSV as BC_PIT_2014.csv
    participant CPI as bc_cpi_inflation.csv
    participant StatCan as Statistics Canada API<br/>(table 18-10-0005-01)

    User->>PIT: from_name_with_cpi("BC_PIT_2014.csv")
    PIT->>CSV: Load bracket definitions
    PIT->>CPI: Check for cached CPI
    alt CPI cache exists
        CPI-->>PIT: Return cached rates
    else No cache
        PIT->>StatCan: fetch_bc_cpi_inflation()
        StatCan-->>PIT: CPI rates by year
        PIT->>CPI: Cache to CSV
    end
    PIT-->>User: PITSchedule instance
```

---

## 6. Integration into simulation

```mermaid
flowchart TD
    subgraph Setup["Simulation Setup (run_simulation.py)"]
        A["Is region CAN_BC?"] -->|Yes| B["Load PITSchedule.from_name_with_cpi()"]
        B --> C["Extract brackets & basic_deduction"]
        C --> D["Set CentralGovernmentConfiguration<br/>pit_brackets, pit_basic_deduction"]
        D --> E["Register posthook for<br/>annual CPI indexation"]
    end

    subgraph Runtime["Runtime: Each January"]
        F["posthook fires"] --> G["central_government.step_pit_brackets()"]
        G --> H["Inflate thresholds & deduction<br/>by compound CPI"]
    end

    subgraph TaxCalc["Tax Calculation: Each timestep"]
        I["compute_taxes()"] --> J{"pit_thresholds set?"}
        J -->|Yes| K["compute_progressive_tax() on wages"]
        K --> L["Apply basic_deduction credit"]
        J -->|No| M["Flat Income Tax on all income"]
    end

    Setup --> Runtime
    Runtime --> TaxCalc
```
