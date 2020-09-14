import sys
from argparse import ArgumentParser
import getpass
from PIL import Image
from PIL import ImageEnhance
from io import BytesIO
import pytesseract
import requests
from bs4 import BeautifulSoup
from tabulate import tabulate
import wcwidth


GPA_MAP = {
    'A+': 4.3,
    'A': 4,
    'A-': 3.7,
    'B+': 3.3,
    'B': 3,
    'B-': 2.7,
    'C+': 2.3,
    'C': 2,
    'C-': 1.7,
    'D': 1,
    'E': 0,
    'X': 0,
}

GPA_IGNORE = ['通過', '不通過', 'W']

def LoginPortal(username, password):
    ses = requests.Session()
    ses.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; rv:68.0) Gecko/20100101 Firefox/68.0'})
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

def ParseGrid(ses, url):
    res = ses.get(url)
    soup = BeautifulSoup(res.content, 'lxml')
    stuScore = []
    stuScoreTable = soup.find(id='GridView1')
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
        stuScore.append(line)
    return stuScore, soup

def PrintFooter(soup):
    for i in soup.find(id='trScore').findAll('td', recursive=False):
        s = i.find('span')
        if s:
            print(s.string, end='')
        else:
            print(' ', end='')
    print()

def CalGPA(stuScore):
    header = stuScore[0]
    credit_idx = header.index('學分')
    grade_idx = header.index('等級成績')
    credit_total = 0
    grade_weight_total = 0
    for row in stuScore[1:]:
        if row[grade_idx] not in GPA_IGNORE:
            credit = float(row[credit_idx])
            grade = GPA_MAP[row[grade_idx]]
            credit_total += credit
            grade_weight_total += credit * grade

    return grade_weight_total / credit_total

def main():
    # Parse Argument
    parser = ArgumentParser(description='Web crawler for NCTU Student\'s Score.')
    parser.add_argument('username', help='username of NCTU portal', type=str)
    args = parser.parse_args()
    password = getpass.getpass('Password:')
    # Login System
    ses = LoginPortal(args.username, password)
    ses = LoginRegistSys(ses)
    # Print Overall Score
    stuScore, soup = ParseGrid(ses, 'https://regist.nctu.edu.tw/p_student/grd_stdscorelist.aspx')
    print(tabulate(stuScore, tablefmt='fancy_grid'))

    while True:
        Semester = input('Enter the number in leftest column (0:ALL): ')
        if Semester == '':
            print('Invalid.')
            continue
        else:
            Semester = int(Semester)
            if Semester == 0:
                # Get Score, Soup
                url = 'https://regist.nctu.edu.tw/p_student/grd_stdscoreedit.aspx'
                stuScore, soup = ParseGrid(ses, url)
                gpa = CalGPA(stuScore)
                # Print Table
                print(tabulate(stuScore, tablefmt='fancy_grid'))
                PrintFooter(soup)
                print(f"GPA: {gpa}")
                break
            elif Semester >= len(stuScore):
                print('Invalid number.')
                continue
            else:
                # Get Score, Soup
                Semester = stuScore[Semester][1].replace('上', '1').replace('下', '2').replace('暑', '3')
                url = 'https://regist.nctu.edu.tw/p_student/grd_stdscoreedit.aspx?yearterm=' + Semester
                stuScore, soup = ParseGrid(ses, url)
                # Print Table
                print(tabulate(stuScore, tablefmt='fancy_grid'))
                PrintFooter(soup)
                break

if __name__ == "__main__":
    main()