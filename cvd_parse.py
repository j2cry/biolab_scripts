from collections import defaultdict, namedtuple
from datetime import date
import hashlib
import pandas as pd

headers = ['Full name', 'Birthday', 'Direction type', 'Received date', 'Sample type', 'Result']
exl_filename = 'covid.xlsx'
exl_sheet_name = 'COVID-19 INFO'

PatientName = namedtuple('PatientName', 'surname name patronymic', defaults=('', '', ''))
AnalysisResult = namedtuple('AnalysisResult', 'date direction type result')


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

        writer = pd.ExcelWriter(exl_filename, engine='openpyxl')
        res_df[headers].to_excel(writer, exl_sheet_name, index=False)

        worksheet = writer.sheets[exl_sheet_name]  # pull worksheet object
        dims = {}
        for row in worksheet.rows:
            for cell in row:
                if cell.value:
                    dims[cell.column_letter] = max((dims.get(cell.column_letter, 0), len(str(cell.value))))
        for col, value in dims.items():
            worksheet.column_dimensions[col].width = value + 2

        writer.save()
