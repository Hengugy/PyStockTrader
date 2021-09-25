import os
import sys
import sqlite3
import numpy as np
import pandas as pd
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
from utility.static import now, timedelta_sec, strf_time
from utility.setting import columns_gj1, ui_num, db_setting, stock_csan_time

TUJAGMDIVIDE = 10    # 종목당 투자금 분할계수


class StrategyStock:
    def __init__(self, windowQ, stockQ, sstgQ):
        self.windowQ = windowQ
        self.stockQ = stockQ
        self.sstgQ = sstgQ

        self.list_buy = []
        self.list_sell = []
        self.dict_gsjm = {}     # key: 종목코드, value: 10시이전 DataFrame, 10시이후 list
        self.dict_intg = {
            '체결강도차이': 0.,
            '평균시간': 0,
            '거래대금차이': 0,
            '체결강도하한': 0.,
            '누적거래대금하한': 0,
            '등락율하한': 0.,
            '등락율상한': 0.,
            '청산수익률': 0.
        }
        self.dict_time = {'관심종목': now()}
        self.Start()

    def Start(self):
        con = sqlite3.connect(db_setting)
        df = pd.read_sql('SELECT * FROM stock', con)
        df = df.set_index('index')
        self.dict_intg['체결강도차이'] = df['체결강도차이'][0]
        self.dict_intg['평균시간'] = df['평균시간'][0]
        self.dict_intg['거래대금차이'] = df['거래대금차이'][0]
        self.dict_intg['체결강도하한'] = df['체결강도하한'][0]
        self.dict_intg['누적거래대금하한'] = df['누적거래대금하한'][0]
        self.dict_intg['등락율하한'] = df['등락율하한'][0]
        self.dict_intg['등락율상한'] = df['등락율상한'][0]
        self.dict_intg['청산수익률'] = df['청산수익률'][0]
        con.close()
        int_time = int(strf_time('%H%M%S'))
        while True:
            data = self.sstgQ.get()
            if data == '시스템종료':
                sys.exit()
            elif len(data) == 2:
                self.UpdateList(data[0], data[1])
            elif len(data) == 14:
                self.BuyStrategy(data[0], data[1], data[2], data[3], data[4], data[5], data[6], data[7],
                                 data[8], data[9], data[10], data[11], data[12], data[13])
            elif len(data) == 7:
                self.SellStrategy(data[0], data[1], data[2], data[3], data[4], data[5], data[6])

            if now() > self.dict_time['관심종목']:
                self.windowQ.put([ui_num['관심종목'], self.dict_gsjm])
                self.dict_time['관심종목'] = timedelta_sec(1)

            if int_time < stock_csan_time - 1 <= int(strf_time('%H%M%S')):
                break
            int_time = int(strf_time('%H%M%S'))
        sys.exit()

    def UpdateList(self, gubun, code):
        if '조건진입' in gubun:
            if code not in self.dict_gsjm.keys():
                data = np.zeros((self.dict_intg['평균시간'] + 2, len(columns_gj1))).tolist()
                df = pd.DataFrame(data, columns=columns_gj1)
                df['체결시간'] = '090000'
                self.dict_gsjm[code] = df.copy()
            if gubun == '조건진입마지막':
                self.windowQ.put([ui_num['관심종목'], self.dict_gsjm])
        elif gubun == '조건이탈':
            if code in self.dict_gsjm.keys():
                del self.dict_gsjm[code]
        elif gubun == '매수완료':
            if code in self.list_buy:
                self.list_buy.remove(code)
        elif gubun == '매도완료':
            if code in self.list_sell:
                self.list_sell.remove(code)

    def BuyStrategy(self, code, name, c, o, h, low, per, ch, dm, t, injango, vitimedown, vid5priceup, batting):
        if code not in self.dict_gsjm.keys():
            return

        hlm = round((h + low) / 2)
        hlmp = round((c / hlm - 1) * 100, 2)
        predm = self.dict_gsjm[code]['누적거래대금'][1]
        sm = 0 if predm == 0 else int(dm - predm)
        self.dict_gsjm[code] = self.dict_gsjm[code].shift(1)
        if len(self.dict_gsjm[code]) == self.dict_intg['평균시간'] + 2 and \
                self.dict_gsjm[code]['체결강도'][self.dict_intg[f'평균시간']] != 0.:
            avg_sm = int(self.dict_gsjm[code]['거래대금'][1:self.dict_intg['평균시간'] + 1].mean())
            avg_ch = round(self.dict_gsjm[code]['체결강도'][1:self.dict_intg['평균시간'] + 1].mean(), 2)
            high_ch = round(self.dict_gsjm[code]['체결강도'][1:self.dict_intg['평균시간'] + 1].max(), 2)
            self.dict_gsjm[code].at[self.dict_intg['평균시간'] + 1] = 0., 0., avg_sm, 0, avg_ch, high_ch, t
        self.dict_gsjm[code].at[0] = per, hlmp, sm, dm, ch, 0., t

        if self.dict_gsjm[code]['체결강도'][self.dict_intg['평균시간']] == 0:
            return
        if code in self.list_buy:
            return
        if injango:
            return

        # 전략 비공개

        oc = int(batting / TUJAGMDIVIDE / c)
        if oc > 0:
            self.list_buy.append(code)
            self.stockQ.put(['매수', code, name, c, oc])

    def SellStrategy(self, code, name, per, sp, jc, ch, c):
        if code in self.list_sell:
            return

        oc = 0
        if per >= 29:
            oc = jc

        # 전략 비공개

        if oc > 0:
            self.list_sell.append(code)
            self.stockQ.put(['매도', code, name, c, oc])
