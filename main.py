import sys
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
# Table
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

def LoginPortal(username, password):
    ses = requests.Session()
    res = ses.get('https://portal.nctu.edu.tw/captcha/pic.php')
    while True:
        res = ses.get('https://portal.nctu.edu.tw/captcha/claviska-simple-php-captcha/pic.php', stream=True) # set captcha type
        # Identify Captcha
        Captcha = Image.open(BytesIO(res.content))
        grey_Captcha = Captcha.convert('L')
        grey_Captcha = ImageEnhance.Brightness(grey_Captcha).enhance(1.1)
        grey_Captcha = ImageEnhance.Contrast(grey_Captcha).enhance(2)
        key = pytesseract.image_to_string(grey_Captcha)
        if len(key) == 4:
            auth = {
                "username": username,
                "Submit2": "登入(Login)",
                "pwdtype": "static",
                "password": password,
                "seccode": key
            }
            res = ses.post("https://portal.nctu.edu.tw/portal/checkuser.php", data=auth)
            res.encoding = "utf8"
            if "校園資訊系統" in res.text:
                break
            elif "請確認密碼是否正確" in res.text:
                print("Wrong password.")
                exit()
            elif "無此帳號" in res.text:
                print("Wrong ID number.")
                exit()
            else:
                print('Wrong captcha code, retry.')
    return ses

def LoginRegistSys(ses):
    res = ses.get('https://portal.nctu.edu.tw/portal/relay.php?D=regist')
    soup = BeautifulSoup(res.content, 'lxml')
    form = soup.find_all("input")
    submit = {}
    for i in form:
        if i.attrs['name'] == "Chk_SSO":
            submit[i.attrs['name']] = "checked"
        else:
            submit[i.attrs['name']] = i.attrs['value']
    ses.post("https://regist.nctu.edu.tw/login_users_ldap.aspx", data=submit)
    return ses

def ParseOverallScore(ses):
    stuInfo = {}
    res = ses.get('https://regist.nctu.edu.tw/p_student/grd_stdscorelist.aspx')
    soup = BeautifulSoup(res.content, 'lxml')

    stuScoreList = soup.find(id='divWorking').find('table').findAll('tr', recursive=False)
    stuInfoTable = stuScoreList[1]
    stuScoreTable = stuScoreList[2].find(id='GridView1')

    stuInfo['lblClass'] = stuInfoTable.find(id='lblClass').string
    stuInfo['lblStdcode'] = stuInfoTable.find(id='lblStdcode').string
    stuInfo['lblStdname'] = stuInfoTable.find(id='lblStdname').string
    stuInfo['lblIdentity'] = stuInfoTable.find(id='lblIdentity').string
    stuInfo['lblYearterm'] = stuInfoTable.find(id='lblYearterm').string
    stuInfo['lblTermcount'] = stuInfoTable.find(id='lblTermcount').string
    stuInfo['lblEnglish'] = stuInfoTable.find(id='GridView2').find('td').string
    stuInfo['lblEthics'] = stuInfoTable.find(id='GridView3').find('td').string

    stuScoreInfo = ParseGrid(stuScoreTable)
    return stuInfo, stuScoreInfo

def main():
    # Parse Argument
    parser = ArgumentParser(description='Web crawler for NCTU Score.')
    parser.add_argument('username', help='username of NCTU portal', type=str)
    args = parser.parse_args()
    password = getpass.getpass('Password:')
    # Login System
    ses = LoginPortal(args.username, password)
    ses = LoginRegistSys(ses)
    # Get Overall Score
    stuInfo, stuScoreInfo = ParseOverallScore(ses)
    print(stuInfo['lblClass'], stuInfo['lblStdcode'], stuInfo['lblStdname'], stuInfo['lblIdentity'], stuInfo['lblYearterm'], stuInfo['lblTermcount'])
    print(stuInfo['lblEnglish'])
    print(stuInfo['lblEthics'])
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
            print('Invalid number.')
            continue
        else:
            Semester = stuScoreInfo[Semester][1].replace('上', '1').replace('下', '2')
            res = ses.get('https://regist.nctu.edu.tw/p_student/grd_stdscoreedit.aspx?yearterm=' + Semester)
            soup = BeautifulSoup(res.content, 'lxml')
            stuScoreInfo = ParseGrid(soup.find(id='GridView1'))
            print(tabulate(stuScoreInfo, tablefmt='fancy_grid'))
            break

if __name__ == "__main__":
    main()