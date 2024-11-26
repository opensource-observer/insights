## Table of Contents
- [Overview](#Overview)
- [How to Use](#How-to-Use)
- [Classification Approach](#Classification-Approach)
- [Pros](#Pros)
- [Cons](#Cons)
- [Future Enhancements for Improved Project Analysis](#Future-Enhancements-for-Improved-Project-Analysis)

## Overview

[**OSO Instant Analysis**](https://oso-instant-analysis.streamlit.app/) is a tool designed to help grant managers quickly assess and profile open-source projects within a given collection. By classifying projects based on their activity, popularity, and community involvement, the application provides a high-level understanding of the cohort's nature. This enables grant managers to:

- **Identify Patterns**: Understand the distribution of projects across meaningful categories like "High Popularity, Actively Maintained" or "Inactive or Abandoned."
- **Explore Granular Details**: Drill down into specific categories to access detailed data on the projects that make up each group.
- **Make Data-Driven Decisions**: Use interactive visualizations and sortable metrics to evaluate project viability, identify growth opportunities, and strategize funding allocations effectively.

## How to Use

On https://oso-instant-analysis.streamlit.app/, follow these steps to explore and analyze:

1. **Select a Collection**: Choose a collection from the dropdown to analyze its projects.
2. **View High-Level Insights**:
   - Check the **Bar Chart** for a quick count of projects in each category.
    - Use the **Treemap** to see the distribution of projects by category. 
3. **Drill Down into Categories**: :
    - Use the **Scatter Plot** to compare popularity (stars) and developer activity.
    - Search, sort, or download detailed metrics in the **Data Table** to compare and identify key projects.

## Classification Approach

The script classifies each project using predefined criteria. It uses the following metrics:
- **Popularity**: Star and fork counts.
- **Community Engagement**: Number of developers and contributors.
- **Activity**: Commit frequency in the last 6 months.
- **Age**: Time since the first commit.
- **Recent Updates**: Time since the last commit

| **Category**                             | **Popularity (Stars & Forks)** | **Community Engagement (Devs & Contributors)** | **Activity (Commits)**    | **Age**   | **Recent Updates**    |
| ---------------------------------------- | ------------------------------ | ---------------------------------------------- | ------------------------- | --------- | --------------------- |
| **High Popularity, Actively Maintained** | Stars > 200, Forks > 100       | Devs > 10, Contributors > 50                   | Commits > 200 in 6 months | Any       | Within last 180 days  |
| **High Popularity, Low Maintenance**     | Stars > 200, Forks > 100       | Devs: 4–10, Contributors: 10–50                | Commits < 30 in 6 months  | > 2 years | None in last 180 days |
| **Niche, Actively Maintained**           | Stars: 30–200, Forks: 10–100   | Devs > 4, Contributors > 10                    | Commits > 200 in 6 months | Any       | Within last 180 days  |
| **New and Growing**                      | Stars: 2–30, Forks: 1–10       | Devs: 1–4, Contributors: 2–10                  | Commits > 30 in 6 months  | ≤ 2 years | Within last 180 days  |
| **Mature, Low Activity**                 | Stars > 200, Forks > 100       | Devs < 4, Contributors < 10                    | Commits < 30 in 6 months  | > 2 years | None in last 180 days |
| **Inactive or Abandoned**                | Stars < 2, Forks < 1           | Devs < 1, Contributors < 2                     | Commits < 1 in 6 months   | Any       | None in last 365 days |
| **Low Popularity, Low Activity**         | Stars < 30, Forks < 10         | Devs ≤ 4, Contributors ≤ 15                    | Commits ≤ 12 in 6 months  | Any       | Any                   |
| **Moderate Popularity, Low Activity**    | Stars: 7–200, Forks: 3–70      | Devs: 2–9, Contributors: 5–34                  | Commits ≤ 23 in 6 months  | Any       | Any                   |
| **Moderately Maintained**                | Any                            | Any                                            | Commits > 50 in 6 months  | Any       | Within last 180 days  |
| **Uncategorized**                        | N/A                            | N/A                                            | N/A                       | N/A       | N/A                   |

## Pros
- **Comprehensive**: Evaluates multiple metrics (popularity, activity, community engagement) for a holistic project profile.
- **Granular**: Provides detailed categories to capture diverse project dynamics, from "New and Growing" to "Mature, Low Activity."
- **Actionable Insights**: Enables grant managers to identify trends, prioritize projects, and make informed, data-driven decisions.

## Cons
- **Static Criteria**: The thresholds for metrics (e.g., stars > 200, commits > 200) are rigid and may not adapt well to different contexts or domains.
- **Ambiguity for Edge Cases**: Projects near category boundaries may not be classified accurately, leading to potential misrepresentation.
- **Overemphasis on Popularity**: Metrics like stars and forks heavily influence some categories, which may not always reflect the true value or impact of a project.
- **Lack of Weighting**: All metrics are treated equally, which might not align with the relative importance of these factors in certain scenarios.
- **Neglects Qualitative Factors**: Ignores subjective aspects like the quality of contributions, innovative potential, or alignment with specific grant goals.

## Future Enhancements for Improved Project Analysis
- **Configurable Categories**: Allow grant managers to create custom categories on the fly using individual metrics or composites tailored to the ecosystem's context.
- **Priority Weighting**: Enable grant managers to assign relative importance to metrics (e.g., emphasizing developer activity over popularity) to reflect strategic priorities.
- **Dynamic Thresholds**: Implement clustering techniques (e.g., k-means, hierarchical clustering) to identify natural breakpoints in metrics for more effective and adaptive grouping.
- **Incorporate Qualitative Factors**: Include non-quantitative insights like project alignment with goals, innovative potential, or qualitative community feedback.
- **Address Edge Cases**: Develop rules for projects near category boundaries to reduce misclassification or ambiguity.
- **Context-Specific Profiles**: Offer pre-configured classification profiles optimized for specific ecosystems, domains, or funding goals.