import numpy as np
import pandas as pd
import pathlib
import os
import re

DATA_PATH = r'\\DC1-MOSCOW\Proteogenex\Working\qc complete'
estimates = {8: 5, 7: 4, 5: 3, 3: 2}


def get_value(x):
    if isinstance(x, str):
        # res = re.findall(r'(\d\.?\d*)', x)
        if found := re.findall(r'(\d\.?\d*)', x):
            return float(found[0])
        else:
            return np.nan
    elif np.isreal(x):
        return float(x)

    return np.nan


def repair_estimate(rin):
    if rin >= 8:
        return 5
    if rin >= 7:
        return 4
    if rin >= 5:
        return 3
    if rin >= 2.5:
        return 2
    return 0


excel_files = [str(pathlib.Path(path).joinpath(file))
               for path, sub_dirs, files in os.walk(DATA_PATH)
               for file in files if file.endswith('xls') or file.endswith('xlsx')]

# print(*excel_files, sep='\n')
print(f'Total {len(excel_files)} files found.')

target_cols = {'Код', 'Тип', 'Поставщик', 'Оценка', 'RIN'}
dataset = pd.DataFrame(columns=target_cols)

# collect dataset
for f in excel_files:
    # collect existing column names
    print(f'Reading file "{f}"...', end='')
    df = pd.read_excel(f, engine=None)
    existing_cols = target_cols & set(df.columns)

    # correct estimate column
    if 'Оценка' not in existing_cols:
        if 'Оценки' in df.columns:
            df.rename(columns={'Оценки': 'Оценка'}, inplace=True)
        elif 'оценки' in df.columns:
            df.rename(columns={'оценки': 'Оценка'}, inplace=True)
        elif 'оценка' in df.columns:
            df.rename(columns={'оценка': 'Оценка'}, inplace=True)
    existing_cols.add('Оценка')
    df['Оценка'] = df['Оценка'].apply(get_value)

    # get RIN value
    if 'RIN' in existing_cols:
        df['RIN'] = df['RIN'].apply(get_value)

    # concat to main dataset
    dataset = pd.concat((dataset, df[existing_cols]), axis=0)
    print('done.')

# re-index
dataset.reset_index(drop=True, inplace=True)
# rename columns
dataset.rename(columns={'Оценка': 'estimate', 'Код': 'code', 'Поставщик': 'provider', 'Тип': 'type'},
               inplace=True)

# drop non-valid rows
out_estimate = dataset['estimate'].isna() # | (dataset['estimate'] == 0)
out_rin = dataset['RIN'].isna()
out_code = dataset['code'].isna()
dataset.drop(dataset[out_code | (out_estimate & out_rin)].index, inplace=True)

# repair estimate according to rin
out_estimate = dataset['estimate'].isna()
dataset.loc[out_estimate, 'estimate'] = dataset.loc[out_estimate, 'RIN'].apply(repair_estimate)

# add localization column
dataset['loc'] = dataset['code'].apply(lambda x: str(x)[:2])

print('Saving collected dataset...', end='')
# For excel
# dataset.to_csv('dataset.csv', sep=';', encoding='utf-8-sig')
dataset.to_csv('dataset.csv', sep=';', index=False, encoding='utf-8-sig')
print('done.')
