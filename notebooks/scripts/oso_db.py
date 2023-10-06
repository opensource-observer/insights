import csv
from datetime import datetime
from dotenv import load_dotenv
import os
import psycopg2


def connect_to_database():

    load_dotenv()
    db_host = os.getenv("DB_HOST")
    db_port = os.getenv("DB_PORT")
    db_name = os.getenv("DB_NAME")
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    connection_string = f"postgres://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

    try:
        connection = psycopg2.connect(connection_string)
        return connection
    except psycopg2.Error as e:
        print("Error connecting to the database:", e)
        return None


def read_query_from_file(filename):

    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
    with open(path, 'r') as file:
        query = file.read()
    return query


def execute_query(query, params=None, col_names=False):
    
    results = None
    connection = connect_to_database()
    if connection:    
        try:
            with connection.cursor() as cursor:
                cursor.execute(query, params)
                if col_names:
                    results = cursor.fetchall()
                    column_names = [desc[0] for desc in cursor.description]
                    results = [column_names] + results
                else:
                    results = cursor.fetchall()
                
        except psycopg2.Error as e:
            print("Error executing query:", e)    
        
        connection.close()

    return results


def name_data_file(query, params=None):
    
    now = datetime.now()
    timestamp = now.strftime("%Y-%m-%d")
    query_name = query.split('.')[0]
    filename = f"{timestamp}_{query_name}"
    if params:
        filename = "_".join([filename, *params])
    return filename


def dump_results_to_csv(results, filename):

    local_path = "../data/" + filename + ".csv"
    abs_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), local_path)
    with open(abs_path, 'w') as file:
        writer = csv.writer(file)
        writer.writerows(results)
    print("Results dumped to:", local_path)
    return abs_path


def query_and_dump_to_csv(query_name, params=None, col_names=True):

    query_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "queries", query_name + ".sql")
    query = read_query_from_file(query_path)
    results = execute_query(query, params=params, col_names=col_names)
    if results:
        filename = name_data_file(query_name, params)
        return dump_results_to_csv(results, filename)