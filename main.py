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

def ParseGrid(stuScoreTable):
    stuScoreInfo = []
    for i in stuScoreTable.findAll('tr', recursive=False):
        td = i.findAll('td')
        th = i.findAll('th')
        line = []
        if len(th):
            for j in th:
                line.append(j.string)
        elif len(td):
            for j in td:
                if (j.find('span')):
                    line.append(j.find('span').string)
                else:
                    line.append(j.string)
        stuScoreInfo.append(line)
    return stuScoreInfo

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

stuScoreList = soup.find(id='divWorking').find('table').findAll('tr', recursive=False)
stuInfoTable = stuScoreList[1]
stuScoreTable = stuScoreList[2].find(id='GridView1')

stuInfo = {}
stuInfo['lblClass'] = stuInfoTable.find(id='lblClass').string
stuInfo['lblStdcode'] = stuInfoTable.find(id='lblStdcode').string
stuInfo['lblStdname'] = stuInfoTable.find(id='lblStdname').string
stuInfo['lblIdentity'] = stuInfoTable.find(id='lblIdentity').string
stuInfo['lblYearterm'] = stuInfoTable.find(id='lblYearterm').string
stuInfo['lblTermcount'] = stuInfoTable.find(id='lblTermcount').string
stuInfo['lblEnglish'] = stuInfoTable.find(id='GridView2').find('td').string
stuInfo['lblEthics'] = stuInfoTable.find(id='GridView3').find('td').string

stuScoreInfo = ParseGrid(stuScoreTable)
print(tabulate(stuScoreInfo, tablefmt='fancy_grid'))

while True:
    Semester = int(input('Enter your semester: '))
    if Semester == 0:
        res = ses.get('https://regist.nctu.edu.tw/p_student/grd_stdscoreedit.aspx')
        soup = BeautifulSoup(res.content, 'lxml')
        stuScoreInfo = ParseGrid(soup.find(id='GridView1'))
        print(tabulate(stuScoreInfo, tablefmt='fancy_grid'))
        break
    elif Semester >= len(stuScoreInfo):
        print('Invalid enter.')
        continue
    else:
        Semester = stuScoreInfo[Semester][1].replace('上', '1').replace('下', '2')
        res = ses.get('https://regist.nctu.edu.tw/p_student/grd_stdscoreedit.aspx?yearterm=' + Semester)
        soup = BeautifulSoup(res.content, 'lxml')
        stuScoreInfo = ParseGrid(soup.find(id='GridView1'))
        print(tabulate(stuScoreInfo, tablefmt='fancy_grid'))
        break