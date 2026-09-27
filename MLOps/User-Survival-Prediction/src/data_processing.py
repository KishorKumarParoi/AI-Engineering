import sys
import pandas as pd
from sklearn.model_selection import train_test_split
from imblearn.over_sampling import SMOTE
from src.feature_store import RedisFeatureStore
from src.logger import get_logger
from src.custom_exception import CustomException
from config.paths_config import *

logger = get_logger(__name__)


class DataProcessing:
    def __init__(self, train_data_path , test_data_path , feature_store : RedisFeatureStore):
        self.train_data_path = train_data_path
        self.test_data_path = test_data_path
        self.data=None
        self.test_data = None
        self.X_train = None
        self.X_test = None
        self.y_train=None
        self.y_test = None

        self.X_resampled = None
        self.y_resampled = None

        self.feature_store = feature_store
        logger.info("Your Data Processing is intialized...")
    
    def load_data(self):
        try:
            self.data = pd.read_csv(self.train_data_path)
            self.test_data = pd.read_csv(self.test_data_path)
            logger.info("Read the data sucesfully")
        except Exception as e:
            logger.error(f"Error while reading data {e}")
            raise CustomException(str(e), sys)
    
    def preprocess_data(self):
        try:
            self.data['PassengerId'] = self.data['passenger_id']

            self.data['Age'] = self.data['age'].fillna(self.data['age'].median())

            self.data['Embarked'] = self.data['embarked'].fillna(self.data['embarked'].mode()[0])

            self.data['Fare'] = self.data['fare'].fillna(self.data['fare'].median())

            self.data['Sex'] = self.data['sex'].map({'male': 0, 'female': 1})

            self.data['Embarked'] = self.data['embarked'].astype('category').cat.codes
            self.data['SibSp'] = self.data["sibsp"]
            self.data['Parch'] = self.data['parch']
            self.data["Cabin"] = self.data['cabin']     
            self.data['Pclass'] = self.data['pclass']
            self.data["Ticket"] = self.data["ticket"]
            self.data["Survived"] = self.data["survived"]

            # 1. Family features
            self.data['Familysize'] = self.data['SibSp'] + self.data['Parch'] + 1
            self.data['Isalone'] = (self.data['Familysize'] == 1).astype(int)

            # 2. Cabin feature
            self.data['HasCabin'] = self.data['Cabin'].notna().astype(int)

            # 3. Title feature (use lowercase 'name', handle synonyms, map, and cast to int)
            title_mapping = {
                'Mr': 0,
                'Miss': 1, 'Mlle': 1, 'Ms': 1,
                'Mrs': 2, 'Mme': 2,
                'Master': 3
            }

            self.data['Title'] = (
                self.data['name']
                .str.extract(r' ([A-Za-z]+)\.', expand=False)
                .map(title_mapping)
                .fillna(4)
                .astype(int)
            )

            # 4. Interaction terms
            self.data['Pclass_Fare'] = self.data['Pclass'] * self.data['Fare']
            self.data['Age_Fare'] = self.data['Age'] * self.data['Fare']

            logger.info("Data Preprocessing done...")

        except Exception as e:
            logger.error(f"Error while preprocessing data {e}")
            raise CustomException(str(e), sys)
    
    def handle_imbalance_data(self):
        try:
            X = self.data[['Pclass', 'Sex', 'Age', 'Fare', 'Embarked', 'Familysize', 'Isalone', 'HasCabin', 'Title', 'Pclass_Fare', 'Age_Fare']]
            y = self.data['Survived']

            smote = SMOTE(random_state=42)

            self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(X, y, test_size=0.2, random_state=42)

            self.X_train_resampled, self.y_train_resampled = smote.fit_resample(self.X_train, self.y_train)


            logger.info("Handled imbalance data successfully...")

        except Exception as e:
            logger.error(f"Error while imabalanced handling data {e}")
            raise CustomException(str(e), sys)
    
    def store_feature_in_redis(self):
        try:
            batch_data = {}
            for idx,row in self.data.iterrows():
                entity_id = row.get("PassengerId", row.get("passenger_id", idx))
                features = {
                    "Age" : row['Age'],
                    "Fare" : row["Fare"],
                    "Pclass" : row["Pclass"],
                    "Sex" : row["Sex"],
                    "Embarked" : row["Embarked"],
                    "Familysize": row["Familysize"],
                    "Isalone" : row["Isalone"],
                    "HasCabin" : row["HasCabin"],
                    "Title" : row["Title"],
                    "Pclass_Fare" : row["Pclass_Fare"],
                    "Age_Fare" : row["Age_Fare"],
                    "Survived" : row["Survived"]
                }
                batch_data[entity_id] = features
            self.feature_store.store_batch_features(batch_data)
            logger.info("Data has been feeded into Feature Store..")
        except Exception as e:
            logger.error(f"Error while feature storing data {e}")
            raise CustomException(str(e), sys)
        
    def retrive_feature_redis_store(self,entity_id):
        features = self.feature_store.get_features(entity_id)
        if features:
            return features
        return None
    
    def run(self):
        try:
            logger.info("Starting our Data Processing Pipleine...")
            self.load_data()
            self.preprocess_data()
            self.handle_imbalance_data()
            self.store_feature_in_redis()

            logger.info("End of pipeline Data Processing...")

        except Exception as e:
            logger.error(f"Error while Data Processing Pipleine {e}")
            raise CustomException(str(e), sys)
        
if __name__=="__main__":
    feature_store = RedisFeatureStore()

    data_processor = DataProcessing(TRAIN_PATH,TEST_PATH,feature_store)
    data_processor.run()

    print(data_processor.retrive_feature_redis_store(entity_id=332))
        


