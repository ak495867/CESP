# CESP — Collective Entropy–Synchronization Phase Model

[![Paper](https://img.shields.io/badge/Paper-PDF-8A2BE2?style=for-the-badge&logo=readdotcv&logoColor=white)](https://github.com/ak495867/CESP/blob/main/paper/CESP.pdf)
[![Release](https://img.shields.io/github/v/release/ak495867/CESP?style=for-the-badge)](https://github.com/ak495867/CESP/releases)
[![License](https://img.shields.io/github/license/ak495867/CESP?style=for-the-badge)](https://github.com/ak495867/CESP/blob/main/LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/ak495867/CESP?style=for-the-badge)](https://github.com/ak495867/CESP/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/ak495867/CESP?style=for-the-badge)](https://github.com/ak495867/CESP/network/members)
[![GitHub issues](https://img.shields.io/github/issues/ak495867/CESP?style=for-the-badge)](https://github.com/ak495867/CESP/issues)
[![GitHub last commit](https://img.shields.io/github/last-commit/ak495867/CESP?style=for-the-badge)](https://github.com/ak495867/CESP/commits/main)
[![GitHub repo size](https://img.shields.io/github/repo-size/ak495867/CESP?style=for-the-badge)](https://github.com/ak495867/CESP)
[![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![NumPy](https://img.shields.io/badge/NumPy-013243?style=for-the-badge&logo=numpy&logoColor=white)](https://numpy.org/)
[![Pandas](https://img.shields.io/badge/Pandas-150458?style=for-the-badge&logo=pandas&logoColor=white)](https://pandas.pydata.org/)
[![Matplotlib](https://img.shields.io/badge/Matplotlib-11557C?style=for-the-badge&logo=python&logoColor=white)](https://matplotlib.org/)
[![yfinance](https://img.shields.io/badge/yfinance-0B0B0B?style=for-the-badge)](https://github.com/ranaroussi/yfinance)

**CESP** is an independent econophysics framework for cross-asset portfolio risk allocation. It treats a market as a population of interacting assets and represents its state through two *collective* observables — the entropy of cross-sectional normalized-return activity and the synchronization of return signs. A single phase-pressure statistic rises when activity is concentrated, directional movement is aligned, and normalized shock amplitude is large, and a continuous defensive allocation is read off its lagged historical percentile.

The construction relies purely on collective, cross-sectional observables. It makes no use of pairwise asset fields, covariance matrices, regressions, or signed-mass analogies.

This repository is the self-contained companion to the research paper [`paper/CESP.pdf`](paper/CESP.pdf), with the full derivations and proofs in [`MATH.md`](MATH.md). It ships a single script that downloads the data, fits nothing (the model is parameterized up front, with no fitting on the sample), runs the backtest, and reproduces every table and figure.

> **Honest scope statement.** Over the realized sample, CESP reduces risk-basket drawdown relative to risky buy-and-hold and beats the random-exposure placebo on Sharpe ratio, but it does not dominate the strongest diversified or volatility-targeted benchmark and does **not** claim universal alpha. It is a transparent and falsifiable hypothesis about collective market phase, not a validated trading strategy or investment advice.

---

## Highlights

- **One file, end to end.** `code/cesp_research.py` downloads prices, computes the CESP state, runs a cost-aware backtest against six benchmarks, and writes all diagnostics, summary, returns, and sensitivity tables plus a `metadata.json`.
- **Collective-state, not pairwise.** Entropy $H$, synchronization $S$, and amplitude $A$ are pooled across the whole cross-section on each date.
- **Continuous allocation.** The defensive weight $w_D$ moves continuously between 0 and 1 based on the lagged 252-day percentile of smoothed pressure — no hard regime switch.
- **Falsifiable by design.** CESP is benchmarked against equal-weighted risk and defensive baskets, a static 60/40, a 200-day moving-average mix, volatility targeting, and a random-exposure placebo — all with transaction costs applied.
- **Fully reproducible.** Default parameters and the asset universe are pinned in `Config`; the price sample and all artifacts are archived alongside the code.

---

## Model in brief

Let $i = 1, \dots, N$ index assets and $t$ index trading dates. On each date:

**1. Volatility-normalized activity**

$$
z_{i,t} = \frac{r_{i,t}}{\hat\sigma_{i,t-1} + \varepsilon}
$$

where $\hat\sigma_{i,t-1}$ is an exponentially weighted (63-day) standard deviation known the day before.

**2. Cross-sectional activity entropy**

$$
H_t = -\frac{1}{\log N}\sum_{i=1}^{N} p_{i,t}\log p_{i,t}, \qquad p_{i,t} = \frac{|z_{i,t}|}{\sum_{j=1}^N |z_{j,t}|}
$$

High $H_t$ means activity is spread evenly across assets; low $H_t$ means it is concentrated in a few.

**3. Directional synchronization**

$$
S_t = \frac{2}{N(N-1)}\sum_{i<j}\operatorname{sign}(z_{i,t})\,\operatorname{sign}(z_{j,t})
$$

$S_t$ is the degree of pairwise sign agreement across the cross-section. CESP keeps only its positive part, $\max(S_t, 0)$ — ordered rallies and ordered selloffs are both treated as ordered states.

**4. Shock amplitude**

$$
A_t = \left(\frac{1}{N}\sum_{i=1}^N z_{i,t}^2\right)^{1/2}
$$

**5. Phase pressure**

$$
\Psi_t = (1 - H_t)\,\max(S_t, 0)\,A_t, \qquad P_t = \operatorname{EWMA}_{21}(\Psi_t)
$$

**6. Defensive weight**

$$
w_{D,t} = \min\!\left(1,\ \max\!\left(0,\ \frac{Q_t - q_0}{1 - q_0}\right)\right)
$$

where $Q_t$ is the lagged percentile rank of $P_t$ over the trailing 252 days and $q_0 = 0.70$ is the intervention threshold.

**Portfolio return**

$$
R^{\text{CESP}}_t = (1 - w_{D,t-1})\,R^R_t + w_{D,t-1}\,R^D_t - c\,\lvert w_{D,t-1} - w_{D,t-2}\rvert
$$

with $R^R_t$, $R^D_t$ the risky- and defensive-basket returns and $c = 10\text{bps}$ the per-unit-turnover cost. The one-day lag on $w_D$ prevents same-close look-ahead.

The notation follows the paper. The paper additionally writes a cross-sectional sign order parameter $m_t = \frac{1}{N}\sum_i \tanh(\beta z_{i,t})$ for interpretability; the code implements the pairwise sign statistic $S_t$ directly in `ces_state`.

For the full formal treatment — entropy bounds, the range of $S_t$, and proofs that phase pressure and the allocation rule are monotonic in their inputs — see [`MATH.md`](MATH.md).

---

## Asset universe

| Risk basket | Defensive basket |
|---|---|
| `SPY` — US large-cap | `TLT` — long Treasuries |
| `QQQ` — US tech | `IEF` — 7–10yr Treasuries |
| `IWM` — US small-cap | `GLD` — gold |
| `EFA` — international equity | `UUP` — US dollar index |
| `VNQ` — US real estate | |
| `XLE` — energy | |
| `DBC` — commodities | |
| `BTC-USD` — crypto | |
| `ETH-USD` — crypto | |

---

## Repository layout

```
cesp_research_code/
├── code/
│   └── cesp_research.py      # entire pipeline: download → state → backtest → artifacts
├── data/                     # generated artifacts (prices + all result tables)
│   ├── prices.csv            #   downloaded/cleaned adjusted close prices
│   ├── cesp_diagnostics.csv  #   per-date CESP state + strategy returns/equity
│   ├── cesp_summary.csv      #   headline backtest metrics per strategy
│   ├── cesp_summary_compact.csv
│   ├── cesp_returns.csv      #   aligned daily returns for every strategy
│   └── cesp_sensitivity.csv  #   CESP metrics across threshold × pressure-span grid
├── tables/
│   └── cesp_summary.tex      # LaTeX summary table (used in the paper)
├── figures/
│   ├── cesp_equity.png       #   equity curves
│   ├── cesp_sharpe.png       #   Sharpe ratios
│   ├── cesp_phase_space.png  #   phase-space map
│   └── cesp_phase_state.png  #   phase-state time series
├── paper/
│   ├── CESP.tex
│   └── CESP.pdf
├── MATH.md                   # full formal derivations and proofs
├── metadata/
│   ├── metadata.json         #   asset lists, config, UTC retrieval stamp
│   ├── requirements.txt
│   └── SHA256SUMS.txt        #   checksums of the shipped artifacts
└── logs/                     # runtime logs for each pipeline stage
```

> **Note:** running the script locally writes a fresh `artifacts/` directory next to `code/`. The checked-in `data/`, `tables/`, `figures/`, and `metadata/` folders hold the **archived output of the committed sample**, so the paper remains reproducible even without re-downloading live prices.

---

## Requirements

- Python 3.9+ (`from __future__ import annotations` is used)
- A pure scientific stack — no model-training frameworks required

| Package | Used for |
|---|---|
| `numpy` | vectorized collective-statistic math |
| `pandas` | time-series handling, rolling/EWMA/rank |
| `yfinance` | daily adjusted close price download |
| `matplotlib` | figure generation |

Install with:

```bash
pip install -r metadata/requirements.txt
```

---

## Quick start

```bash
git clone https://github.com/ak495867/CESP
cd CESP
python code/cesp_research.py
```

A fresh `artifacts/` directory is created next to `code/`, containing `prices.csv`, `cesp_diagnostics.csv`, `cesp_summary.csv`, `cesp_returns.csv`, `cesp_sensitivity.csv`, and `metadata.json`. The benchmark table is printed to stdout.

> **Live data note:** prices are pulled from Yahoo Finance at run time, so repeating the script today will reproduce the *structure* of the analysis but not the byte-identical numbers of the archived sample. The last archived retrieval timestamp is recorded in `metadata/metadata.json`.

---

## How it works

All logic lives in `code/cesp_research.py` as small, pure functions:

| Function | Role |
|---|---|
| `download()` | Pulls auto-adjusted daily close prices, aligns to the universe, forward-fills then drops all-NaN rows, and caches to `prices.csv` |
| `ces_state(close, cfg)` | Core routine — returns a DataFrame of per-date `entropy`, `synchronization`, `amplitude`, `psi`, `pressure`, `percentile` (lagged rank), and `defensive_weight` |
| `metrics(ret, name)` | CAGR, annualized vol, Sharpe, max drawdown, Calmar, and observation count for one return series |
| `run(close, cfg)` | Builds the CESP strategy plus the six benchmarks, computes metrics, and writes the diagnostics/summary/returns tables |
| `sensitivity(close)` | Reruns `run` across $\text{threshold} \in \{0.6, 0.7, 0.8\}$ × $\text{pressure\_span} \in \{10, 21, 42\}$ and writes `cesp_sensitivity.csv` |
| `main()` | Orchestrates download → run → sensitivity → metadata, and prints the summary |

### Benchmarks

| Label | Construction |
|---|---|
| `CESP` | $(1 - w_D)\cdot\text{risk} + w_D\cdot\text{defensive} - \text{turnover}\cdot\text{cost}$ |
| Risk equal-weight | Mean of risk-basket returns |
| Defensive equal-weight | Mean of defensive-basket returns |
| `60_40` | Static 60% risk / 40% defensive |
| SMA200 mix | Risk until SPY breaches its 200-day SMA, then defensive |
| Vol-targeted mix | Risk scaled toward 10% target vol, remainder defensive |
| Random exposure placebo | Same average defensive exposure as CESP, but random timing |

Transaction costs default to **10 bps** per unit of turnover (`cost_bps`).

---

## Configuration

`Config` is a dataclass holding every tunable parameter.

| Field | Default | Meaning |
|---|---|---|
| `start` | `2015-01-02` | Data start |
| `end` | `None` | Data end (today + 1 otherwise) |
| `vol_span` | `63` | EWMA span on sector shocks for $\hat\sigma$ (≈ 1 quarter) |
| `pressure_span` | `21` | EWMA span smoothing $\Psi$ into $P$ (≈ 1 month) |
| `percentile_window` | `252` | Lookback for the lagged pressure percentile |
| `threshold` | `0.70` | Intervention percentile $q_0$ |
| `cost_bps` | `10.0` | Per-unit-turnover transaction cost |

To run with different parameters, pass a custom `Config` into `ces_state` / `run`; see `sensitivity()` for the canonical grid pattern.

---

## Reading the output

- **`cesp_diagnostics.csv`** — one row per date: every CESP state variable plus the risk/defensive/CESP returns and equity curves and the live defensive weight. This is the file to chart.
- **`cesp_summary.csv` / `.tex`** — one row per strategy: `cagr`, `volatility`, `sharpe`, `max_drawdown`, `calmar`, plus CESP-only `defensive_exposure` (mean weight) and `turnover`. This is the headline table.
- **`cesp_returns.csv`** — aligned daily returns for all strategies, for downstream analysis or plotting.
- **`cesp_sensitivity.csv`** — CESP diagnostics across the threshold × pressure-span grid; use it to check how sensitive results are to the two behavior-shaping parameters.

Representative headline metrics (archived sample):

| Strategy | CAGR | Sharpe | Max DD | Calmar |
|---|---|---|---|---|
| CESP | 0.146 | 0.973 | −0.359 | 0.406 |
| Vol-targeted mix | 0.108 | 1.018 | −0.221 | 0.491 |
| 60/40 | 0.101 | 0.930 | −0.251 | 0.402 |
| Risk equal-weight | 0.144 | 0.840 | −0.396 | 0.364 |
| Random placebo | 0.146 | 0.881 | −0.365 | 0.400 |

Full numbers live in `tables/cesp_summary.tex`.

---

## Reproducing the paper

The paper at `paper/CESP.pdf` (LaTeX source alongside) is built from the same `data/` and `figures/` artifacts. To regenerate:

1. Run the script to produce fresh artifacts.
2. Compile the `.tex` file — a `booktabs`, `graphicx`, `natbib` stack. See `logs/latex_compile.log` for the build trail.

`metadata/SHA256SUMS.txt` pins the integrity of the shipped artifacts.

---

## License

Research project by **Akhilesh Varma** ([github.com/ak495867/CESP](https://github.com/ak495867/CESP)).
See the paper for full attribution.

Financial content is provided for research and educational purposes only and does not constitute investment advice.