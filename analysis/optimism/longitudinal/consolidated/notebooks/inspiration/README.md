# Optimism Grant Analysis Notebooks - Complete Guide

This directory contains 6 Marimo notebooks for analyzing the impact and ROI of grants, incentives, and infrastructure investments on Optimism and the Superchain. This guide provides a comprehensive overview of what each notebook does, what makes it unique, and how to use it.

---

## Table of Contents

1. [Chainlink ROI Analysis](#1-chainlink-roi-analysis)
2. [Rainbow Wallet ROI Analysis](#2-rainbow-wallet-roi-analysis)
3. [S7 TVL Grant Impact Analysis](#3-s7-tvl-grant-impact-analysis)
4. [S8 TVL Grant Impact Analysis](#4-s8-tvl-grant-impact-analysis)
5. [Synthetic Control Framework](#5-synthetic-control-framework)
6. [TVL Grant ROI Analysis (Portfolio-Level)](#6-tvl-grant-roi-analysis-portfolio-level)
7. [Comparative Overview](#comparative-overview)

---

## 1. Chainlink ROI Analysis

**File**: `chainlink-roi-analysis.py`

### Overview
Measures Chainlink's impact and value contribution to OP Mainnet by analyzing oracle usage patterns, revenue generation, and the downstream DeFi ecosystem that depends on Chainlink's infrastructure.

### What It Analyzes

#### Core Metrics
- **Market Share**: Chainlink's dominance vs. Pyth (the main alternative oracle) in terms of transaction volume
- **Direct Revenue**: L2 gas fees from oracle read operations
- **Indirect Revenue**: Total fees from DeFi applications and trading bots that use Chainlink
- **DeFi Ecosystem**: TVL and activity from applications dependent on Chainlink oracles

#### Key Findings Structure
1. Market share percentage (Chainlink vs Pyth on OP Mainnet)
2. Direct revenue contribution in ETH over past year and all-time
3. TVL and revenue from DeFi apps using Chainlink
4. Additional revenue from trading/arbitrage bots
5. Overall revenue impact range (lower and upper bound estimates)

### Data Sources
- **Superchain Data** (via Goldsky): Raw transaction and trace data
- **DefiLlama**: TVL data for DeFi protocols
- **Chainlink DevHub**: Oracle contract addresses on OP Mainnet
- **OSS Directory**: Project and address registry
- **OSO API**: Data and metrics pipeline

### Methodology

#### Direct Impact Measurement
1. **Contract Labeling**: Comprehensive mapping of Chainlink oracle contracts (price feeds, CCIP, aggregators) and Pyth contracts
2. **Trace Analysis**: Identifies read operations (static calls) to oracle contracts within transaction traces
3. **Fee Calculation**: Attributes gas fees to oracle read operations using the formula:
   ```
   GAS_READ_OPERATION = (gas_used_trace × gas_price_tx) / 10^18
   ```

#### Indirect Impact Measurement
1. **Application Identification**: Links transactions to DeFi applications (DEXs, perps platforms) using top-level transaction addresses
2. **TVL Attribution**: Identifies apps with >$1M TVL and >90% Chainlink share
3. **Revenue Aggregation**: Calculates total L2 fees from Chainlink-dependent applications

#### Impact Range Estimation
- **Lower Bound**: Direct revenue from Chainlink read operations only
- **Upper Bound**: Combined revenue from DeFi apps + trading/arb bots that use Chainlink

### What Makes It Unique

1. **Multi-Layer Attribution**: Goes beyond direct oracle calls to measure the full ecosystem impact, including downstream DeFi applications and trading bots

2. **Market Share Analysis**: Provides competitive context by comparing Chainlink's usage against Pyth, the primary alternative

3. **Granular Trace Analysis**: Uses transaction trace data to precisely attribute gas costs to oracle read operations, not just top-level transaction fees

4. **Conservative Methodology**: Presents both lower-bound (direct only) and upper-bound (ecosystem-wide) estimates with clear assumptions

5. **Application Profiling**: Identifies which specific DeFi protocols are most dependent on Chainlink, including Synthetix, Uniswap, and Velodrome

### Key Insights

The analysis reveals that:
- Chainlink has maintained dominant market share (vs Pyth) since OP Mainnet launch
- Direct oracle revenue represents a small percentage of total OP Mainnet revenue
- The indirect impact through DeFi applications is substantially larger than direct oracle usage
- Perps platforms and DEXs are the heaviest users of oracle data
- Unknown addresses (likely arbitrage bots) contribute significant additional revenue

### Use Cases
- **Infrastructure ROI**: Measuring the value of oracle infrastructure investments
- **Grant Evaluation**: Assessing the return on foundation/ecosystem grants to oracle providers
- **Ecosystem Analysis**: Understanding dependencies between infrastructure and applications
- **Competitive Benchmarking**: Comparing different oracle solutions

---

## 2. Rainbow Wallet ROI Analysis

**File**: `rainbow-wallet-roi-analysis.py`

### Overview
Evaluates the impact of OP token incentives distributed to Rainbow Wallet users, measuring user acquisition, lifetime value (LTV), retention patterns, and overall return on investment for the grant program.

### What It Analyzes

#### Grant Program Details
- **Agreement**: Gov Fund Phase 1 proposal for Rainbow
- **Success Metric**: RevShare from swaps using Rainbow's router contract
- **Distribution Period**: February 2023 - January 2024
- **Total Distribution**: ~200K OP to ~5,000 unique addresses

#### Core Measurement Approach
1. Calculate direct revshare from Rainbow wallet swaps
2. Isolate new addresses onboarded to Superchain via Rainbow
3. Measure LTV for new addresses (indirect revshare)
4. Combine direct + indirect contributions to estimate grant payback period

#### Key Metrics Analyzed
- Distribution patterns (OP rewards per user)
- User lifetime metrics (gas fees, transactions, days active)
- Activity trends vs. incentive delivery timing
- Cohort retention and churn rates
- Comparative retention vs. other DEXs (e.g., Metamask)
- LTV analysis and revenue projections

### Data Sources
- **Superchain Data** (via Goldsky): Transaction and trace data
- **Dune Analytics**: Rainbow OP rewards distribution data (CSV)
- **OSS Directory**: Project and address registry
- **OSO Pipeline**: Processed metrics and event data

### Methodology

#### User Identification & LTV Calculation
1. **Reward Recipients**: Lists ~5,000 addresses from Dune Analytics export
2. **Lifetime Metrics**: Aggregates total activity on OP Mainnet and specifically on DEXs:
   - Total gas fees contributed
   - Transaction counts
   - Days active
   - Percentage of activity on DEXs
3. **Activity Windows**:
   - Pre-incentive: 7 days before program start
   - Post-incentive: 7 days before program end
   - Monthly aggregations for trend analysis

#### Retention Analysis
- **Cohort Tracking**: Monthly cohorts based on first Rainbow trade
- **Status Classification**: New, Retained, Dormant, Resurrected, Churned
- **Comparative Analysis**: Rainbow retention vs. other DEXs (Metamask, etc.)

#### ROI Calculation
Compares total OP distributed (~200K OP at $0.75 = ~$150K value) against:
- Total revenue generated by incentivized users
- Estimated LTV based on recent activity patterns
- Retention rates and projected future value

### What Makes It Unique

1. **Grant-to-Behavior Linkage**: Directly connects on-chain token distribution to specific user addresses and their subsequent activity patterns

2. **Temporal Analysis**: Overlays activity metrics with incentive delivery timing to show correlation (peaked in late 2023 coinciding with both incentive delivery and Rainbow's points program launch)

3. **Retention Benchmarking**: Compares Rainbow's user retention against other DEX wallets, providing competitive context

4. **LTV Methodology**: Estimates user lifetime value by combining:
   - Historical activity (total gas fees to date)
   - Recent trends (90-day averages)
   - Retention modeling (churn analysis)

5. **Multi-Level Attribution**: Separates:
   - Direct impact (activity on Rainbow specifically)
   - Indirect impact (broader OP Mainnet activity by incentivized users)
   - DEX-specific vs. all activity

### Key Insights

The analysis reveals:
- Median reward was small (~OP tokens), but some users received 1000+ OP
- Distribution peaked in late 2023 with ~200K OP total
- Activity metrics peaked around the same time then declined 80%+
- Total revenue contribution: ~1,800 ETH on OP Mainnet, ~400 ETH on DEXs
- ~33% of users still active 3 months after program end
- Median engagement: 12 days on OP Mainnet, 4 days on DEXs
- Rainbow's retention patterns similar to Metamask for comparable cohorts

### Use Cases
- **Incentive Program Evaluation**: Measuring ROI of token distribution programs
- **User Acquisition Analysis**: Understanding cost and value of acquired users
- **Retention Optimization**: Identifying what drives user stickiness
- **Competitive Benchmarking**: Comparing wallet performance and user quality
- **Grant Design**: Informing future incentive program structures

---

## 3. S7 TVL Grant Impact Analysis

**File**: `s7-tvl-grant-impact-analysis.py`

### Overview
Provides an observational impact analysis of Season 7 Grants Council grants targeting TVL growth on the Superchain, comparing pre- and post-incentive metrics with attribution adjustments for co-incentives and scope limitations.

### What It Analyzes

#### Program Scope
- **Focus**: S7 Grants Council grants with "TVL" intent and DefiLlama integration
- **Period**: March-May 2025 delivery dates
- **Data Lock**: 2025-07-12 (30 days after program end)
- **Program Dates**:
  - Start: 2025-04-14 (weighted average delivery date)
  - End: 2025-06-12

#### Core Metrics
- **TVL Changes**: Pre-incentive vs. post-incentive TVL using 7-day trailing averages
- **Attribution-Adjusted ROI**: TVL inflows per OP token, adjusted for co-incentives and scope
- **Chain Distribution**: TVL breakdown across Superchain networks
- **Project Performance**: Individual project deep dives with baseline dates

### Data Sources
- **Grants Council Tracker**: Official grant delivery tracking (Google Sheets)
- **OSO Normalized Metadata**: Attribution and measurement assumptions (Google Sheets)
- **DefiLlama API**: TVL and volume data via OSO pipeline
- **OSO Database**: Processed metrics and event data

### Methodology

#### Time Window Analysis
- **Pre-Incentive Window**: 7-day trailing average before program start (2025-04-14)
- **Post-Incentive Window**: 7-day trailing average before program end (2025-06-12)
- **Trailing Days**: Configurable (default: 7 days)

#### Data Processing
1. **Grant Metadata Normalization**:
   - Explodes DefiLlama slugs and chains into individual rows
   - Maps project → protocol → chain combinations
2. **Interpolation**: Fills missing dates in TVL data using linear interpolation
3. **Attribution Calculation**: Adjusts impact based on:
   - Co-incentives from other programs (SuperStacks, ACS)
   - Scope limitations (subset of pools/vaults targeted)

#### Attribution Model
```
Attributed TVL Inflow = (Net TVL Inflow) × (Attribution %)
Attributable ROI = (Attributed TVL Inflow) / (OP Delivered)
```

Where Attribution % accounts for:
- Share of TVL in scope (e.g., 50% if only certain pools incentivized)
- Co-incentive dilution (e.g., other concurrent campaigns)
- Project-specific adjustments documented in metadata

#### Individualized Analysis
The notebook also calculates project-specific baselines:
- Each project's individual grant delivery date (not program start)
- First inflow date (if earlier than delivery)
- Customized pre/post windows per project

### What Makes It Unique

1. **Attribution Framework**: Sophisticated model accounting for:
   - Co-incentives from multiple sources
   - Partial scope (not all protocol TVL targeted)
   - Concurrent campaigns and overlapping programs
   - Project-specific caps based on grant/TVL ratios

2. **Dual Time Horizons**:
   - **Program-level**: Consistent baseline (program start) for all projects
   - **Project-level**: Individual baselines per grant delivery date

3. **Interactive Configuration**: Allows toggling between:
   - OP Delivered vs. OP Total Amount
   - Program-wide vs. individualized date ranges
   - Different trailing window sizes

4. **Multi-Chain Analysis**: Breaks down TVL across different Superchain networks (Base, Mode, OP Mainnet, etc.)

5. **Visualization Suite**:
   - Stacked area charts (by project and by chain)
   - Horizontal bar charts for ROI comparison
   - Time series with program start/end annotations
   - Interactive Altair charts

### Key Insights Structure

The analysis provides:
1. Total projects and OP distributed
2. Net TVL inflows (before attribution)
3. Top performers by attributable ROI
4. Attribution adjustment distribution (% with ≥50% attribution)
5. Positive vs. negative growth by individualized dates

### Limitations

As documented in the notebook:
- Does not account for TVL retention beyond 30-day window
- Attribution percentages are estimates based on available information
- Some protocols had incomplete DefiLlama data
- Market conditions and external factors not isolated
- No causal inference (observational only)

### Use Cases
- **Grant Performance Evaluation**: Measuring ROI of TVL-focused grants
- **Portfolio Analysis**: Comparing performance across grant recipients
- **Attribution Modeling**: Understanding impact amid co-incentives
- **Program Optimization**: Informing future grant program design
- **Stakeholder Reporting**: Transparent impact measurement for governance

---

## 4. S8 TVL Grant Impact Analysis

**File**: `s8-tvl-grant-impact-analysis.py`

### Overview
Comprehensive analysis of S8 Grants Council TVL-focused grants with advanced attribution modeling, on-chain token transfer verification, and detailed project-level performance tracking. Represents a mature evolution of grant impact measurement with sophisticated ROI calculations and transparent methodology.

### What It Analyzes

#### Program Overview
- **Scope**: All S8 TVL-intent grants approved and delivered
- **Total Scale**: ~$2.2M in approved grants (~6.3M OP)
- **Project Count**: 20+ projects with DefiLlama TVL data
- **Chains**: Multi-chain Superchain coverage (Base, OP Mainnet, Mode, Ink, etc.)
- **Time Period**: September 2025 onwards (ongoing)

#### Core Measurements

**Program-Level Metrics**:
- Total TVL change across all grant recipients
- Aggregate fees and revenue generation
- Chain-by-chain TVL distribution
- Co-incentive leverage ratios
- Attributable ROI (TVL per OP, attribution-adjusted)

**Project-Level Deep Dives**:
For each project:
- Baseline TVL (7-day avg at delivery/first inflow)
- Current TVL (7-day avg at latest date)
- TVL delta and days elapsed
- Unadjusted ROI (TVL change per OP)
- Attribution-adjusted ROI
- OP balance tracking over time
- Chain-by-chain breakdown

### Data Sources
- **Karma Platform**: Project metadata and grant applications
- **On-chain Events**: OP token transfer logs for verification
- **DefiLlama**: Protocol TVL data
- **OSO Database**: Consolidated Superchain metrics
- **Attribution Spreadsheet**: Manual attribution assumptions (Google Sheets)

### Methodology

#### Token Transfer Verification
```sql
-- Tracks actual OP token flows to verify delivery
- Inflows: From Optimism multisig (0x8A2725...) to project L2 addresses
- Outflows: From project addresses after first inflow
- Balance Tracking: Daily peak OP balance per project
```

**Verification Logic**:
- Compares first on-chain inflow to expected delivery amount (±2% tolerance)
- Flags discrepancies for manual review
- Accounts for other grants (e.g., audit grants) arriving simultaneously

#### Baseline Date Calculation
```python
project_baseline_date = MIN(initial_delivery_date, first_inflow_date)
```

**Sources Tracked**:
- `delivery_date`: Reported by Grants Council
- `first_inflow`: First on-chain OP token receipt
- `program_start`: Fallback if neither available
- `undelivered`: Special handling for grants not yet sent

**Rationale**: Captures TVL at the earliest point when project could have been influenced by the grant.

#### TVL Calculation
- **Baseline TVL**: 7-day average centered on baseline date (±3 days)
- **Current TVL**: Latest 7-day average (using 2nd-to-last date to avoid data quality issues)
- **TVL Delta**: Current - Baseline
- **Unadjusted ROI**: TVL Delta / OP Delivered

#### Attribution Model

**Formula**:
```
1. Incentive Share = OP Value / (OP Value + Co-incentives)
2. Raw Attribution = Scope % × Incentive Share
3. Apply cap if specified (10× grant/TVL ratio)
4. Round to nearest bucket: 1%, 2%, 5%, 10%, 20%, 50%, 100%
```

**Example**:
- 80% scope, $100K OP grant, $50K co-incentives
- Incentive Share = $100K / ($100K + $50K) = 67%
- Raw = 80% × 67% = 53%
- Final = 50% (rounded to nearest bucket)

**Cap Mechanism**:
```
Attribution Cap = 10 × (OP Grant Value / Baseline TVL)
```
Prevents over-attribution for grants that are tiny relative to existing TVL.

**Inputs**:
- `scope_pct`: Fraction of TVL in scope (e.g., 0.8 if only 80% of pools incentivized)
- `coincentives_usd`: Estimated USD value of concurrent incentives
- `attribution_cap_applied`: Boolean flag for cap enforcement
- `scope_notes` & `coincentives_notes`: Contextual explanations

#### OP Balance Tracking
- Reconstructs daily OP balance from event logs
- Uses peak balance per day (max before any outflows)
- Forward-fills for days with no events
- Shows as secondary Y-axis on TVL charts

### What Makes It Unique

1. **On-Chain Verification**: First grant analysis to verify delivery via on-chain token transfers, reconciling reported delivery dates with actual token receipt

2. **Sophisticated Attribution**: Explicit formulas and calculation steps shown per project, accounting for both scope and co-incentive competition with attribution cap mechanism

3. **Dual Baseline Approach**: Uses MIN(delivery_date, first_inflow_date) for accuracy, tracking which source was used

4. **Financial Context**: OP balance visualization alongside TVL, co-incentive leverage calculations, grant value in both OP and USD

5. **Leaderboard & Rankings**: Projects ranked by attributable ROI with extended details table

6. **Data Quality Handling**: Uses 2nd-to-last date for current TVL (avoids latest date issues), interpolation of missing dates, graceful handling of incomplete data

### Report Structure

**Part 1: Program Overview**
- Grant approval and delivery stats
- Overall TVL change (unadjusted)
- TVL over time by project and by chain
- Distribution of positive vs. negative outcomes

**Part 2: Project Deep Dives**
For each project (sorted by ROI):
- 4 stat cards: Baseline TVL, Current TVL, TVL Change, Adjusted ROI
- Time series chart with OP balance overlay
- Baseline date annotation and footnote
- Full attribution formula breakdown
- Links to Karma, OSO, and Etherscan

**Part 3: Summary**
- Portfolio-level attribution metrics
- Leaderboard by attributable ROI
- Extended financial details (co-incentives, leverage, etc.)
- Aggregation by vertical/category

### Key Features

**Interactive Elements**:
- Filterable project views
- Sortable tables
- Stat cards with color-coded performance
- Hover details on charts

**Transparency**:
- Methodology section with formulas
- Assumptions documented
- Limitations acknowledged
- Data sources linked

**Scalability**:
- Designed to refresh weekly with new data
- Handles new projects automatically
- Supports multiple chains/protocols per project

### Use Cases
- **Real-time Grant Monitoring**: Track impact as grants deploy
- **ROI Benchmarking**: Compare projects within and across seasons
- **Attribution Science**: Understand co-incentive dynamics
- **Portfolio Management**: Optimize future grant allocations
- **Stakeholder Communication**: Transparent reporting to governance
- **Research Template**: Reusable framework for future seasons

---

## 5. Synthetic Control Framework

**File**: `synthetic-control-framework.py`

### Overview
Implements the synthetic control method (SCM) to estimate causal effects of interventions on blockchain networks by creating a weighted combination of control units that serves as a counterfactual for the treated unit. A statistical framework for causal inference commonly used in economics and policy evaluation.

### What It Analyzes

#### Core Concept
Creates a "synthetic" version of a treatment network (e.g., Base) by combining control networks (e.g., Arbitrum, zkSync, Scroll) in a way that best matches the treatment network's pre-intervention behavior. The post-intervention gap between actual and synthetic represents the estimated treatment effect.

#### Configurable Parameters

**Network Selection**:
- **Treatment Network**: The network receiving the intervention (default: Base)
- **Control Networks**: Comparable networks used to construct the synthetic control (default: Arbitrum One, Unichain, zkSync Era, Scroll, Optimism, Linea)

**Metrics**:
- **Dependent Variable**: Primary outcome to analyze (default: TVL - USD from DefiLlama)
- **Predictor Variables**: Metrics used to match synthetic to treatment (default: Stablecoin Value, Tx Costs Median)

Available metrics span:
- TVL (DefiLlama, growthepie, L2Beat variants)
- Financial (Fees, Revenue, Market Cap, Stablecoins)
- Activity (Transaction count, Gas per second, Active addresses, User operations)

**Time Parameters**:
- **Intervention Date**: When the treatment began (e.g., 2025-04-15)
- **Training Period**: Months of pre-intervention data to use for optimization (default: 3 months)

### Data Sources
- **Goldsky/Superchain Data**: Chain-level metrics
- **DefiLlama**: TVL data
- **growthepie**: Financial and activity metrics
- **L2Beat**: TVL variants and user operations
- **OSO Database**: Consolidated `int_chain_metrics` table

### Methodology

#### 1. Data Preparation
```python
# Time windows
training_start = intervention_date - training_months
training_end = intervention_date - 1 day

# Data structure
- Rows: Daily observations
- Columns: Metrics (TVL, fees, etc.)
- Index: [sample_date, chain]
```

#### 2. Optimization Problem
Finds optimal weights W for control networks that minimize:

```
Loss = Σ(Actual_Treatment - Σ(W_i × Control_i))²
```

**Constraints**:
- Weights sum to 1: Σ(W_i) = 1
- Weights are non-negative: W_i ≥ 0
- Each weight between 0 and 1: 0 ≤ W_i ≤ 1

**Methods tried** (uses best result):
1. SLSQP (Sequential Least Squares Programming)
2. BFGS (Broyden–Fletcher–Goldfarb–Shanno)
3. L-BFGS-B (Limited-memory BFGS with bounds)

#### 3. Synthetic Control Construction
```
Synthetic_Value(t) = Σ(W_i × Control_i(t))
```

Where:
- `W_i` = optimal weight for control network i
- `Control_i(t)` = metric value for control i at time t

#### 4. Treatment Effect Estimation
```
Gap(t) = Actual_Treatment(t) - Synthetic(t)
```

For t > intervention_date, Gap estimates the causal effect.

### What Makes It Unique

1. **Multi-Method Optimization**: Tries 3 different optimization algorithms, uses the one with lowest loss, handles edge cases gracefully

2. **Flexible Configuration**: 29 available chains, 15+ metric categories, interactive parameter selection, real-time computation

3. **Comprehensive Diagnostics**:
   - **Pre-Intervention Fit Quality**: RMSE, visual match quality, weight distribution
   - **Post-Intervention Analysis**: Mean gap, gap as % of synthetic control, days of data, cumulative effect

4. **Rich Metadata Output**: Treatment/control units, dependent variable and predictors, data dimensions, means/stds, optimization method and loss, optimal weights

5. **Statistical Foundation**: Based on established causal inference methodology (Abadie, Diamond & Hainmueller 2010, 2015), widely used in economics for policy evaluation

### Visualization

**Main Chart**:
- Line plot with actual treatment network (red/orange), synthetic control (blue), vertical intervention line
- Hover details with exact values and dates
- Unified hover for side-by-side comparison

**Summary Statistics**:
- **Pre-Intervention RMSE**: How well synthetic matches actual before intervention
- **Post-Intervention Avg Gap**: Mean difference after intervention
- **Gap as %**: Percentage effect relative to synthetic control

### Key Assumptions

1. **No anticipation**: Treatment network didn't change behavior before official intervention
2. **No spillovers**: Control networks weren't affected by the treatment
3. **Stable relationships**: Pre-intervention patterns hold post-intervention
4. **Adequate controls**: Control pool includes networks similar enough to treatment

### Use Cases

**Blockchain/Crypto Applications**:
- **Grant Impact**: Measure effect of foundation grants on network TVL
- **Campaign Evaluation**: Assess marketing or incentive campaigns
- **Feature Launches**: Estimate impact of new protocol features
- **Competitive Analysis**: Compare network growth trajectories

**Broader Applications**:
- Policy interventions in economics
- Marketing campaign effectiveness
- Infrastructure investments
- Regulatory changes

### Technical Details

**Libraries Used**:
- **pysyncon**: Synthetic control implementation
- **scipy.optimize**: Multiple optimization algorithms
- **pandas**: Data manipulation
- **plotly**: Interactive visualization
- **marimo**: Reactive notebook framework

**Performance**:
- Handles daily data for 1+ years
- Optimization completes in <2 seconds
- Supports 10+ control networks simultaneously
- Real-time interactive updates

### Interpretation Guide

**Good Fit Indicators**:
- Low pre-intervention RMSE (<10% of mean)
- Smooth visual match in training period
- Balanced weights (not all weight on one control)
- Plausible post-intervention gap

**Warning Signs**:
- High pre-intervention RMSE
- Unbalanced weights (>80% on one control)
- Implausible gap magnitude
- Optimization failure across all methods

### Example Workflow

1. Select treatment network (e.g., Base)
2. Choose control networks (similar L2s)
3. Set intervention date (e.g., major grant program start)
4. Select dependent variable (e.g., TVL)
5. Choose predictors (metrics that predict TVL)
6. Set training period (e.g., 3 months)
7. Click "Compute"
8. Review fit quality and weights
9. Interpret post-intervention gap

### Resources Referenced
- Wikipedia: [Synthetic Control Method](https://en.wikipedia.org/wiki/Synthetic_control_method)
- GitHub: [pysyncon Documentation](https://github.com/sdfordham/pysyncon)
- OSO: [Python API Docs](https://docs.opensource.observer/docs/get-started/python)
- Marimo: [Framework Documentation](https://docs.marimo.io/)

---

## 6. TVL Grant ROI Analysis (Portfolio-Level)

**File**: `tvl-grant-roi-analysis.py`

### Overview
Comprehensive portfolio-level benchmarking of all TVL-focused grants on the Superchain from July 2021 through September 2025, analyzing market share, fee generation, activity metrics, and lifetime value (LTV) across DeFi verticals. Provides a holistic view of grant program ROI with sophisticated cohort analysis and joyplot visualizations.

### What It Analyzes

#### Portfolio Scope
- **Time Period**: July 2021 - September 2025 (4+ years)
- **Program Coverage**: All prospective grants through Season 7
- **Project Universe**: 40+ DeFi protocols with >$1M TVL on Superchain
- **Total Grants**: Includes both Gov Fund (Grants Council) and Partner Fund (direct grants)

#### Core Metrics

**Market Dynamics**:
- TVL market share by DeFi vertical (DEXs, Lending, Derivatives, etc.)
- Fee generation per $100M TVL across verticals
- Activity (userops) per $1M TVL
- Revenue attribution to L2 sequencers

**Vertical Comparisons**:
- **DEXs vs. Lending**: Fee efficiency, activity density, retention patterns
- **Time Series**: TVL, fees, and userops over time by vertical
- **Dual-axis charts**: TVL (primary) with fees/userops (secondary)

**LTV Analysis**:
- Protocol age (months since first activity)
- All-time high TVL vs. current TVL
- 90-day metrics (TVL, fees, revenue, userops)
- Lifetime metrics (all-time fees, revenue, userops)
- Fee efficiency (ETH per $100M TVL)

#### Cohort Classification
Projects segmented into:
- 🟢 **New Protocol** (<12 months old)
- 🔴 **Top Protocol** (≥$75M current TVL)
- 🟡 **Former Top Protocol** (≥$75M all-time high, <$75M current)
- ⚪️ **Less Relevant Protocol** (All others)

### Data Sources
- **Superchain Data** (via Goldsky): Transaction and trace data
- **DefiLlama**: TVL data for all protocols
- **OSS Directory**: Project and address registry
- **OSO Pipeline**: Pre-aggregated metrics (`int_optimism_grants_rolling_defi_*` tables)
- **Grants Records**: Internal tracking sheets + on-chain data

### Methodology

#### Grant Consolidation
```python
# Combines two grant streams:
1. Grants Council (Gov Fund): Seasons 3-7, DeFi projects with >$1M TVL
2. Partner Fund (Direct): Manual list of major grants (Lido, Exactly, Ethos)

# Aggregates to project level:
- First grant delivery date
- Total grants (OP and USD value)
- Grant count
```

#### Metrics Calculation

**Rolling Averages**:
All metrics use 7-day trailing averages to smooth volatility:
```sql
TVL (7D) = AVG(TVL over last 7 days)
Fees (7D) = SUM(fees over last 7 days)
Revenue (7D) = SUM(revenue over last 7 days)
Userops (7D) = SUM(userops over last 7 days)
```

**Fee Efficiency Metrics**:
```python
Fees per $100M TVL = Fees (7D) / (TVL (7D) / 100_000_000)
Userops per $1M TVL = Userops (7D) / (TVL (7D) / 1_000_000)
```

#### LTV/CAC Model

**Inputs**:
- `Protocol Age`: Months since first on-chain activity
- `Expected Lifetime`: 60 months (assumption)
- `Revenue - Last 90D`: Recent revenue (ETH)
- `Revenue - Actual to Date`: Lifetime revenue (ETH)
- `CAC`: All grants (OP) × OP price ($0.155/OP)

**Calculation**:
```python
Monthly Revenue = Revenue (90D) / 3
Expected Lifetime Remaining = 60 - Protocol Age
Projected Revenue = Monthly Revenue × Remaining Lifetime
LTV = Actual Revenue + Projected Revenue
LTV/CAC = LTV / CAC
```

**Interpretation**:
- LTV/CAC > 1.0: Grant has positive ROI
- LTV/CAC < 1.0: Grant underwater (so far)

#### Monthly Uplift Analysis
For each project, calculates metrics at 0, 3, 6, 12, 18, 24, 36 months post-grant:
- **Month 0 TVL**: Baseline at grant delivery
- **Month N TVL**: TVL at Nth month anniversary
- **Month N TVL Uplift**: Change from baseline
- **Month N Cumulative Fees/Revenue/Userops**: Total since grant

Uses the deepest available month with data for "Incremental" columns.

### What Makes It Unique

1. **Vertical Benchmarking**: Cross-vertical comparison showing DEXs generate 15X more fees per TVL than lending, 10X more userops per TVL

2. **LTV/CAC Framework**: Applies SaaS-style metrics to DeFi protocols, projects future revenue based on recent performance, ranks by ROI

3. **Joyplot Visualizations**:
   ```python
   make_superchain_tvl_joyplot(
       project_list,     # Filter to specific cohort
       smoothing=7,      # Days for rolling average
       resample='7D',    # Downsample frequency
       colorscale='Reds' # Color scheme
   )
   ```
   - Ridge plots showing TVL over time per project
   - Projects ordered by absolute TVL uplift
   - Annotations for first grant date and amount
   - Right-side labels showing TVL change and cumulative fees

4. **Performance Bands**: Generates percentile bands (25th, 50th, 75th) for key metrics at monthly intervals, enabling benchmarking against portfolio

5. **Cohort-Specific Insights**:
   - **Top Protocols** (🔴): Hold ~70% of Superchain TVL, collectively received ~8M OP
   - **Less Relevant** (⚪️): Includes "zombie" protocols, often negative LTV

### Key Insights Structure

1. **Market Share**: % of TVL in DEXs + Lending vs. other verticals
2. **Fee Efficiency**: Fees per $100M TVL over time
3. **Vertical Comparison**: DEX vs. Lending fee multiples
4. **Activity Comparison**: DEX vs. Lending userop multiples
5. **Top Protocols**: Who they are, their metrics, and grant amounts

### Visualizations

**Time Series Charts**:
- Stacked Area: TVL by vertical over time
- Dual-Axis: TVL (left) with fees/userops (right) by vertical
- Line Charts: Fee efficiency and revenue trends

**Tables**:
- Top Protocols: Sorted by fee efficiency with 90D and lifetime metrics
- LTV Analysis: Projects ranked by LTV/CAC ratio
- Vertical Aggregation: Summary stats by DeFi category

**Joyplots**:
- Top Protocol Ridge Plot: Shows grant timing and TVL trajectories
- Cohort-Specific Plots: Filterable by cohort classification
- Interactive Dropdown: Select cohort to visualize

### Methodology Details

**Attribution**:
- Full attribution to first grant (no co-incentive adjustments)
- Includes both Grants Council and Partner Fund
- Aggregates multiple grants to same project
- Uses delivery date (not approval date)

**Vertical Classification**:
- **Best Vertical**: Primary DeFi category
- **All Categories**: Tags for protocols spanning multiple verticals
- Based on DefiLlama categories + manual curation

**Time Alignment**:
- **Grant Date**: First delivery date
- **Baseline**: TVL on grant date (Month 0)
- **Evaluation**: Monthly anniversaries (3, 6, 12, 18, 24, 36 months)
- **Current**: 2025-09-30 snapshot for LTV calculations

### Limitations

As acknowledged:
- Assumes 60-month protocol lifetime (arbitrary)
- Uses fixed OP price ($0.155) for CAC
- Projects future revenue from 90D average (may not hold)
- No attribution adjustments for co-incentives
- Market conditions not isolated
- Survivorship bias (only >$1M TVL projects)

### Use Cases

**Grant Program Management**:
- Portfolio ROI: Overall return on TVL grant investments
- Vertical Strategy: Which DeFi categories to prioritize
- Cohort Analysis: New vs. established protocol performance

**Benchmarking**:
- Performance Bands: Is a project top 25%, median, or bottom 25%?
- Vertical Norms: Expected fee/activity levels by category
- Temporal Patterns: How long does TVL growth take?

**Grant Design**:
- Target Cohorts: Should we fund new protocols or blue chips?
- Size Optimization: Optimal grant size by vertical
- Success Predictors: What metrics predict LTV/CAC >1?

**Stakeholder Communication**:
- Governance Reports: Transparent portfolio-level metrics
- Vertical Deep Dives: DEX vs. Lending performance
- Visual Storytelling: Joyplots for grant impact narrative

### Technical Features

- **Modular Functions**: Reusable components for different cohorts
- **Interactive Filters**: Dropdown selectors for cohort and vertical
- **Dual-Axis Charts**: Plotly subplots with secondary y-axis
- **Custom Joyplots**: Advanced ridge plot implementation with annotations
- **Color Palettes**: Consistent visual design across charts
- **Freeze Columns**: Table navigation with frozen project names

---

## Comparative Overview

### By Analysis Type

| Notebook | Analysis Type | Scope | Time Horizon |
|----------|---------------|-------|--------------|
| Chainlink ROI | Infrastructure Impact | Single provider (oracle) | Ongoing |
| Rainbow Wallet ROI | User Acquisition | Single wallet (~5K users) | 11 months (Feb 2023 - Jan 2024) |
| S7 TVL Grants | Grant Program Evaluation | Season 7 (20+ projects) | 2 months (Mar-May 2025) |
| S8 TVL Grants | Grant Program Evaluation | Season 8 (20+ projects) | Ongoing (Sept 2025+) |
| Synthetic Control | Causal Inference Framework | Configurable (any network) | Configurable |
| TVL Grant ROI | Portfolio Benchmarking | All TVL grants (40+ projects) | 4+ years (Jul 2021 - Sep 2025) |

### By Methodology Maturity

**Foundation Level** (Observational):
- Rainbow Wallet ROI: Basic LTV calculation, retention tracking
- Chainlink ROI: Multi-layer attribution without causal claims

**Intermediate Level** (Attribution Modeling):
- S7 TVL Grants: Co-incentive adjustments, dual baselines
- TVL Grant ROI: Vertical benchmarking, cohort analysis

**Advanced Level** (Verification & Causal Inference):
- S8 TVL Grants: On-chain verification, sophisticated attribution caps
- Synthetic Control: Rigorous causal inference methodology

### By Key Innovation

| Notebook | Primary Innovation |
|----------|-------------------|
| Chainlink ROI | Multi-layer ecosystem attribution (direct + indirect impact) |
| Rainbow Wallet ROI | Grant-to-behavior linkage (address-level tracking) |
| S7 TVL Grants | Dual baseline approach (program-wide + individualized) |
| S8 TVL Grants | On-chain verification of token transfers |
| Synthetic Control | Statistical causal inference for blockchain interventions |
| TVL Grant ROI | Joyplot visualizations with grant timing overlays |

### By Use Case Priority

**For Grant Program Managers**:
1. S8 TVL Grants (real-time monitoring)
2. TVL Grant ROI (portfolio benchmarking)
3. S7 TVL Grants (seasonal evaluation)

**For Researchers/Analysts**:
1. Synthetic Control (causal inference)
2. S8 TVL Grants (methodology template)
3. Chainlink ROI (infrastructure attribution)

**For Governance/Stakeholders**:
1. TVL Grant ROI (comprehensive overview)
2. S7 TVL Grants (seasonal deep dive)
3. Rainbow Wallet ROI (user acquisition case study)

### Data Requirements Comparison

| Notebook | Primary Data Sources | Special Requirements |
|----------|---------------------|---------------------|
| Chainlink ROI | Transaction traces, contract labels | Oracle contract addresses |
| Rainbow Wallet ROI | Dune Analytics export | List of reward recipients |
| S7 TVL Grants | DefiLlama API, attribution sheet | Co-incentive estimates |
| S8 TVL Grants | On-chain events, Karma platform | OP token transfer logs |
| Synthetic Control | Chain-level metrics (OSO DB) | Comparable control networks |
| TVL Grant ROI | 4+ years historical data | DefiLlama integration |

### Attribution Sophistication

**No Attribution Adjustments**:
- Rainbow Wallet ROI (all activity attributed to grant)
- TVL Grant ROI (full attribution to first grant)

**Simple Attribution**:
- Chainlink ROI (lower/upper bound ranges)

**Moderate Attribution**:
- S7 TVL Grants (co-incentive share, scope percentage)

**Advanced Attribution**:
- S8 TVL Grants (co-incentive + scope + attribution caps)

**Causal Attribution**:
- Synthetic Control (counterfactual-based treatment effect)

---

## Getting Started

### Prerequisites
All notebooks require:
- Python 3.9+
- marimo (`pip install marimo`)
- pyoso (`pip install pyoso`)
- Standard data science stack (pandas, numpy, plotly)

Specific notebooks may require:
- pysyncon (Synthetic Control)
- scipy (Synthetic Control)
- External data files (Rainbow Wallet, S7/S8 attribution sheets)

### Running a Notebook

```bash
# Navigate to the directory
cd /path/to/inspiration-notebooks

# Run with marimo
marimo edit <notebook-name>.py

# Example
marimo edit synthetic-control-framework.py
```

### Choosing the Right Notebook

**Start here if you want to**:
- Measure infrastructure ROI → **Chainlink ROI Analysis**
- Evaluate a user incentive program → **Rainbow Wallet ROI Analysis**
- Assess a recent grant season → **S7 or S8 TVL Grant Impact**
- Establish causal effects → **Synthetic Control Framework**
- Benchmark across all grants → **TVL Grant ROI Analysis**

---

## Contributing

These notebooks serve as templates and inspiration for future grant impact analyses. When adapting them:

1. **Preserve methodology sections** for transparency
2. **Document assumptions explicitly** in accordion elements
3. **Provide data source links** for reproducibility
4. **Include limitation sections** to acknowledge uncertainties
5. **Use consistent formatting** (stat cards, plotly configs, table formats)

---

## License & Attribution

These notebooks were created by the OSO (Open Source Observer) team for the Optimism Collective. When reusing or adapting:

- Credit the OSO team
- Link to the original repository
- Note any modifications made
- Maintain open-source spirit

---

## Questions or Issues

For questions about methodology, data access, or adaptations:
- Open an issue in the OSO repository
- Contact the OSO team via Discord
- Review the [OSO documentation](https://docs.opensource.observer)
