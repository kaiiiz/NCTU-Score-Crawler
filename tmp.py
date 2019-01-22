# parse
from argparse import ArgumentParser
import getpass

parser1 = ArgumentParser(description='Web crawler for NCTU class schedule.')
parser1.add_argument('username', help='username of NCTU portal', type=str)
args = parser1.parse_args()
password = getpass.getpass('Password:')

# web crawler
import requests

ses = requests.Session()

# Captcha
from PIL import Image
from PIL import ImageEnhance
from io import BytesIO
import pytesseract

res = ses.get('https://portal.nctu.edu.tw/captcha/pic.php') # get captcha
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
        res = ses.post("https://portal.nctu.edu.tw/portal/chkpas.php", data=auth)
        res.encoding = "utf8"
        if "校園資訊系統" in res.text:
            break
        if "請確認密碼是否正確" in res.text:
            print("Wrong password.")
            exit()
        if "無此帳號" in res.text:
            print("Wrong ID number.")
            exit()

# Data Process
from bs4 import BeautifulSoup

res = ses.get("https://portal.nctu.edu.tw/portal/relay.php?D=cos")
soup = BeautifulSoup(res.content, 'lxml')
form = soup.find_all("input")
submit = {}
for i in form:
    if i.attrs['name'] == "Chk_SSO":
        submit[i.attrs['name']] = "checked"
    else:
        submit[i.attrs['name']] = i.attrs['value']
res = ses.post("https://course.nctu.edu.tw/jwt.asp", data=submit)
res = ses.get("https://course.nctu.edu.tw/adSchedule.asp")
res.encoding = 'big5'

# print table
from tabulate import tabulate
import pandas as pd

tb = pd.read_html(res.text)
df = tb[0].drop(tb[0].index[0]).fillna("")
print(tabulate(df, tablefmt='fancy_grid'))