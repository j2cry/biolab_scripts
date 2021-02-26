""" Script for searching RNA samples in excel file
    install pandas openpyxl ?xlrd"""

# Command for debug in terminal
# rna_find.py -rf materials -db materials/RNA database.xls

import os
import pandas as pd
import argparse
from collections import defaultdict
from pathlib import Path
import re

# Еще можно сделать вывод log.txt при возникновении ошибок

# parsing arguments
parser = argparse.ArgumentParser()
parser.add_argument('-p', help='request files prefix ("request_" as default)')
parser.add_argument('-e', help='request files extension (.txt as default)')
parser.add_argument('-rf', help='folder with request files (current dir as default)')
parser.add_argument('-db', help='path to excel file with your data ("RNA database.xls" in current dir as default)')
parser.add_argument('-s', help='sheet name in excel file ("RNA DATABASE" as default)')
parser.add_argument('-f', nargs='*', help="searching fields. The key field must be marked with '!' before its name.\n"
                                          "['!Код', 'Дата', 'Comment'] as default.")
args = parser.parse_args()

# =============== user settings ===============
prefix = args.p if args.p else 'request_'
extension = args.e if args.e else '.txt'
req_folder = Path(args.rf) if args.rf else Path()
db_file = Path(args.db) if args.db else Path('RNA database.xls')
sheet_name = args.s if args.s else 'RNA DATABASE'
# список полей, сохраняемых из db при нахождении совпадений. Ключевое поле обозначается как ! перед именем
fields = args.f if args.f else ['!Код', 'Date', 'Comment']
# =============================================
# print(prefix, extension, req_folder, db_file, sheet_name, fields)

# calculating other settings
target_field = ''
for i, fld in enumerate(fields):
    if fld.startswith('!'):
        target_field = fld[1:]
        fields[i] = target_field
        break
if not target_field:
    exit("Critical error. The key field is not specified.")


# reading request files
req_data = defaultdict(list)        # project: list of samples
request_filenames = [fn for fn in os.listdir(req_folder) if fn.startswith(prefix) and fn.endswith(extension)]
for filename in request_filenames:
    with open(req_folder / filename, 'r', encoding='utf-8') as file:
        project = filename.replace(prefix, '').replace(extension, '')
        sample = file.readline().rstrip()
        while sample:
            req_data[project].append(re.split(r'\(', sample)[0])
            sample = file.readline().rstrip()


# reading data from excel as DataFrame
workbook = pd.ExcelFile(db_file)
rna_db = workbook.parse(sheet_name)
workbook.close()


# find fields in dataframe
headers = set(rna_db.columns) & set(fields)
if target_field not in headers:
    exit("Critical error. The key field not found.")
if len(headers) < len(fields):
    print('ATTENTION: not all columns were found.')


# find samples and write result files
for project, codes in req_data.items():
    # старый способ - проверяет только абсолютное совпадение
    # founded = rna_db.loc[rna_db[target_field].isin(codes)]

    # новый способ - проверяет вхождение с начала
    founded = pd.DataFrame()
    for code in codes:
        founded = pd.concat([rna_db.loc[rna_db[target_field].str.startswith(code)], founded])

    writer = pd.ExcelWriter(req_folder / (project + '.xlsx'), engine='openpyxl')
    founded[headers].to_excel(writer, 'RNA request')
    writer.save()
