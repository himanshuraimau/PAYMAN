import pandas as pd
import numpy as np
from dotenv import load_dotenv
import os
import requests 

PAYMAN_API_KEY = os.getenv("PAYMAN_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

data = pd.read_csv('data.csv')

commission_earned = data['Commission Earned']


