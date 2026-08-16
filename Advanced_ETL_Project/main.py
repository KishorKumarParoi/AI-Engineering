from networksecurity.entity.config_entity import TrainingPipelineConfig, DataIngestionConfig
from networksecurity.components.data_ingestion import DataIngestion
from networksecurity.logging.logger import logging
from networksecurity.exception.network_security_exception import NetworkSecurityException
import sys 

def main():
    print("Hello from advanced-etl-project!")

    try:
        trainingpipelineconfig=TrainingPipelineConfig()
        dataingestionconfig=DataIngestionConfig(trainingpipelineconfig)
        data_ingestion=DataIngestion(dataingestionconfig)
        logging.info("Initiate the data ingestion")
        dataingestionartifact=data_ingestion.initiate_data_ingestion()
        logging.info("Data Initiation Completed")
        print(dataingestionartifact)
    except Exception as e:
           raise NetworkSecurityException(e,sys)


if __name__ == "__main__":
    main()
