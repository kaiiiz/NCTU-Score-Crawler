# parse
from argparse import ArgumentParser
import getpass
# Captcha
from PIL import Image
from PIL import ImageEnhance
from io import BytesIO
import pytesseract
# Crawer
import requests
from bs4 import BeautifulSoup
# print table
from tabulate import tabulate
import pandas as pd

parser1 = ArgumentParser(description='Web crawler for NCTU class schedule.')
parser1.add_argument('username', help='username of NCTU portal', type=str)
args = parser1.parse_args()
password = getpass.getpass('Password:')

ses = requests.Session()
res = ses.get('https://portal.nctu.edu.tw/captcha/pic.php')  # get captcha

while True:
    res = ses.get('https://portal.nctu.edu.tw/captcha/claviska-simple-php-captcha/pic.php', stream=True) # set captcha type
    Captcha = Image.open(BytesIO(res.content))
    grey_Captcha = Captcha.convert('L')
    grey_Captcha = ImageEnhance.Brightness(grey_Captcha).enhance(1.1)
    grey_Captcha = ImageEnhance.Contrast(grey_Captcha).enhance(2)
    key = pytesseract.image_to_string(grey_Captcha)
    if len(key) == 4:
        auth = {
            "username": args.username,
            "Submit2": "登入(Login)",
            "pwdtype": "static",
            "password": password,
            "seccode": key
        }
        res = ses.post("https://portal.nctu.edu.tw/portal/checkuser.php", data=auth)
        res.encoding = "utf8"
        if "校園資訊系統" in res.text:
            print("Enter portal.")
            break
        if "請確認密碼是否正確" in res.text:
            print("Wrong password.")
            exit()
        if "無此帳號" in res.text:
            print("Wrong ID number.")
            exit()
    print('Wrong captcha code, retry.')

res = ses.get('https://portal.nctu.edu.tw/portal/relay.php?D=regist')
soup = BeautifulSoup(res.content, 'lxml')
form = soup.find_all("input")
submit = {}
for i in form:
    if i.attrs['name'] == "Chk_SSO":
        submit[i.attrs['name']] = "checked"
    else:
        submit[i.attrs['name']] = i.attrs['value']
res = ses.post("https://regist.nctu.edu.tw/login_users_ldap.aspx", data=submit)

res = ses.get('https://regist.nctu.edu.tw/p_student/grd_stdscorelist.aspx')
soup = BeautifulSoup(res.content, 'lxml')

stuInfoTable = soup.find(id='divWorking').find('table').find('tr').find_next('tr')
stuScoreTable = soup.find(id='divWorking').find('table').find(id='GridView1').findAll('tr')
stuInfo = {}
stuScoreInfo = []
stuScoreIndex = []
stuInfo['lblClass'] = stuInfoTable.find(id='lblClass').string
stuInfo['lblStdcode'] = stuInfoTable.find(id='lblStdcode').string
stuInfo['lblStdname'] = stuInfoTable.find(id='lblStdname').string
stuInfo['lblIdentity'] = stuInfoTable.find(id='lblIdentity').string
stuInfo['lblYearterm'] = stuInfoTable.find(id='lblYearterm').string
stuInfo['lblTermcount'] = stuInfoTable.find(id='lblTermcount').string
stuInfo['lblEnglish'] = stuInfoTable.find(id='GridView2').find('td').string
stuInfo['lblEthics'] = stuInfoTable.find(id='GridView3').find('td').string

# add index
for i in stuScoreTable[0].findAll('th'):
    stuScoreIndex.append(i.string)
stuScoreInfo.append(stuScoreIndex)

# add each entry
for i in range(1, len(stuScoreTable)):
    td = stuScoreTable[i].findAll('td')
    line = []
    for j in range(len(td)):
        line.append(td[j].string)
    stuScoreInfo.append(line)

print(tabulate(stuScoreInfo, tablefmt='fancy_grid'))