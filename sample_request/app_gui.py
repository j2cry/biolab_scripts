import sys
import os
from PyQt5 import QtWidgets, uic
from pathlib import Path
import jaydebeapi
from datetime import datetime

PATH_CWD = Path().cwd()
PATH_UI = Path(PATH_CWD, 'ui', 'mainform.ui')

PATH_MDB = r'path to MDB file'
driver_path = Path(PATH_CWD, 'ucanaccess')
driver_jars = [str(Path(path).joinpath(file))
               for path, subdirs, files in os.walk(driver_path)
               for file in files if file.endswith('jar')]


class AppGui(QtWidgets.QMainWindow):
    def __init__(self):
        super(AppGui, self).__init__()
        uic.loadUi(PATH_UI, self)

        # initialize MDB connection
        self.mdb_conn = jaydebeapi.connect("net.ucanaccess.jdbc.UcanaccessDriver",
                                           f"jdbc:ucanaccess://{PATH_MDB};memory=false;",
                                           ["", ""], driver_jars)
        self.mdb = self.mdb_conn.cursor()
        self.statusbar = self.findChild(QtWidgets.QStatusBar, 'statusbar')
        # bind events
        self.requestButton.clicked.connect(self.request)

        self.show()

    def request(self):
        req_data = self.requestEdit.toPlainText().split('\n')
        response = []
        for row in req_data:
            self.mdb.execute('SELECT surname, in1, in2, sex, age '
                             'FROM tblmain_Data '
                             'WHERE tube = ? OR hist_no = ?',
                             parameters=(row, row))
            if self.mdb.fetchall():
                response.append(f'{row}: matches found!')
            else:
                response.append(f'{row}')
        self.requestEdit.setText('\n'.join(response))
        self.statusbar.showMessage(f"Finished at {datetime.now()}")

    def closeEvent(self, event):
        self.mdb.close()
        self.mdb_conn.close()


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    ui = AppGui()
    app.exec_()
