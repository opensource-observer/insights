import os
from typing import Optional
from pyoso import Client
from langchain_community.utilities import SQLDatabase
from langchain_experimental.sql import SQLDatabaseChain
from langchain_openai import ChatOpenAI
import json
from langchain_core.prompts import PromptTemplate
from sqlalchemy import text
import pandas as pd

class OsoLangChainQuery:
    def __init__(self, oso_api_key: str, openai_api_key: Optional[str] = None):
        """
        Initialize the OsoLangChainQuery class with API keys for OSO and OpenAI.
        """
        self.oso_client = Client(api_key=oso_api_key)
        
        # Initialize OpenAI client
        self.llm = ChatOpenAI(
            temperature=0,
            model="gpt-3.5-turbo",
            api_key=openai_api_key or os.getenv("OPENAI_API_KEY")
        )
        
        # Create a simple prompt for SQL generation
        self.prompt = PromptTemplate(
            input_variables=["input"],
            template="""
            Generate a SQL query for the following tables:
            - metrics_v0: Contains metric definitions with columns:
              * metric_id (TEXT): Unique identifier
              * metric_name (TEXT): Name of metric (e.g. active_developers_count)
              * metric_source, metric_namespace, display_name, description

            - timeseries_metrics_by_project_v0: Contains metric values over time:
              * metric_id (TEXT): References metrics_v0.metric_id
              * project_id (TEXT): References projects_v1.project_id
              * sample_date (TIMESTAMP): When the metric was recorded
              * amount (FLOAT): The metric value, use this column for all metric values
              * unit (TEXT): Unit of measurement

            - projects_v1: Contains project information:
              * project_id (TEXT): Unique identifier
              * project_name (TEXT): Name of the project
              * project_source, project_namespace, display_name, description

            Important SQL syntax rules:
            1. For string matching: Use LIKE (not ILIKE) and UPPER() for case-insensitive matching
            2. Use table aliases: m for metrics_v0, t for timeseries, p for projects
            3. Only join tables when you need:
               - Join timeseries table when you need metric values or dates
               - Join projects table when you need project information
               - For just listing or searching metrics, use only metrics_v0

            Select metrics metadata:
            - GITHUB_active_developers_monthly - monthly active developers count    
            - GITHUB_commits_monthly - monthly commit frequency count
            - GITHUB_contributors_monthly - monthly contributors count
            - GITHUB_merged_pull_requests_monthly - monthly merged pull requests count

            Question: {input}

            Return only the SQL query, nothing else.
            """
        )
    
    def execute_query(self, natural_language_query: str) -> dict:
        """Execute a natural language query through PyOSO."""
        # Generate SQL query using OpenAI
        response = self.llm.invoke(self.prompt.format(input=natural_language_query))
        sql_query = response.content.strip().rstrip(';')
        
        print("Executing SQL Query:", sql_query)
        
        # Execute query using PyOSO
        df = self.oso_client.to_pandas(sql_query)
        
        # Convert date columns to datetime
        for col in df.columns:
            if 'date' in col.lower():
                df[col] = pd.to_datetime(df[col])
        
        return {
            "sql_query": sql_query,
            "results": df.to_dict(orient='records')
        }

# Example usage
if __name__ == "__main__":
    # Initialize with your API keys
    oso_api_key = os.getenv("OSO_API_KEY")
    
    query_handler = OsoLangChainQuery(oso_api_key)
    
    while True:
        # Get query from user input
        user_query = input("\nEnter your question (or 'quit' to exit): ")
        
        # Check if user wants to quit
        if user_query.lower() in ['quit', 'exit', 'q']:
            print("Exiting...")
            break
            
        # Execute query
        results = query_handler.execute_query(user_query)
        print("\nQuery Results:", json.dumps(results["results"], indent=2))
        