import os
import platform
import subprocess
import sys
import pandas as pd
import re
from PyQt5 import QtWidgets, uic


class RnaFindGui(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('mainform.ui', self)

        # get components
        self.dbFile = self.findChild(QtWidgets.QLabel, 'rnaFile')
        self.codesEdit = self.findChild(QtWidgets.QTextEdit, 'codesEdit')
        self.searchButton = self.findChild(QtWidgets.QPushButton, 'searchButton')
        self.setFolderButton = self.findChild(QtWidgets.QPushButton, 'setFolderButton')
        self.statusBar = self.findChild(QtWidgets.QStatusBar, 'statusbar')

        # bind events
        self.searchButton.clicked.connect(self.search)
        self.setFolderButton.clicked.connect(self.set_db)

        self.show()

    def set_db(self):
        folder = QtWidgets.QFileDialog()
        # folder.setFileMode(QtWidgets.QFileDialog.DirectoryOnly)
        # folder.setViewMode(QtWidgets.QFileDialog.List)
        # folder.setOptions(QtWidgets.QFileDialog.ShowDirsOnly)
        if folder.exec():
            self.dbFile.setText(folder.selectedFiles()[0])

    def search(self):
        # SCRIPT PARAMETERS
        # sheet_name = 'RNA DATABASE'
        fields = ['!Код', 'Date', 'Comment']
        RESULT_FILE = 'rna_search_result.xlsx'

        target_field = ''
        for i, fld in enumerate(fields):
            if fld.startswith('!'):
                target_field = fld[1:]
                fields[i] = target_field
                break
        if not target_field:
            self.statusBar.showMessage("Critical error. The key field is not specified.")
            return

        # reading request files
        req_data = self.codesEdit.toPlainText().split('\n')

        # reading data from excel as DataFrame
        rna_db = pd.read_excel(self.dbFile.text())

        # find fields in dataframe
        headers = set(rna_db.columns) & set(fields)
        if target_field not in headers:
            self.statusBar.showMessage("Critical error. The key field not found.")
            return
        if len(headers) < len(fields):
            self.statusBar.showMessage('ATTENTION: not all columns were found.')

        # find samples and write result files
        # apply the mask and generate vector
        mask = rna_db[target_field].apply(lambda value: any([bool(re.match(code, value)) for code in req_data]))
        # get values by generated mask
        founded = rna_db[mask]
        # print(founded)

        writer = pd.ExcelWriter(RESULT_FILE, engine='openpyxl')
        founded[headers].to_excel(writer, 'RNA request', index=False)
        writer.save()

        # webbrowser.open_new_tab(RESULT_FILE)
        if platform.system() == 'Windows':
            os.system(f'start {RESULT_FILE}')
        elif platform.system() == 'Linux':
            subprocess.call(['xdg-open', RESULT_FILE])
        else:
            self.statusBar.showMessage('Auto-open is supported only on Windows or Linux platform.')


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    ui = RnaFindGui()
    app.exec_()


