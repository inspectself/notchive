# -*_ coding: utf-8 -*-

from unicodedata import name
import pandas as pd
import tushare as ts
import json
from datetime import datetime, date
from datetime import timedelta
import requests
from time import *
import threading
from tqdm import *

list_ok = []

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
        # tqdm.write("Failed to get daily. Error code: %s" % resp.status_code)
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


class my_thread(threading.Thread):
    def __init__(self, threadId, df, begin, end):
        threading.Thread.__init__(self)
        self.threadId = threadId
        self.df = df
        self.begin = begin
        self.end = end

    def run(self):
        stocks = self.df
        with tqdm(total=len(stocks), leave=False) as pbar:
            for code, name, index in zip(stocks.ts_code, stocks.name, range(len(stocks))):
                if check_week_kline(code[0:6], begin, end):
                    list_ok.append("{}-{}".format(name, code))

                pbar.update(1)
                pbar.set_description("{:\u3000>4}".format(name))
        
            pbar.close()

if __name__ == "__main__":
    starttime = time()

    end = date.today().strftime('%Y%m%d')
    begin = (date.today() - timedelta(days=70)).strftime('%Y%m%d')
    all_stock = get_all_stock()


    thread_lst = []
    thread_num = len(all_stock)//1000 + 1
    for index in range(0, thread_num):
        bIndex = index * 1000
        eIndex = bIndex + 1000
        if eIndex > len(all_stock) - 1:
            eIndex = len(all_stock) - 1
        thread = my_thread(0, all_stock.iloc[bIndex: eIndex], begin, end)
        thread.start()
        thread_lst.append(thread)

    for index in range(0, thread_num):
        thread_lst[index].join()
    
    endtime = time()
    print("运行耗时:", endtime - starttime)
    for obj in list_ok:
        print(obj)