import socket
import os


def rootReturn(stopWord='data'):
    root = ''  # Идём в каталог stopWord
    for i in os.getcwd().split('\\'):
        root += i + '/'
        if i == stopWord:
            break
    return root


class Sender():
    def __init__(self, connect):
        self.connect = connect

    def send(self, data, encode=True):
        self.connect.send(data.encode() + b'>' if encode else data)

    def exit(self, arg=None):
        self.send('%')
        self.read()

    def read(self, decode=True):
        return self.connect.recv(1024).decode() if decode else\
               self.connect.recv(1024)


def autorize(connect, auto=False):
    send = Sender(connect).send

    phoneCode = {'+7': '8'}
    autorizeErrorsCode = {'badPhoneNumber': 'Некорректный номер телефона.',
                          'badMailAddress': 'Некорректный почтовый адрес.',
                          'badPassword': 'Некорректный пароль.',
                          'wrongMailPassword': 'Неверный пароль/почта.',
                          'reservedAddress': 'Адрес занят.'}

    print('Система автоматически зарегистрирует вас, если это не сделано.')

    if auto:
        phoneNumber, mailAddress, accountPassword = auto
    else:
        phoneNumber = input('Введите номер телефона >> ')
        mailAddress = input('Введите почтовый адрес >> ')
        accountPassword = input('Введите пароль >> ')

    if len(phoneNumber) < 11:  # Избегаю IndexError
        return autorizeErrorsCode['badPhoneNumber']

    if phoneNumber[0] == '+':
        if phoneNumber[:2] not in phoneCode.keys():
            return autorizeErrorsCode['badPhoneNumber']
        phoneNumber = phoneCode[phoneNumber[:2]] + phoneNumber[2:]

    parsedPhoneNumber = ''
    totalBrackets = 0
    lastDeffis = False

    for i in phoneNumber:
        if i == '(':
            totalBrackets += 1
        elif i == ')':
            totalBrackets -= 1
        elif i == '-':
            if lastDeffis:
                return autorizeErrorsCode['badPhoneNumber']
            lastDeffis = True
        elif i not in '0123456789':
            return autorizeErrorsCode['badPhoneNumber']
        else:
            lastDeffis = False
            parsedPhoneNumber += i

    if totalBrackets != 0 or lastDeffis:
        return autorizeErrorsCode['badPhoneNumber']

    phoneNumber = parsedPhoneNumber
    del parsedPhoneNumber, totalBrackets

    if len(phoneNumber) != 11:  # Проверка для "чистого" номера
        return autorizeErrorsCode['badPhoneNumber']

    if '@' not in mailAddress or '.' not in mailAddress:
        return autorizeErrorsCode['badMailAddress']
    if mailAddress.index('.') - mailAddress.index('@') < 2 or\
       mailAddress.index('@') == 0 or\
       mailAddress.index('.') == len(mailAddress) - 1 or\
       len(mailAddress.split('@')) != 2 or\
       len(mailAddress.split('.')) != 2:
        return autorizeErrorsCode['badMailAddress']

    word = False
    for i in mailAddress:
        if i.lower() not in 'abcdefghijklmnopqrstuvwxyz0123456789_@.':
            return autorizeErrorsCode['badMailAddress']
        if i.lower() in 'abcdefghijklmnopqrstuvwxyz':
            word = True

    if len(accountPassword) < 8:
        return autorizeErrorsCode['badPassword']

    lowLit, highLit = False, False
    otherSymbol = False
    for i in accountPassword:
        if i in '0123456789_':
            otherSymbol = True
        elif i == i.lower():
            if i in 'abcdefghijklmnopqrstuvwxyz':
                lowLit = True
            else:
                return autorizeErrorsCode['badPassword']
        elif i.lower() in 'abcdefghijklmnopqrstuvwxyz':
            highLit = True
        else:
            return autorizeErrorsCode['badPassword']
    if not (highLit and lowLit and otherSymbol):
        return autorizeErrorsCode['badPassword']

    send('A')
    send(phoneNumber)
    send(mailAddress)
    send(accountPassword)

    result = connect.recv(1024).decode()
    if result in autorizeErrorsCode.keys():
        return autorizeErrorsCode[result]
    else:
        file = open(str(rootReturn()) + '/data/autorize.ini', 'w')
        file.write(phoneNumber + '\n')
        file.write(mailAddress + '\n')
        file.write(accountPassword)
        file.close()
        return 'M_' + result
