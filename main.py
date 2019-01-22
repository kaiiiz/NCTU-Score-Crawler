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