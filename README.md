# NCTU Score Crawler

把自己[學籍成績管理系統](https://regist.nctu.edu.tw/)上面的成績全部抓下來

## Install

```
git clone https://github.com/kaiiiz/NCTU_Score_Crawler.git
cd NCTU_Score_Crawler
pip install -r requirements.txt
```

Beside the python packages, you also need [tesseract](https://github.com/tesseract-ocr/tesseract/wiki) to recognize captcha.

Here is an example for Arch Linux user:

```
yaourt -S tesseract tesseract-data-eng
export TESSDATA_PREFIX=/usr/share/tessdata
```

## How to use

```
python main.py {student_id}
```

After enter your student id, you will be asked to enter your portal password.
