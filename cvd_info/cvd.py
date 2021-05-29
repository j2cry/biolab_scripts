"""
    Script for automated data acquisition for covid-19 from the EMIAS system for medical institutions.

    HOW TO USE:
        1) setup your EMIAS login and password below
        2) create file 'cvreq.txt'
        3) type inside surname [name] [patronymic]: 1 row per patient, for example:
                Petrov
                Nikolaev Alexandr
                Shetinina Valentina Vladimirovna
        4) run script
            NOTE, that it's recommended to have Python 3.7 or higher, installed modules: requests, pandas, openpyxl
        5) get result in covid.xlsx
"""

import requests
from cvd_parse import URL_LOG, URL_TABLE, REQUEST_HEADER, REQUEST_AUTH, REQUEST_DATA, PatientsInfo, PatientName

req_file = 'cvreq.txt'

# loading and parsing request info
req_patients = []
with open(req_file, 'r') as file:
    pat = file.readline()
    while pat:
        pname = PatientName(*pat.split())
        req_patients.append(pname)
        pat = file.readline()

# start up session
session = requests.Session()
request_body = {**REQUEST_HEADER, **REQUEST_AUTH}
post_request = session.post(URL_LOG, json=request_body)

if post_request.status_code != 200:
    exit(f'Error! Response code {post_request.status_code}')
print('Logging OK')

# authorization
response = post_request.json()
token = response.get('token')
REQUEST_HEADER.update({'Authorization': f'Bearer {token}'})

# getting data
info = PatientsInfo()
for pat in req_patients:
    # generating POST body
    user_info = {'surname': pat.surname, 'name': pat.name, 'patronymic': pat.patronymic}
    request_body = {**REQUEST_DATA, **user_info}
    # sending POST
    post_request = session.post(URL_TABLE, headers=REQUEST_HEADER, json=request_body)

    if post_request.status_code != 200:
        print(f'POST ERROR! CODE: {post_request.status_code}')
        print(**user_info)
        continue
    response = post_request.json()

    # parsing RESPONSE
    for elem in response:
        info.update(elem)

info.make_frame()

