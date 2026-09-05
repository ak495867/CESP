# CESP — Usage Guide

This guide walks through running the CESP pipeline end to end: installing
dependencies, triggering a full run, using the API functions programmatically,
tuning parameters, and reading every file the script produces.

---

## 1. Prerequisites

- **Python 3.9+**
- The packages in [`metadata/requirements.txt`](metadata/requirements.txt).

Install them:

```bash
cd cesp_research_code
pip install -r metadata/requirements.txt
```

Verify a quick success:

```bash
python -c "import numpy, pandas, yfinance, matplotlib; print('ok')"
```

---

## 2. Full pipeline run

**Run everything** (download prices → compute CESP state → backtest → write all
artifacts + metadata):

```bash
python code/cesp_research.py
```

What happens:

1. `download()` pulls auto-adjusted daily close prices for the 13-asset universe
   from Yahoo Finance, cleans them, and writes `artifacts/prices.csv`.
2. `run()` builds the CESP strategy and six benchmarks, computes metrics, and
   writes `artifacts/cesp_diagnostics.csv`, `cesp_summary.csv`, and
   `cesp_returns.csv`.
3. `sensitivity()` reruns CESP across a threshold × pressure-span grid and writes
   `artifacts/cesp_sensitivity.csv`.
4. `main()` dumps `artifacts/metadata.json` (asset lists, config, UTC retrieval
   time) and prints the benchmark table to stdout.

Artifacts land in a newly created **`artifacts/`** directory next to `code/`.

Set the config once at the top of the script (`CFG = Config(...)`) to change the
data window or model parameters before running.

---

## 3. Using the API

Every step is exposed as an importable function, so you can embed CESP in your
own notebook or script.

```python
import sys
sys.path.insert(0, "code")
from cesp_research import download, ces_state, run, sensitivity, Config
```

### 3.1 Download prices

```python
close = download()               # uses the module-level CFG
print(close.shape, list(close.columns))
```

`download()` uses `Config.start/end`. It writes `artifacts/prices.csv` and
returns the cleaned close-price DataFrame (index = DatetimeIndex, columns = the
13 tickers).

### 3.2 Compute CESP state only

```python
state = ces_state(close)         # default CFG
state[["entropy", "synchronization", "pressure", "percentile", "defensive_weight"]].tail()
```

Returns a per-date DataFrame with columns:

| Column | Meaning |
|---|---|
| `entropy` | cross-sectional activity entropy `H` |
| `synchronization` | directional sign synchronization `S` |
| `amplitude` | normalized shock amplitude `A` |
| `psi` | raw phase pressure `Ψ` |
| `pressure` | EWMA-smoothed pressure `P` |
| `percentile` | lagged 252-day percentile rank of `P` |
| `defensive_weight` | continuous defensive allocation `w_D` |

### 3.3 Full backtest

```python
diagnostics, summary = run(close)
print(summary.to_string(index=False))
```

`run()` returns two DataFrames and also writes the three CSVs:

- `diagnostics` — state + returns/equity (same as `cesp_diagnostics.csv`)
- `summary` — per-strategy metrics (same as `cesp_summary.csv`)

`run()` also writes `cesp_returns.csv` (aligned daily returns for all
strategies).

### 3.4 Sensitivity sweep

```python
sensitivity(close)               # writes artifacts/cesp_sensitivity.csv
```

Grid: `threshold ∈ {0.60, 0.70, 0.80}` × `pressure_span ∈ {10, 21, 42}`.

---

## 4. Tuning parameters

All tunables live in the `Config` dataclass:

```python
from cesp_research import Config

cfg = Config(
    start="2010-01-01",   # extend history
    threshold=0.75,       # intervene at the 75th pressure percentile
    cost_bps=5.0,         # 5 bps per unit turnover
)
state  = ces_state(close, cfg)
_, summary = run(close, cfg)
```

| Field | Default | Effect |
|---|---|---|
| `start` | `2015-01-02` | data start date |
| `end` | `None` | data end (else tomorrow) |
| `vol_span` | `63` | EWMA span on shocks for `σ̂` |
| `pressure_span` | `21` | EWMA span smoothing `Ψ → P` |
| `percentile_window` | `252` | lookback for the lagged percentile |
| `threshold` | `0.70` | defensive-intervention percentile `q₀` |
| `cost_bps` | `10.0` | transaction cost per unit turnover (bps/10000) |

**Worked example — a tighter intervention with lower costs:**

```python
cfg = Config(threshold=0.65, cost_bps=5.0)
close = download()
diag, summary = run(close, cfg)
print(summary.loc[summary.strategy == "CESP"])
```

> Note: `download()` reads the module-level `CFG`, not an argument. To combine a
> custom window with custom model parameters, edit `CFG` (or pass a pre-cleaned
> `close` DataFrame into `ces_state`/`run` and set `end` yourself).

---

## 5. Benchmark strategies

The backtest compares CESP against six benchmarks (all defined in `run()`):

- **Risk equal-weight** — mean of the 9 risk-basket returns.
- **Defensive equal-weight** — mean of the 4 defensive-basket returns.
- **60_40** — static 60% risk / 40% defensive.
- **SMA200 mix** — risk exposure until `SPY` crosses below its 200-day moving
  average, then defensive (cost deducted on switches).
- **Vol-targeted mix** — risk scaled toward a 10% annualized vol target (clamped
  to [5%, 40%]), remainder in defensive (no cost for the daily rebalance).
- **Random exposure placebo** — the **same mean defensive exposure** as CESP but
  with randomly *timed* switches (seeded), to test whether CESP’s edge comes from
  *when* it rotates, not just *how much*.

---

## 6. Reading the output files

All files are written as CSV (or LaTeX/JSON) and mirror a single pipeline stage.

### `prices.csv`
One row per date, one column per ticker — the cleaned adjusted-close matrix the
model consumes.

### `cesp_diagnostics.csv`
The richest file. One row per date:
- all CESP state variables (`entropy`, `synchronization`, `amplitude`, `psi`,
  `pressure`, `percentile`, `defensive_weight`, `weight`);
- daily returns for `risk_return`, `defensive_return`, `cesp_return`;
- cumulative equity for `cesp_equity`, `risk_equity`, `defensive_equity`;
- a `date` string column.

Good for plotting the phase state, the defensive weight, and drawdowns over
time.

```python
import pandas as pd
diag = pd.read_csv("artifacts/cesp_diagnostics.csv", index_col="Date")
diag["defensive_weight"].plot()   # or chart pressure, entropy, equity, ...
```

### `cesp_summary.csv` / `cesp_summary.tex`
One row per strategy. Columns: `strategy`, `cagr`, `volatility`, `sharpe`,
`max_drawdown`, `calmar`, `observations`, and CESP-only `defensive_exposure`,
`turnover`. The `.tex` is the paper-formatted LaTeX table.

### `cesp_returns.csv`
Aligned daily returns for every strategy (columns = strategy names). Use this
for correlation, drawdown, or any cross-strategy analysis.

### `cesp_sensitivity.csv`
CESP metrics for each `(threshold, pressure_span)` combo. Columns repeat the
summary metrics plus `threshold` and `pressure_span`. Lets you verify robustness
of the headline numbers.

### `metadata.json`
`risk_assets`, `defensive_assets`, the exact `config` used, and the UTC time
prices were retrieved. This stamps *what* and *when* the archived sample was
built.

---

## 7. Example: a minimal custom analysis

```python
import pandas as pd
import matplotlib.pyplot as plt
import sys
sys.path.insert(0, "code")
from cesp_research import download, run

close = download()
diag, summary = run(close)

# CESP vs risk bucket on Sharpe
print(summary[["strategy", "sharpe", "max_drawdown"]])

# Defensive weight over time
plt.figure(figsize=(12, 3))
plt.plot(diag.index, diag["defensive_weight"], label="w_D", linewidth=1)
plt.title("CESP defensive allocation")
plt.legend(); plt.show()
```

---

## 8. Reproducing the paper

The paper (`paper/cesp_research_paper.pdf`, LaTeX source alongside) is compiled
from the archived `data/` + `figures/` artifacts.

1. Regenerate artifacts: `python code/cesp_research.py`
2. Rebuild the docs/figures (see `logs/latex_compile.log` for the exact build
   trail).
3. Verify artifact integrity against `metadata/SHA256SUMS.txt`.

Because prices are pulled live, a fresh run reproduces the analysis *structure*
with today’s data rather than byte-identical archived numbers; the archived
retrieval stamp is in `metadata/metadata.json`.

---

## 9. Troubleshooting

| Symptom | Likely cause / fix |
|---|---|
| `yfinance` download returns mostly NaN / empty | Network or Yahoo rate-limiting (rare with `threads=False`). Re-run, or use a cached `prices.csv` by skipping `download()` and reading `data/prices.csv` instead. |
| ImportError on `yfinance` | `pip install -r metadata/requirements.txt`. |
| Different numbers than the archive | Expected: live data → live numbers. Compare *relative* performance, not exact digits. |
| "no modules named..." | Make sure you run from the repo root (`cd cesp_research_code`), or add `code/` to `sys.path` when importing directly. |