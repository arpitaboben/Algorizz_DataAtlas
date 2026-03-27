import os
from dotenv import load_dotenv



load_dotenv()


username = os.getenv("KAGGLE_USERNAME")
key = os.getenv("KAGGLE_KEY")

#print("KAGGLE_USERNAME:", username)
#print("KAGGLE_KEY:", key)


os.environ["KAGGLE_USERNAME"] = username
os.environ["KAGGLE_KEY"] = key


api = KaggleApi()
api.authenticate()

print("Kaggle API connected successfully")