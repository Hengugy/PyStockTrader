import os
import sys
import pyupbit
import pandas as pd
from PyQt5.QtCore import QThread
from pyupbit import WebSocketManager
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
from utility.setting import ui_num, coin_exit_time
from utility.static import now, timedelta_sec, strf_time


class UpdaterTickUpbit:
    def __init__(self, windowQ, queryQ, tickQ):
        self.windowQ = windowQ
        self.queryQ = queryQ
        self.tickQ = tickQ

        self.dict_df = {}                   # 틱데이터 저장용 딕셔너리 key: ticker, value: datafame
        self.dict_orderbook = {}            # 오더북 저장용 딕셔너리
        self.time_info = timedelta_sec(60)  # 틱데이터 저장주기 확인용
        self.Start()

    def Start(self):
        int_time = int(strf_time('%H%M%S'))
        while True:
            data = self.tickQ.get()
            if type(data) == list:
                self.UpdateTickData(data[0], data[1])
            else:
                self.UpdateOrderbook(data)

            if int_time < coin_exit_time <= int(strf_time('%H%M%S')):
                break
            int_time = int(strf_time('%H%M%S'))
        sys.exit()

    def UpdateTickData(self, data_, receiv_time):
        ticker = data_['code']
        dt = data_['trade_date'] + data_['trade_time']
        if ticker not in self.dict_orderbook.keys():
            return

        data = {
            '현재가': data_['trade_price'],
            '시가': data_['opening_price'],
            '고가': data_['high_price'],
            '저가': data_['low_price'],
            '등락율': round(data_['signed_change_rate'] * 100, 2),
            '누적거래대금': data_['acc_trade_price'],
            '누적매수량': data_['acc_bid_volume'],
            '누적매도량': data_['acc_ask_volume']
        }
        data.update(self.dict_orderbook[ticker])

        if ticker not in self.dict_df.keys():
            self.dict_df[ticker] = pd.DataFrame(data, index=[dt])
        else:
            self.dict_df[ticker].at[dt] = list(data.values())

        if now() > self.time_info:
            gap = (now() - receiv_time).total_seconds()
            self.windowQ.put([ui_num['C단순텍스트'], f'수신시간과 갱신시간의 차이는 [{gap}]초입니다.'])
            self.queryQ.put([4, self.dict_df])
            self.dict_df = {}
            self.time_info = timedelta_sec(60)

    def UpdateOrderbook(self, data):
        ticker = data['code']
        self.dict_orderbook[ticker] = {
            '매도호가2': data['orderbook_units'][1]['ask_price'],
            '매도호가1': data['orderbook_units'][0]['ask_price'],
            '매수호가1': data['orderbook_units'][0]['bid_price'],
            '매수호가2': data['orderbook_units'][1]['bid_price'],
            '매도잔량2': data['orderbook_units'][1]['ask_size'],
            '매도잔량1': data['orderbook_units'][0]['ask_size'],
            '매수잔량1': data['orderbook_units'][0]['bid_size'],
            '매수잔량2': data['orderbook_units'][1]['bid_size']
        }


class WebsTicker(QThread):
    def __init__(self, tick9Q, tick10Q):
        super().__init__()
        self.tick9Q = tick9Q
        self.tick10Q = tick10Q

        self.tickers = pyupbit.get_tickers(fiat="KRW")
        self.tickers1 = [ticker for i, ticker in enumerate(self.tickers) if i % 2 == 0]
        self.tickers2 = [ticker for i, ticker in enumerate(self.tickers) if i % 2 == 1]

    def run(self):
        int_time = int(strf_time('%H%M%S'))
        dict_time = {}
        int_tick = 0
        websQ_ticker = WebSocketManager('ticker', self.tickers)

        while True:
            data = websQ_ticker.get()
            int_tick += 1
            ticker = data['code']
            t = data['trade_time']
            try:
                pret = dict_time[ticker]
            except KeyError:
                pret = None
            if pret is None or t != pret:
                dict_time[ticker] = t
                if ticker in self.tickers1:
                    self.tick9Q.put([data, now()])
                elif ticker in self.tickers2:
                    self.tick10Q.put([data, now()])

            if int_time < coin_exit_time + 100 <= int(strf_time('%H%M%S')):
                break
            int_time = int(strf_time('%H%M%S'))
        sys.exit()


class WebsOrderbook(QThread):
    def __init__(self, tick9Q, tick10Q):
        super().__init__()
        self.tick9Q = tick9Q
        self.tick10Q = tick10Q

        self.tickers = pyupbit.get_tickers(fiat="KRW")
        self.tickers1 = [ticker for i, ticker in enumerate(self.tickers) if i % 2 == 0]
        self.tickers2 = [ticker for i, ticker in enumerate(self.tickers) if i % 2 == 1]

    def run(self):
        int_time = int(strf_time('%H%M%S'))
        int_tick = 0
        websQ_order = WebSocketManager('orderbook', self.tickers)

        while True:
            data = websQ_order.get()
            int_tick += 1
            ticker = data['code']
            if ticker in self.tickers1:
                self.tick9Q.put(data)
            elif ticker in self.tickers2:
                self.tick10Q.put(data)

            if int_time < coin_exit_time <= int(strf_time('%H%M%S')):
                break
            int_time = int(strf_time('%H%M%S'))

        self.windowQ.put([ui_num['C로그텍스트'], '콜렉터를 종료합니다.'])
        if self.dict_bool['알림소리']:
            self.soundQ.put('코인 콜렉터를 종료합니다.')
        self.teleQ.put('코인 콜렉터를 종료하였습니니다.')
        sys.exit()
