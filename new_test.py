import os
from dotenv import load_dotenv
import pandas as pd
load_dotenv()

os.environ["KAGGLE_USERNAME"] = os.getenv("KAGGLE_USERNAME")
os.environ["KAGGLE_KEY"] = os.getenv("KAGGLE_KEY")

import kaggle
from kaggle.api.kaggle_api_extended import KaggleApi

api = KaggleApi()

try:
    api.authenticate()
    print("Authentication successful")
except Exception as e:
    print("Authentication failed")
    print(e)


dataset = kaggle.api.dataset_list(search="house prices", file_type="csv")
os.makedirs("metadata", exist_ok=True)
for d in dataset:
    filename = f"metadata/{d.ref.replace('/', '_')}.json"
    metadata = kaggle.api.dataset_metadata(dataset= d.ref, path = filename)

    print(metadata)

print("Datasets found:", len(dataset))
