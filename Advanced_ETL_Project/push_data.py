import os
import sys
import json

from dotenv import load_dotenv
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
print(MONGO_URI)

import certifi 

ca = certifi.where()

import pandas as pd
import numpy as np
import pymongo

from networksecurity.exception.network_security_exception import NetworkSecurityException
from networksecurity.logging.logger import logging

class NetworkDataExtract():
    def __init__(self):
        try:
            # self.mongo_client = pymongo.MongoClient(MONGO_URI, tlsCAFile=ca)
            # logging.info("MongoDB connection successful")
            pass
        except Exception as e:
            raise NetworkSecurityException(e, sys)

    def cv_to_json_convertor(self, file_path):
        try:
            data = pd.read_csv(file_path)
            data.reset_index(drop=True, inplace=True)
            records = list(json.loads(data.T.to_json()).values())
            return records
        except Exception as e:
            raise NetworkSecurityException(e, sys)
    def insert_data_mongodb(self,database,collection,records):
        try:
            self.database=database
            self.collection=collection
            self.records=records

            self.mongo_client=pymongo.MongoClient(MONGO_URI, tlsCAFile=ca)
            self.database = self.mongo_client[self.database]
            self.collection=self.database[self.collection]
            self.collection.insert_many(self.records)
            return(len(self.records))
        except Exception as e:
            raise NetworkSecurityException(e,sys)
            
if __name__ == '__main__':
    FILE_PATH = "Network_Data/phisingData.csv"
    DATABASE = "NetworkSecurity"
    COLLECTION = "NetworkData"
    networkobj = NetworkDataExtract()
    records = networkobj.cv_to_json_convertor(file_path=FILE_PATH)
    no_of_records = networkobj.insert_data_mongodb(database=DATABASE, collection=COLLECTION, records=records)
    print(no_of_records)    