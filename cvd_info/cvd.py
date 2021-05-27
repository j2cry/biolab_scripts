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
from cvd_parse import PatientsInfo, PatientName

req_file = 'cvreq.txt'
log_url = 'https://materials.mosmedzdrav.ru/api/auth/login'
table_url = 'https://materials.mosmedzdrav.ru/api/main/getTable'

user_agent = 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.190 Safari/537.36'
host = 'materials.mosmedzdrav.ru'
origin = 'https://materials.mosmedzdrav.ru'
referer = 'https://materials.mosmedzdrav.ru/corona/auth/'

login = 'type your login here'              # LOGIN
password = 'type your password here'        # PASSWORD

request_header = {
    # 'Accept': '*/*',
    # 'Accept-Encoding': 'gzip, deflate, br',
    # 'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
    # 'Authorization': 'Bearer',
    # 'Connection': 'keep-alive',
    # 'Content-Length': 26 + len(login) + len(password),     # 26 + len(login) + len(password)
    # 'Content-Type': 'application/json',
    # 'Cookie': 'cookie',
    # 'Host': host,
    # 'Origin': origin,
    'Referer': referer,
    # 'sec-ch-ua': '"Chromium";v="88", "Google Chrome";v="88", ";Not A Brand";v="99" ',
    # 'sec-ch-ua-mobile': '?0',
    # 'Sec-Fetch-Dest': 'empty',
    # 'Sec-Fetch-Mode': 'cors',
    # 'Sec-Fetch-Site': 'same-origin',
    'User-Agent': user_agent,
}

request_auth = {
    'login': login,
    'password': password
}

request_info = {
    "all_mo": None,
    "birth_dt": "",
    "direction_number": "",
    "direction_status_id": -1,
    "get_date_at": "",
    "is_lab_number": False,
    "is_view_not_approve": False,
    "is_wait_approve": False,
    "laboratory_id": -1,
    "limit": 10,
    "mu_id": 1109,
    "name": "",                     # ИМЯ
    "offset": 0,
    "patronymic": "",               # ОТЧЕСТВО
    "receive_date_at": "",
    "result_date_at": "",
    "samples_result_id": -1,
    "samples_status_id": -1,
    "send_date_at": "",
    "send_laboratory_id": -1,
    "spec_samples_number": "",
    "surname": "",                  # ФАМИЛИЯ
    "direction_type_id": -1,
    "source_id": -1,
    "employer_id": None,
    "direction_category_id": -1,
    "symptom_orvi": None,
    "is_deleted": False,
    "is_mo_reestr_create": False,
    "is_ref_reestr": False,
    "mkb_id": -1,
    "min_direction_id": None
}


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
request_body = {**request_header, **request_auth}
post_request = session.post(log_url, json=request_body)

if post_request.status_code != 200:
    exit(f'Error! Response code {post_request.status_code}')
print('Logging OK')

# authorization
response = post_request.json()
token = response.get('token')
request_header.update({'Authorization': f'Bearer {token}'})

# getting data
info = PatientsInfo()
for pat in req_patients:
    # generating POST body
    user_info = {'surname': pat.surname, 'name': pat.name, 'patronymic': pat.patronymic}
    request_body = {**request_info, **user_info}
    # sending POST
    post_request = session.post(table_url, headers=request_header, json=request_body)

    if post_request.status_code != 200:
        print(f'POST ERROR! CODE: {post_request.status_code}')
        print(**user_info)
        continue
    response = post_request.json()

    # parsing RESPONSE
    for elem in response:
        info.update(elem)

info.make_frame()

