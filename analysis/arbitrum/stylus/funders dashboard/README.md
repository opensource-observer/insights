# Stylus Sprint Ecosystem Dashboard

A Streamlit-based dashboard for visualizing and analyzing the Stylus Sprint ecosystem data, powered by Open Source Observer.

## Overview

The Stylus Sprint Ecosystem Dashboard provides interactive visualizations and insights into the Stylus Sprint ecosystem. It features various metrics, growth analysis, and network visualizations to help understand the ecosystem's development and trends.

## Installation

1. Clone the repository:
```bash
git clone https://github.com/your-org/stylus.git
cd stylus
```

2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Run the Streamlit app:
```bash
streamlit run run_dashboard.py
```

2. Open your web browser and navigate to the provided local URL (typically http://localhost:8501)

## Dependencies

- streamlit >= 1.32.0
- pandas >= 2.0.0
- plotly >= 5.18.0
- networkx >= 3.1
- python-dotenv == 1.0.0
- pyoso == 0.1.0

## Project Structure

```
stylus/
├── data/               # Data files and resources
├── images/            # Image assets
├── scripts/           # Utility scripts
├── stylus_dashboard/  # Dashboard application package
│   ├── components/    # Reusable dashboard components
│   ├── utils/        # Utility functions
│   ├── main.py       # Main dashboard application
│   └── config.py     # Configuration settings
├── requirements.txt   # Project dependencies
└── run_dashboard.py   # Dashboard entry point
```

Powered by [Open Source Observer](https://opensource.observer)
