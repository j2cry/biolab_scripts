import pandas as pd
import numpy as np
from re import findall

CURRENTS_PATH = 'test.xlsx'
CODE_REGEX = r'(^\D{,3}\d{,7}\D\w*)'


# def parse_code(x):
#     if isinstance(x, str) and (code := findall(r'(\D{,3}\d{,7}\D\w*)', x)):
#         return code[0]
#     return np.nan


df = pd.read_excel(CURRENTS_PATH)

# code = df.applymap(parse_code)
print(df.stack().str.match(CODE_REGEX))


