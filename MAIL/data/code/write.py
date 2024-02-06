from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5 import uic
import sys
import os
import socket
from totalFunc import *

SETUP = {}
for i in open('data/setup.ini').read().split('\n'):
    SETUP.update({i.split('=')[0]: i.split('=')[1]})

CONNECT = socket.socket(

    socket.AF_INET,
    socket.SOCK_STREAM

    )
CONNECT.connect((SETUP['address'], int(SETUP['port'])))

exit = Sender(CONNECT).exit  # Отправиить / получить данные
send = Sender(CONNECT).send  # Sender импортирован из data.code.totalFunc
read = Sender(CONNECT).read  # Как и autorize

mail = autorize(CONNECT, open('data/autorize.ini').read(
    ).split('\n'))[2:]


class CWidget(QMainWindow):
    def __init__(self):
        super().__init__()

        self.dataRoot = rootReturn()
        uic.loadUi('data/design/send.ui', self)

        send('R')
        send(mail)

        read()

        self.buttonSend.clicked.connect(self.sendMail)

    def sendMail(self):
        self.labelError.setText(self.parseError())
        if self.labelError.text() != 'OK':
            return
        self.addFiles.setText(self.addFiles.text().replace('\\', '/'))
        send('S')
        send(self.sendTo.text())
        send(self.textMailEdit.toPlainText())
        send(str(len(self.addFiles.text().split('&'))))

        read()
        if self.addFiles.text() != '':
            for i in self.addFiles.text().split('&'):
                CONNECT.send(i.encode())
                for j in open(i, 'rb'):
                    CONNECT.send(j)
                read()

    def parseError(self):
        if self.addFiles.text() == self.textMailEdit.toPlainText() == '':
            return 'Ничего не отправлено'
        if self.textMailEdit.toPlainText() != '':
            if len(self.textMailEdit.toPlainText()) > 2000:
                return 'Слишком много символов в присьме (> 2000)'
            if '>' in self.textMailEdit.toPlainText() or\
               '&*&' in self.textMailEdit.toPlainText():
                return 'В письме использованны символы ">" или "&*&"'
            if len(self.addFiles.text().split('&')) > 10:
                return 'Нельзя отправлять больше десяти файлов'
        if self.addFiles.text() != '':
            for i in self.addFiles.text().split('&'):
                try:
                    open(i)
                except:
                    return f'Файл {i} не сущевствует'
        if self.sendTo.text() == '':
            return 'Такого получателя нет'
        send('C')
        send('M')
        send(self.sendTo.text())
        if read() == 'F':
            return 'Такого получателя нет'
        return 'OK'


if __name__ == '__main__':
    app = QApplication(sys.argv)

    widget = CWidget()
    widget.show()

    sys.exit(app.exec_())
