from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5 import uic
import sys
import os
from data.code.totalFunc import *


SETUP = {}
for i in open('data/setup.ini').read().split('\n'):
    SETUP.update({i.split('=')[0]: i.split('=')[1]})

CONNECT = socket.socket(
    socket.AF_INET,
    socket.SOCK_STREAM
    )
CONNECT.connect((SETUP['address'], int(SETUP['port'])))

send = Sender(CONNECT).send  # Sender импортирован из data.code.totalFunc
read = Sender(CONNECT).read  # Как и autorize

mail = autorize(CONNECT)
if mail[:2] != 'M_':  # Сообщение об ошибке
    print(mail)
    input()
    exit()
mail = mail[2:]


class CWidget(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('data/design/main.ui', self)
        send('R')
        send(mail)

        read()

        self.mailNumber = 0
        self.changeMail()  # Обновляем сообщения

        self.buttonNext.clicked.connect(self.nextMail)
        self.buttonBack.clicked.connect(self.previousMail)
        self.buttonDownloadFiles.clicked.connect(self.downloadAttachments)
        self.saveText.clicked.connect(self.downloadMail)
        self.buttonWrite.clicked.connect(self.writeMail)

    def changeMail(self, number=0):
        self.changeData(number)
        self.labelFrom.setText('От: ' + self.data[0])
        self.textInMail.setPlainText(self.data[1])

        if self.data[3] != '':
            weight = str(int(self.data[3]) // 1024) + 'KB | ' +\
                     str(int(self.data[3]) // 1048576) + 'MB'
            self.labelWeight.setText('Вес: ' + weight)
        else:
            self.labelWeight.setText('Вес:')

        self.saveText.setEnabled(self.data[1] != '')
        self.buttonDownloadFiles.setEnabled(self.data[2] != '0')
        self.buttonDownloadFiles.setText(
            'Скачать\nприкреплённые\nфайлы')

    def nextMail(self):
        if self.mailNumber + 1 < self.messages:
            self.mailNumber += 1
            self.changeMail(self.mailNumber)

    def previousMail(self):
        if self.mailNumber - 1 >= 0:
            self.mailNumber -= 1
            self.changeMail(self.mailNumber)

    def changeData(self, number=0):
        send('L>' + str(number))
        self.data = read().split('&*&')
        self.messages = int(read())

    def downloadAttachments(self):
        self.buttonDownloadFiles.setText(
            'Файлы в папке\n"Прикреплённые\nфайлы"')
        self.buttonDownloadFiles.setEnabled(False)
        for i in range(int(self.data[2])):
            send('F')
            send(str(i))

            newFile = open('Прикреплённые файлы\\' + read(), 'wb')

            data = read(False)  # Не декодировать (записывать байты)
            while data != b' ':
                newFile.write(data)
                data = read(False)

            newFile.close()

        del newFile, data

    def downloadMail(self):
        newFile = open(f'Письма/mail{len(os.listdir("Письма/"))}.txt', 'w')
        newFile.write(self.data[1])
        newFile.close()
        self.saveText.setEnabled(False)

    def writeMail(self):
        # Запуск файла клиента отправки
        os.system(f'python "{os.getcwd()}\\data\\code\\write.py"')


if __name__ == '__main__':
    app = QApplication(sys.argv)

    widget = CWidget()
    widget.show()

    exit(app.exec_())
