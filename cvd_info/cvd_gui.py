import sys
import os
from PyQt5 import QtWidgets, uic
import requests
import platform
import subprocess
from cvd_parse import URL_LOG, URL_TABLE, REQUEST_HEADER, REQUEST_AUTH, REQUEST_DATA, EXCEL_FILE,\
    PatientsInfo, PatientName


class CvdGui(QtWidgets.QMainWindow):
    def __init__(self):
        super(CvdGui, self).__init__()
        uic.loadUi('mainform.ui', self)

        self.statusBar = self.findChild(QtWidgets.QStatusBar, 'statusBar')
        self.requestButton = self.findChild(QtWidgets.QPushButton, 'requestButton')

        self.requestButton.clicked.connect(self.request)
        self.show()

    def request(self):
        # split patient to surname, name, patronymic
        req_patients = [PatientName(*pat.split()) for pat in self.patients.toPlainText().split('\n')]

        # start up session
        session = requests.Session()
        request_body = {**REQUEST_HEADER, **REQUEST_AUTH}
        post_request = session.post(URL_LOG, json=request_body)

        if (err_code := post_request.status_code) != 200:
            self.statusBar.showMessage(f'Connection cannot be established! Error {err_code}.')
            return
        self.statusBar.showMessage('Logging OK')

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

        if info.has_data:
            info.make_frame()
            if platform.system() == 'Windows':
                os.system(f'start {EXCEL_FILE}')
            elif platform.system() == 'Linux':
                subprocess.call(['xdg-open', EXCEL_FILE])
            else:
                self.statusBar.showMessage('Auto-open is supported only on Windows or Linux platform.')
        else:
            self.statusBar.showMessage('Nothing found!')


app = QtWidgets.QApplication(sys.argv)
window = CvdGui()
app.exec_()
