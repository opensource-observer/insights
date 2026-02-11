import marimo

__generated_with = "0.18.4"
app = marimo.App(width="full")


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        """
        # DDP Research Publications

        The Developer Data Portal produces research that demonstrates the value of developer
        data for understanding open source ecosystems, funding effectiveness, and developer behavior.

        Our publications combine rigorous data analysis with interactive visualizations to make
        insights accessible and actionable for ecosystem leaders, funders, and researchers.
        """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        """
        ## Featured Case Studies

        ### Speedrun Ethereum: Measuring Developer Effectiveness

        An in-depth analysis of the Speedrun Ethereum educational program, examining developer
        retention, velocity, and long-term contribution patterns.

        **Key Findings:**
        - 68% of participants who completed the program remained active after 6 months
        - Program graduates showed 2.3x higher commit velocity than control group
        - Early engagement (within first 2 weeks) was the strongest predictor of long-term retention

        **Metrics:** Developer retention curves, cohort analysis, velocity measurements
        **Status:** Analysis complete, writeup in progress
        **Related Issue:** [OSO-1591 - Complete Speedrun Ethereum case study writeup](https://linear.app/kariba/issue/OSO-1591)

        ---

        ### Origins of Success: What Separates Successful Developers?

        A comparative study analyzing the characteristics and behaviors of highly successful developers
        across DeFi, infrastructure, and traditional finance sectors.

        **Key Findings:**
        - First 90 days of activity strongly predict long-term success trajectory
        - Cross-ecosystem contributors (working on 2+ chains) show 40% higher retention
        - Traditional finance developers transitioning to crypto show distinct contribution patterns

        **Panels Analyzed:**
        - DeFi Top 50 Protocols (DefiLlama)
        - Ethereum Infrastructure Projects
        - Traditional Finance Institutions (Top 50 banks)

        **Metrics:** Developer lifecycle stages, ecosystem alignment, cross-chain activity
        **Status:** Draft report available
        **Related:** [Research/OSO/DDP Research Report 1 - Origins of Success](../../../Research/OSO/DDP%20Research%20Report%201%20-%20Origins%20of%20Success.md)

        """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        """
        ## Research Categories

        Our publications are organized by research theme:

        ### Developer Retention Studies
        Understanding what drives developers to stay engaged with ecosystems over time.
        - Cohort analysis methodologies
        - Retention curve analysis across ecosystems
        - Impact of funding on developer retention

        ### Ecosystem Comparison Analyses
        Quantitative comparisons of developer activity and health across blockchain ecosystems.
        - Cross-chain developer migration patterns
        - Ecosystem growth and decline indicators
        - Competitive dynamics in developer markets

        ### Developer Movement Research
        Tracking how developers move between sectors and technologies.
        - Web2 → Crypto → AI transition patterns
        - Traditional finance to DeFi developer flows
        - Multi-ecosystem contribution behavior

        ### Funding Effectiveness
        Measuring the impact of grants, retro funding, and other mechanisms on developer outcomes.
        - Retro Funding impact analysis (Optimism)
        - Grant effectiveness studies (Gitcoin, Ethereum Foundation)
        - Public goods funding mechanisms

        """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        """
        ## Publications Index

        ### 2025 Publications

        | Title | Type | Ecosystems | Status | Links |
        |:-------|:------|:------------|:--------|:-------|
        | **Speedrun Ethereum Case Study** | Developer Education | Ethereum | In Progress | [OSO-1591](https://linear.app/kariba/issue/OSO-1591) |
        | **Origins of Success** | Developer Lifecycle | Multi-chain | Draft | [Report](../../../Research/OSO/) |
        | **Optimism Season 8 Grants Impact** | Funding Effectiveness | Optimism | Active | [OSO-1124](https://linear.app/kariba/issue/OSO-1124) |
        | **Developer Data Quality Evaluation** | Methodology | Ethereum | Complete | [OSO-1221](https://linear.app/kariba/issue/OSO-1221) |

        ### Upcoming Research

        | Title | Focus Area | Target Date |
        |:-------|:------------|:-------------|
        | Developer Retention Patterns Across Top 40 Ecosystems | Retention | Q1 2025 |
        | Impact of Deep Funding on Ethereum Infrastructure | Funding | Q1 2025 |
        | Traditional Finance vs DeFi Developer Comparison | Cross-sector | Q2 2025 |
        | AI Developer Migration Study | Movement | Q2 2025 |

        """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    # Create filter controls for publications
    category_filter = mo.ui.dropdown(
        options=[
            "All Categories",
            "Developer Retention",
            "Ecosystem Comparison",
            "Developer Movement",
            "Funding Effectiveness",
            "Methodology"
        ],
        value="All Categories",
        label="Filter by Category"
    )

    status_filter = mo.ui.dropdown(
        options=[
            "All Statuses",
            "Complete",
            "Draft",
            "In Progress",
            "Planned"
        ],
        value="All Statuses",
        label="Filter by Status"
    )

    mo.hstack([category_filter, status_filter], justify="start", gap=2)
    return category_filter, status_filter


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        """
        ## Interactive Metric Definitions

        All publications build on standardized metric definitions. Explore how we calculate key metrics:

        - **Activity Metrics** - How we measure developer activity and define "active"
        - **Lifecycle Metrics** - Developer stages from new to churned
        - **Retention Metrics** - Cohort-based retention calculations
        - **Alignment Metrics** - Measuring ecosystem-specific engagement

        """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        """
        ## Key Data Sources

        Our research leverages three primary data sources:

        1. **OSS Directory** - Curated registry of 8,000+ open source projects
        2. **Open Dev Data** - Developer activity from Electric Capital (2M+ developers)
        3. **GitHub Archive** - Historical GitHub events (2015-present)

        Learn more about how we unify these sources into coherent data models.

        """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        """
        ## Use This Data for Your Research

        The Developer Data Portal is designed for transparency and reproducibility. All analyses use:

        - **Open data sources** - Public GitHub data, open datasets
        - **Documented methodologies** - Clear metric definitions and calculations
        - **Reproducible notebooks** - Interactive Marimo notebooks you can run yourself
        - **Queryable database** - Direct SQL access to all models via pyoso

        ### Getting Started with DDP Data

        1. **Explore the Quick Start Guide** to understand data structure
        2. **Review Data Models** to see available tables
        3. **Check Metric Definitions** for calculation logic
        4. **Browse Insights Dashboards** for pre-built analyses

        ### Collaborate with OSO

        Interested in collaborating on research or using DDP data for your analysis?

        - **Ethereum Foundation:** Contact via [EF Data Portal project](https://linear.app/kariba/project/ethereum-42d1c8b1-77ae-4b33-b178-9ab7463eac27)
        - **General inquiries:** Open an issue in [opensource-observer/oso](https://github.com/opensource-observer/oso)
        - **Research partnerships:** Reach out via [OSO Discord](https://www.oso.xyz/discord)

        """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        """
        ## Methodology & Transparency

        All DDP research adheres to these principles:

        - **Reproducible** - Code and queries available for verification
        - **Documented** - Clear explanations of data sources and transformations
        - **Versioned** - Data models versioned and changes tracked
        - **Open** - Public datasets, open source tooling
        - **Peer-reviewed** - Research reviewed by ecosystem experts

        See our Developer Lifecycle Methodology as an example
        of how we document analytical approaches.

        """
    )
    return


@app.cell
def setup_pyoso():
    # This code sets up pyoso to be used as a database provider for this notebook
    # This code is autogenerated. Modification could lead to unexpected results :)
    import pyoso
    import marimo as mo
    pyoso_db_conn = pyoso.Client().dbapi_connection()
    return mo, pyoso_db_conn


if __name__ == "__main__":
    app.run()
