# -*_ coding: utf-8 -*-

from unicodedata import name
import pandas as pd
import tushare as ts
import json
from datetime import datetime, date
from datetime import timedelta
import requests
from time import *

def get_all_stock():
    ts.set_token('922a7a740724a061000a97e2b985284fff15ae7e701a53f580d9c1d7')
    pro = ts.pro_api()
    pool = pro.stock_basic(exchage='SSE,SZSE', list_status='L', fields = 'ts_code,symbol,name,fullname,list_date,is_hs')
    print('获取上市股票总数：', len(pool) - 1)
    return pool

def get_week_kline(code, start='20200101', end=''):
    url_mode = "https://q.stock.sohu.com/hisHq?code=cn_%s&start=%s&end=%s&period=w"
    url = url_mode%(code, start, end)
    resp = requests.get(url)
    if resp.status_code != 200:
        print("Failed to get daily. Error code: %s" % resp.status_code)
        return

    data = json.loads(resp.text)
    if 'hq' not in data[0]:
        return pd.DataFrame()

    dp = pd.json_normalize(data[0], record_path=['hq'], errors='ignore')
    return dp

def check_down_times(df, times):
    open_values = df[1]
    end_values = df[2]

    if len(open_values) <= times:
        return False

    for index in range(0, times):
        if float(end_values[index]) - float(open_values[index]) > 0:
            return False
    
    return True

def check_week_kline(code, start, end):
    df = get_week_kline(code, start, end)
    if df.empty:
        return False

    return check_down_times(df, 8)


if __name__ == "__main__":
    starttime = time()

    end = date.today().strftime('%Y%m%d')
    begin = (date.today() - timedelta(days=70)).strftime('%Y%m%d')
    all_stock = get_all_stock()
    for code, name, index in zip(all_stock.ts_code, all_stock.name, range(len(all_stock))):
        print('\r', end='')
        print('\033[0J', end='')  # erase from cursor to end
        print(index, "分析股票中：", name, "-", code, end='')
        if check_week_kline(code[0:6], begin, end):
            print('\r', end='')
            print('\033[0J', end='')  # erase from cursor to end
            print(name, "-", code)

    endtime = time()
    print("运行时:", endtime - starttime)