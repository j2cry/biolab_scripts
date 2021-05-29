from collections import defaultdict, namedtuple
from datetime import date
import hashlib
import pandas as pd

headers = ['Full name', 'Birthday', 'Direction type', 'Received date', 'Sample type', 'Result']
EXCEL_FILE = 'covid.xlsx'
EXCEL_SHEET = 'COVID-19 INFO'

PatientName = namedtuple('PatientName', 'surname name patronymic', defaults=('', '', ''))
AnalysisResult = namedtuple('AnalysisResult', 'date direction type result')

URL_LOG = 'https://materials.mosmedzdrav.ru/api/auth/login'
URL_TABLE = 'https://materials.mosmedzdrav.ru/api/main/getTable'

USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.190 Safari/537.36'
# host = 'materials.mosmedzdrav.ru'
# origin = 'https://materials.mosmedzdrav.ru'
REFERER = 'https://materials.mosmedzdrav.ru/corona/auth/'

LOGIN = 'type your login here'              # LOGIN
PASSWD = 'type your password here'        # PASSWORD

REQUEST_HEADER = {
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
    'Referer': REFERER,
    # 'sec-ch-ua': '"Chromium";v="88", "Google Chrome";v="88", ";Not A Brand";v="99" ',
    # 'sec-ch-ua-mobile': '?0',
    # 'Sec-Fetch-Dest': 'empty',
    # 'Sec-Fetch-Mode': 'cors',
    # 'Sec-Fetch-Site': 'same-origin',
    'User-Agent': USER_AGENT,
}

REQUEST_AUTH = {
    'login': LOGIN,
    'password': PASSWD
}

REQUEST_DATA = {
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


class PatientsInfo:
    def __init__(self):
        self.data = defaultdict()

    @staticmethod
    def parse(pat):
        """ Response parsing. Returns dict needed data from pat.
            pat is a result of post-request """
        if not pat:
            pass

        patient = defaultdict()
        surname = pat.get('surname')
        name = pat.get('name')
        patronymic = pat.get('patronymic')
        birthday = date.fromisoformat(pat.get('birth_dt')).strftime('%d.%m.%Y')
        # set id
        src = f'{surname}{name}{patronymic}{birthday}'
        patient['pat_id'] = int(hashlib.md5(src.encode('utf-8')).hexdigest(), 16)

        patient['Full name'] = f"{surname.title()} {name.title()} {patronymic.title()}"
        patient['Birthday'] = birthday
        patient['Direction type'] = [pat.get('direction_type_name')]  # тип направления
        patient['Received date'] = []
        patient['Sample type'] = []
        patient['Result'] = []

        # analyses
        samples = pat.get('person_table_samples')  # в этом list исходно всегда только 1 значение
        if not samples:
            return patient  # NOTE: возвращаем dict без результата анализов

        for smp in samples:
            patient['Sample type'].append(smp.get('samples_type'))
            patient['Received date'].append(date.fromisoformat(smp.get('get_date')).strftime('%d.%m.%Y'))

            result = smp.get('samples_result')  # общий результат. None если есть результат с антителами

            # get antibodies titer
            analyzes_results = smp.get('person_table_sample_results')  # таблица с результатами на антитела
            antibodies = ''
            if analyzes_results:
                for anl_res in analyzes_results:
                    antibodies += f"{anl_res.get('result_type_name')}: " \
                        f"{anl_res.get('result_value')} (< {anl_res.get('max_value')}) "
            # исходно для результата используется два поля: `samples_result` и `person_table_sample_results`
            # переводим к одному, ибо они взаимоисключающие (по состоянию на 10.03.2021)
            patient['Result'].append(result if result else antibodies)
        return patient

    def update(self, pat: dict, forced=False):
        """ Update patient's data and analysis results
            Set forced = True, if it is required to rewrite data """
        pat = self.parse(pat)
        pat_id = pat.get('pat_id')
        if not pat_id:
            return

        # если такой пат уже есть, то надо просто append к нему результаты парсинга
        # и никакой проверки корректности значений!
        if (pat_id in self.data.keys()) and not forced:
            self.data[pat_id]['Direction type'].extend(pat.get('Direction type'))
            self.data[pat_id]['Received date'].extend(pat.get('Received date'))
            self.data[pat_id]['Sample type'].extend(pat.get('Sample type'))
            self.data[pat_id]['Result'].extend(pat.get('Result'))
        else:
            self.data[pat_id] = pat

    def make_frame(self):
        """ Returns DataFrame with analysis result """
        res_df = pd.DataFrame()
        for pat in self.data.values():
            res_df = res_df.append(pd.DataFrame(pat))

        writer = pd.ExcelWriter(EXCEL_FILE, engine='openpyxl')
        res_df[headers].to_excel(writer, EXCEL_SHEET, index=False)

        worksheet = writer.sheets[EXCEL_SHEET]  # pull worksheet object
        dims = {}
        for row in worksheet.rows:
            for cell in row:
                if cell.value:
                    dims[cell.column_letter] = max((dims.get(cell.column_letter, 0), len(str(cell.value))))
        for col, value in dims.items():
            worksheet.column_dimensions[col].width = value + 2

        writer.save()
