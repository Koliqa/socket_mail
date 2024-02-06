import _thread
import sqlite3
import socket
import select
import os


def readData(connect, decode=True):
    data = '' if decode else b''
    connect.setblocking(False)
    # Можно было сделать условие в одну строку
    # Это не было сделано ради скорости. Во время
    # Передачи большого файла, мы сэкономим много
    # Условий, что ускорит загрузгу на сервер
    if decode:
        while True:
            ready = select.select([connect], [], [], 1)
            if ready[0]:
                readed = connect.recv(1024)
                if not readed:
                    break
                data += readed.decode()
            else:
                break
    else:
        while True:
            ready = select.select([connect], [], [], 1)
            if ready[0]:
                readed = connect.recv(1024)
                if not readed:
                    break
                data += readed
            else:
                break
    connect.setblocking(True)
    return data


def eventHandler(connect, address):
    con = sqlite3.connect('data/mails.db')
    cur = con.cursor()
    # Слежующие два массива нужны, так как на сервер
    # Могут поступить два одинаковых по названию файла,
    # Поэтому массив fileUpload имеет примитивные названия
    # Вроде 0.png, 1.mp3, А массив fileNames имеет
    # Название заданное пользователем
    fileUpload = []
    fileNames = []
    mailNow = 0
    while True:
        try:
            data = readData(connect)
            # В клиенте и на сервере часто фигурирует число 1024
            # Это один килобайт (порции чтения), если файл
            # Может весить > 1 кб, то его отправка происхдит
            # В цикле (например скачивание прикреплённого видео)
        except ConnectionResetError:
            _thread.exit()

        if data:
            data = data.split('>')[:-1]

            # Обработчик запросов {

            if data[0] == 'A':
                phoneNumber = data[1]
                mailAddress = data[2]
                accountPassword = data[3]
                actualMail, actualPassword = '', ''

                sqlRequest = cur.execute("""SELECT * FROM accounts
                                            WHERE phone=?""", (phoneNumber,))
                result = sqlRequest.fetchall()
                if result == []:
                    # Если не зарегестрирован
                    sqlRequest = cur.execute("""SELECT address FROM accounts
                                        WHERE address=?""", (mailAddress,))
                    # И адрес не занят
                    if sqlRequest.fetchall() == []:
                        cur.execute("""INSERT INTO accounts(phone,
                                    address, password)
                                    VALUES(?, ?, ?)""", (phoneNumber,
                                    mailAddress, accountPassword))
                        con.commit()
                        connect.send(mailAddress.encode())
                    else:
                        connect.send(b'reservedAddress')
                else:
                    actualMail, actualPassword = result[0][1], result[0][2]
                    # Если пароль и адрес соответствуют регистрационным данным
                    if actualMail == mailAddress and\
                       actualPassword == accountPassword:
                        connect.send(mailAddress.encode())
                    else:
                        connect.send(b'wrongMailPassword')

            elif data[0] == 'R':  # Remember mail
                clientMail = data[1]
                connect.send(b' ')

            elif data[0] == 'L':  # Чтение входящих писем
                                # Отправитель-Текст письма-Количество файлов-
                                # -Вес файлов
                sqlRequest = cur.execute("""SELECT * FROM mails
                                            WHERE getter = ?""", (clientMail,))
                getterMailIn = sqlRequest.fetchall()  # Для отправки
                if getterMailIn == []:
                    # Нет писем - отправляет пустое письмо
                    # &8& - разделитель (строка без них = "00")
                    connect.send(b'&*&&*&0&*&0')
                else:
                    i = list(getterMailIn[int(data[1])])
                    if i[3] is None:
                        i[3] = ''  # Напоминаю, i[4] это название i[3]
                        i[4] = ''  # С сервера, но для получателя
                    if i[2] is None:
                        i[2] = ''
                    mailNow = int(data[1])

                    fileUpload = []
                    fileNames = []

                    totalWeight = 0
                    for j in i[3].split('&'):
                        totalWeight += os.path.getsize(
                            os.getcwd() + '/data/attachments/' + j)
                    connect.send(str(i[0] + '&*&' +
                                     i[2] + '&*&' +
                                     str(len(i[3].split('&')) - (i[3] == '')) +
                                     '&*&' + str(totalWeight)).encode())
                    for j in i[3].split('&'):
                        if j != '':
                            fileUpload.append(j)
                    for j in i[4].split('&'):
                        if j != '':
                            fileNames.append(j)
                    del i
                connect.send(str(len(getterMailIn)).encode())

            elif data[0] == 'F':  # Передача файла (любого!)
                idx = int(data[1])
                connect.send(fileNames[idx].encode())
                for i in open('data/attachments/' +
                              fileUpload[idx], 'rb'):
                    connect.send(i)
                connect.send(b' ')  # Конец отправки

            elif data[0] == 'C':  # Проверить
                if data[1] == 'M':  # Почту (по БД)
                    sqlRequest = cur.execute("""SELECT address FROM accounts
                                                WHERE address=?""", (data[2],))
                    if sqlRequest.fetchall() == []:
                        connect.send(b'F')
                    else:
                        connect.send(b'T')

            elif data[0] == 'S':
                getterMail = data[1]
                mailText = None if data[2] == '' else data[2]
                filesNumber = int(data[3])
                fileNamesServerTotal = None if filesNumber == 0 else ''
                fileNamesTotal = None if filesNumber == 0 else ''
                connect.send(b' ')
                if filesNumber != 0:
                    for i in range(filesNumber):
                        name = connect.recv(1024).decode().split('/')[-1]
                        fileNamesTotal += name + '&'
                        file = open('data/attachments/' +
                                    str(len(os.listdir('data/attachments/'))) +
                                    '.' +
                                    name.split('.')[1], 'wb')

                        # Можно было сделать цикл (это быстрее)
                        # Но readData надёжнее
                        file.write(readData(connect, False))
                        name = file.name
                        fileNamesServerTotal += name.split('/')[-1] + '&'
                        file.close()
                        connect.send(b' ')
                    fileNamesTotal = fileNamesTotal[:-1]  # Последний &
                    fileNamesServerTotal = fileNamesServerTotal[:-1]
                sqlRequest = cur.execute("""INSERT INTO mails(
                                        sender, getter, text, files, fileNames)
                                        VALUES(?, ?, ?, ?, ?)
                                        """, (clientMail, getterMail,
                                              mailText, fileNamesServerTotal,
                                              fileNamesTotal))
                con.commit()

            # } Обработчик запросов


SETUP = {}
for i in open('data/setup.ini').read().split('\n'):
    SETUP.update({i.split('=')[0]: i.split('=')[1]})

nSocket = socket.socket(
    socket.AF_INET,
    socket.SOCK_STREAM
    )
nSocket.bind((SETUP['address'], int(SETUP['port'])))
nSocket.listen()

while True:
    connect, address = nSocket.accept()
    # ↓ многопоточность
    _thread.start_new_thread(eventHandler, (connect, address))
