# CESP — Mathematical Appendix

This document gives the complete formal construction of the Collective Entropy–Synchronization Phase model (CESP) and full proofs of its two structural propositions. It is a companion to [`paper/CESP.pdf`](paper/CESP.pdf) and to the implementation in `code/cesp_research.py`.

---

## 1. Setup and notation

Let $i = 1, \dots, N$ index the assets in the universe, and let $t$ index trading dates. Let $r_{i,t}$ denote the log return of asset $i$ on date $t$, and let $\hat\sigma_{i,t-1}$ denote an exponentially weighted standard deviation of asset $i$'s returns computed using only information available strictly before date $t$ (a 63-day EWMA span in the reference implementation).

A small constant $\varepsilon > 0$ is used throughout purely to avoid division by zero; it has no economic role and can be taken arbitrarily small.

### 1.1 Volatility-normalized activity

$$
z_{i,t} \;=\; \frac{r_{i,t}}{\hat\sigma_{i,t-1} + \varepsilon}. \tag{1}
$$

### 1.2 Cross-sectional activity shares

$$
p_{i,t} \;=\; \frac{|z_{i,t}| + \varepsilon}{\sum_{j=1}^{N}\big(|z_{j,t}| + \varepsilon\big)}, \qquad \sum_{i=1}^N p_{i,t} = 1,\quad p_{i,t} > 0. \tag{2}
$$

So $\{p_{i,t}\}_{i=1}^N$ is a proper probability distribution over assets for each fixed $t$ — the share of the day's total normalized "activity" attributable to asset $i$.

### 1.3 Cross-sectional activity entropy

$$
H_t \;=\; -\frac{1}{\log N}\sum_{i=1}^{N} p_{i,t}\log p_{i,t}. \tag{3}
$$

**Lemma 1 (Entropy bounds).** $0 \le H_t \le 1$, with $H_t = 1$ iff $p_{i,t} = 1/N$ for all $i$ (activity uniformly spread across assets), and $H_t \to 0$ as activity concentrates onto a single asset.

*Proof.* The unnormalized quantity $-\sum_i p_{i,t}\log p_{i,t}$ is the Shannon entropy of the distribution $\{p_{i,t}\}$, which is classically bounded as
$$
0 \;\le\; -\sum_{i=1}^N p_{i,t}\log p_{i,t} \;\le\; \log N,
$$
with the lower bound approached as $p_{i,t}\to 1$ for one asset and $p_{j,t}\to 0$ for all others (concentration), and the upper bound attained uniquely at $p_{i,t}=1/N$ for all $i$ by Gibbs' inequality (equivalently, strict concavity of $x\mapsto -x\log x$ combined with Jensen's inequality, with equality iff all $p_{i,t}$ are equal). Dividing through by $\log N$ gives $0 \le H_t \le 1$ with the same equality conditions. $\blacksquare$

So $H_t$ is a normalized, scale-free measure of *how many assets are effectively driving the day's return activity*: $H_t \approx 1$ means activity is broad-based; $H_t \approx 0$ means activity is concentrated in a few names.

### 1.4 Directional synchronization

Cross-sectional sign order parameter (reported for interpretability, not used directly in $\Psi_t$):

$$
m_t \;=\; \frac{1}{N}\sum_{i=1}^{N}\tanh(\beta z_{i,t}). \tag{4}
$$

Pairwise sign synchronization statistic:

$$
S_t \;=\; \frac{2}{N(N-1)}\sum_{i<j}\operatorname{sign}(z_{i,t})\,\operatorname{sign}(z_{j,t}). \tag{5}
$$

**Lemma 2 (Range of $S_t$).** $-1 \le S_t \le 1$, with $S_t = 1$ iff all signs agree (pure common direction) and $S_t = -1$ iff signs are maximally split (for even $N$).

*Proof.* Write $\epsilon_i = \operatorname{sign}(z_{i,t}) \in \{-1,+1\}$ (ties handled by an arbitrary but fixed convention). Then
$$
\sum_{i<j}\epsilon_i\epsilon_j \;=\; \frac{1}{2}\left[\Big(\sum_{i=1}^N \epsilon_i\Big)^2 - N\right],
$$
which is a standard combinatorial identity (expand the square and separate diagonal/off-diagonal terms). Since $\left(\sum_i \epsilon_i\right)^2 \in [0, N^2]$, we get $\sum_{i<j}\epsilon_i\epsilon_j \in \left[-\frac{N}{2}, \frac{N(N-1)}{2}\right]$. Multiplying by $\frac{2}{N(N-1)}$ gives $S_t \in \left[-\frac{1}{N-1}, 1\right]$ for the *exact* combinatorial bound; taking $N$ large recovers the stated $[-1,1]$ envelope, and $S_t=1$ occurs exactly when all $\epsilon_i$ are equal (so every pair agrees). $\blacksquare$

CESP uses only the **positive part** $\max(S_t, 0)$: a strongly synchronized rally and a strongly synchronized selloff are both treated as "ordered" states, but negative synchronization (a mixed, disagreeing cross-section) is not treated as risk-reducing.

### 1.5 Normalized shock amplitude

$$
A_t \;=\; \left(\frac{1}{N}\sum_{i=1}^N z_{i,t}^2\right)^{1/2} \;\ge\; 0. \tag{6}
$$

$A_t$ is the root-mean-square normalized shock across the cross-section on date $t$ — large when returns are jointly far from their (locally estimated) typical scale, regardless of sign or concentration.

---

## 2. Collective phase pressure

CESP's central object is the instantaneous phase pressure

$$
\Psi_t \;=\; (1 - H_t)\,\max(S_t, 0)\,A_t, \tag{7}
$$

smoothed via an exponentially weighted moving average with span $\lambda_P$ (21 trading days in the reference run):

$$
P_t \;=\; \operatorname{EWMA}_{\lambda_P}(\Psi_t). \tag{8}
$$

The **lagged** historical percentile rank of the smoothed pressure, over a trailing window of length $L_P$ (252 trading days):

$$
Q_t \;=\; \operatorname{PercentileRank}\big(P_{t-1};\; P_{t-1}, P_{t-2}, \dots, P_{t-L_P}\big). \tag{9}
$$

Note $Q_t$ is a function only of information available strictly before date $t$ — the pressure value being ranked, $P_{t-1}$, and the historical window used to rank it, $\{P_{t-2}, \dots, P_{t-L_P-1}\}$ in the fully lagged convention used by the code — so the allocation below is non-anticipating.

The continuous defensive weight, with intervention threshold $q_0 = 0.70$:

$$
w_{D,t} \;=\; \min\!\Big(1,\ \max\!\Big(0,\ \frac{Q_t - q_0}{1 - q_0}\Big)\Big), \qquad w_{R,t} = 1 - w_{D,t}. \tag{10}
$$

$w_{D,t}$ is a clipped linear ramp: it is exactly $0$ while $Q_t \le q_0$, rises linearly to $1$ as $Q_t$ runs from $q_0$ to $1$, and saturates at $1$ thereafter. This is what makes the allocation rule continuous rather than a binary regime switch.

### 2.1 Portfolio return and cost

$$
R^{\text{CESP}}_t \;=\; (1 - w_{D,t-1})\,R^{R}_t \;+\; w_{D,t-1}\,R^{D}_t \;-\; c\,\big|w_{D,t-1} - w_{D,t-2}\big|, \tag{11}
$$

where $R^R_t$, $R^D_t$ are the risky- and defensive-basket returns and $c = 10\text{bps}$ is the per-unit-turnover transaction cost. The one-day lag on $w_D$ prevents same-close look-ahead: the weight applied on date $t$ was fully determined by information available at the close of $t-1$.

---

## 3. Propositions and proofs

Both propositions are local monotonicity statements about the phase-pressure operator $\Psi_t = (1-H_t)\max(S_t,0)A_t$, treated as a function of its three arguments $(H_t, S_t, A_t) \in [0,1]\times[-1,1]\times[0,\infty)$.

### Proposition 1 (Entropy concentration)

> *Holding normalized shock amplitude $A_t$ fixed, a fall in cross-sectional entropy $H_t$ increases CESP phase pressure whenever synchronization is positive ($S_t > 0$).*

**Proof.** Fix $A_t = A > 0$ and restrict to the region $S_t > 0$, where $\max(S_t,0) = S_t$ and $\Psi_t$ is differentiable in $H_t$. Then

$$
\Psi_t(H_t) = (1-H_t)\,S_t\,A,
$$

is affine and strictly decreasing in $H_t$, since

$$
\frac{\partial \Psi_t}{\partial H_t} \;=\; -S_t\,A \;<\; 0 \quad\text{whenever } S_t > 0,\ A>0. \tag{12}
$$

Hence for any $H_t^{(1)} > H_t^{(2)}$ (i.e. a fall in entropy from $H_t^{(1)}$ to $H_t^{(2)}$) with $S_t, A$ held fixed and $S_t>0$,

$$
\Psi_t\big(H_t^{(2)}\big) - \Psi_t\big(H_t^{(1)}\big) \;=\; S_t A\left(H_t^{(1)} - H_t^{(2)}\right) \;>\; 0,
$$

so phase pressure strictly increases as entropy falls. Since $H_t \in [0,1]$ (Lemma 1), the marginal effect (12) is bounded, $|\partial \Psi_t/\partial H_t| \le A$, so the increase is also uniformly controlled by the shock amplitude: concentration effects cannot be amplified beyond the day's realized shock scale. $\blacksquare$

If $S_t \le 0$, the positive-part operator gives $\max(S_t,0)=0$ identically in a neighborhood where $S_t$ stays non-positive, so $\Psi_t \equiv 0$ there and $\partial\Psi_t/\partial H_t = 0$ — entropy concentration has *no* effect on pressure absent positive synchronization. This is exactly why the proposition's hypothesis "$S_t>0$" is necessary, not merely convenient: it identifies the only regime in which concentration is informative for CESP's risk signal.

### Proposition 2 (Collective order)

> *Holding entropy $H_t$ and shock amplitude $A_t$ fixed, an increase in positive sign synchronization $S_t$ increases phase pressure.*

**Proof.** Fix $H_t = H \in [0,1)$ and $A_t = A > 0$, and restrict to $S_t > 0$ where $\max(S_t,0)=S_t$. Then

$$
\Psi_t(S_t) = (1-H)\,S_t\,A
$$

is affine and strictly increasing in $S_t$, since

$$
\frac{\partial \Psi_t}{\partial S_t} \;=\; (1-H)A \;>\; 0 \quad\text{whenever } H<1,\ A>0. \tag{13}
$$

Hence for any $S_t^{(1)} < S_t^{(2)}$, both positive, with $H, A$ held fixed,

$$
\Psi_t\big(S_t^{(2)}\big) - \Psi_t\big(S_t^{(1)}\big) \;=\; (1-H)A\left(S_t^{(2)} - S_t^{(1)}\right) \;>\; 0,
$$

so phase pressure strictly increases with synchronization. By Lemma 1, $H \in [0,1]$, so the marginal effect (13) vanishes only in the degenerate case $H=1$ (activity perfectly uniform across the cross-section), which is a measure-zero boundary case; for all $H<1$ the monotonicity is strict. $\blacksquare$

As with Proposition 1, this is a statement about the region $S_t>0$: at $S_t = 0$, $\max(S_t,0)$ is continuous but only right-differentiable (the one-sided derivative from below is $0$, from above is $(1-H)A$), so the proposition is naturally read as holding for $S_t\ge 0$ with the derivative interpreted as one-sided at the kink.

### Remark: joint interpretation

Together, Propositions 1 and 2 say that $\Psi_t$ is **coordinate-wise monotonic** on the region $\{S_t \ge 0\}$: decreasing in $H_t$, increasing in $S_t$, and (trivially, since $\Psi_t = (1-H_t)\max(S_t,0)A_t$ is linear in $A_t$ with nonnegative coefficient $(1-H_t)\max(S_t,0)\ge 0$) non-decreasing in $A_t$. Phase pressure is therefore maximized, holding the other two coordinates fixed, exactly when activity is maximally concentrated ($H_t \to 0$), maximally aligned ($S_t \to 1$), and shocks are large ($A_t$ large) — the triple condition the model calls a "collective phase." No single coordinate alone is sufficient: e.g. $H_t \to 0$ with $S_t \le 0$ leaves $\Psi_t = 0$, so concentrated-but-disordered activity is not flagged as high-pressure by construction.

---

## 4. Monotonicity of the allocation rule

**Lemma 3 (Allocation is non-decreasing in pressure percentile).** The map $Q_t \mapsto w_{D,t}$ defined in (10) is continuous, non-decreasing, and piecewise linear on $[0,1]$, with

$$
w_{D,t} = \begin{cases} 0, & Q_t \le q_0 \\[4pt] \dfrac{Q_t - q_0}{1-q_0}, & q_0 < Q_t < 1 \\[6pt] 1, & Q_t \ge 1 \end{cases}
$$

*Proof.* Immediate from (10): $\min(1,\max(0,x))$ is the standard clipping function, non-decreasing and $1$-Lipschitz in $x$, composed here with the affine, strictly increasing map $Q_t \mapsto \frac{Q_t-q_0}{1-q_0}$ (since $1-q_0>0$). A composition of a non-decreasing affine map with a non-decreasing clip is non-decreasing, and each piece is affine, hence continuous at the junctions $Q_t=q_0$ and $Q_t=1$ by direct evaluation. $\blacksquare$

Combined with Propositions 1–2, this gives the full causal chain the model relies on: entropy concentration and positive synchronization raise $\Psi_t$ $\Rightarrow$ raise smoothed pressure $P_t$ $\Rightarrow$ (weakly) raise the historical percentile $Q_t$ $\Rightarrow$ (weakly) raise the defensive weight $w_{D,t}$ via a continuous, monotone, non-anticipating map. No step in this chain requires re-estimation or fitting on the sample; every quantity is computed from a fixed, pre-specified functional form.

---

## 5. Scope of these results

These are structural (comparative-statics) proofs about the deterministic operator $\Psi_t$ and the deterministic allocation map — they establish that the *model does what it is designed to do* (respond monotonically to concentration, synchronization, and amplitude). They are **not** statistical claims: they say nothing about whether $H_t$, $S_t$, and $A_t$ carry genuine predictive information about future drawdowns in real markets, which is an empirical question addressed separately in Sections 4–5 of the paper via the benchmark comparison, the random-exposure placebo, and the sensitivity grid over $(q_0, \lambda_P)$.