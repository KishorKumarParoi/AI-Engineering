from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime

# Define our task 1
def preprocess_data():
    print("Preprocessing data...")

# Define task 2
def train_model():
    print("Training model...")

# Define task 3
def evaluate_model():
    print("Evaluating model...")

# Define task 4
def deploy_model():
    print("Deploying model...")

# Initialize the DAG
with DAG(
    dag_id="ml_pipeline_dag",
    start_date=datetime(2026,8,1),
    schedule="@weekly",
    catchup=False
) as dag:

    # Define the task pipeline
    preprocess_task = PythonOperator(
        task_id="preprocess_data",
        python_callable=preprocess_data,
    )

    train_task = PythonOperator(
        task_id="train_model",
        python_callable=train_model,
    )

    evaluate_task = PythonOperator(
        task_id="evaluate_model",
        python_callable=evaluate_model,
    )

    deploy_task = PythonOperator(
        task_id="deploy_model",
        python_callable=deploy_model,
    )

    # Set the task dependencies
    preprocess_task >> train_task >> evaluate_task >> deploy_task
