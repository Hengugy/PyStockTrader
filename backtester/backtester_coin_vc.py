import os
import sys
import sqlite3
import pandas as pd
from matplotlib import pyplot as plt
from multiprocessing import Process, Queue
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
from utility.static import now, strf_time, timedelta_day
from utility.setting import db_setting, db_backtest, db_coin_tick, graph_path


class BackTester2Coin:
    def __init__(self, q_, ticker_list_, num_, high):
        self.q = q_
        self.ticker_list = ticker_list_
        self.high = high

        if type(num_[3]) == list:
            self.batting = num_[0]
            self.testperiod = num_[1]
            self.totaltime = num_[2]
            self.gap_ch = num_[3][0]
            self.avg_time = num_[4][0]
            self.gap_sm = num_[5][0]
            self.ch_low = num_[6][0]
            self.dm_low = num_[7][0]
            self.per_low = num_[8][0]
            self.per_high = num_[9][0]
            self.cs_per = num_[10][0]
        else:
            self.batting = num_[0]
            self.testperiod = num_[1]
            self.totaltime = num_[2]
            self.gap_ch = num_[3]
            self.avg_time = num_[4]
            self.gap_sm = num_[5]
            self.ch_low = num_[6]
            self.dm_low = num_[7]
            self.per_low = num_[8]
            self.per_high = num_[9]
            self.cs_per = num_[10]

        self.ticker = None
        self.df = None

        self.totalcount = 0
        self.totalcount_p = 0
        self.totalcount_m = 0
        self.totalholdday = 0
        self.totaleyun = 0
        self.totalper = 0.

        self.hold = False
        self.buycount = 0
        self.buyprice = 0
        self.sellprice = 0
        self.index = 0
        self.indexb = 0
        self.indexn = 0
        self.ccond = 0
        self.csell = 0

        self.Start()

    def Start(self):
        conn = sqlite3.connect(db_coin_tick)
        tcount = len(self.ticker_list)
        int_daylimit = int(strf_time('%Y%m%d', timedelta_day(-self.testperiod)))
        for k, ticker in enumerate(self.ticker_list):
            self.ticker = ticker
            self.df = pd.read_sql(f"SELECT * FROM '{ticker}'", conn)
            self.df = self.df.set_index('index')
            self.df['고저평균대비등락율'] = (self.df['현재가'] / ((self.df['고가'] + self.df['저가']) / 2) - 1) * 100
            self.df['고저평균대비등락율'] = self.df['고저평균대비등락율'].round(2)
            self.df['체결강도'] = self.df['누적매수량'] / self.df['누적매도량'] * 100
            self.df['체결강도'] = self.df['체결강도'].round(2)
            self.df['직전체결강도'] = self.df['체결강도'].shift(1)
            self.df['직전누적거래대금'] = self.df['누적거래대금'].shift(1)
            self.df = self.df.fillna(0)
            self.df['거래대금'] = self.df['누적거래대금'] - self.df['직전누적거래대금']
            self.df['직전거래대금'] = self.df['거래대금'].shift(1)
            self.df = self.df.fillna(0)
            self.df['거래대금평균'] = self.df['직전거래대금'].rolling(window=self.avg_time).mean()
            self.df['체결강도평균'] = self.df['직전체결강도'].rolling(window=self.avg_time).mean()
            self.df['최고체결강도'] = self.df['직전체결강도'].rolling(window=self.avg_time).max()
            self.df = self.df.fillna(0)
            self.totalcount = 0
            self.totalcount_p = 0
            self.totalcount_m = 0
            self.totalholdday = 0
            self.totaleyun = 0
            self.totalper = 0.
            self.ccond = 0
            lasth = len(self.df) - 1
            for h, index in enumerate(self.df.index):
                if h != 0 and index[:8] != self.df.index[h - 1][:8]:
                    self.ccond = 0
                if int(index[:8]) < int_daylimit or \
                        (not self.hold and (210000 <= int(index[8:]) or int(index[8:]) < 10000)):
                    continue
                self.index = index
                self.indexn = h
                self.ccond += 1
                if not self.hold and 10000 < int(index[8:]) < 210000 and self.BuyTerm():
                    self.Buy()
                elif self.hold and 10000 < int(index[8:]) < 210000 and self.SellTerm():
                    self.Sell()
                elif self.hold and (h == lasth or int(index[8:]) >= 210000 > int(self.df.index[h - 1][8:])):
                    self.Sell()
            self.Report(k + 1, tcount)
        conn.close()

    def BuyTerm(self):
        if type(self.df['현재가'][self.index]) == pd.Series:
            return False
        if self.ccond < self.avg_time:
            return False

        # 전략 비공개

        return True

    def Buy(self):
        if self.df['매도호가1'][self.index] * self.df['매도잔량1'][self.index] >= self.batting:
            s1hg = self.df['매도호가1'][self.index]
            self.buycount = int(self.batting / s1hg)
            self.buyprice = s1hg
        else:
            s1hg = self.df['매도호가1'][self.index]
            s1jr = self.df['매도잔량1'][self.index]
            s2hg = self.df['매도호가2'][self.index]
            ng = self.batting - s1hg * s1jr
            s2jc = int(ng / s2hg)
            self.buycount = s1jr + s2jc
            self.buyprice = round((s1hg * s1jr + s2hg * s2jc) / self.buycount, 2)
        if self.buycount == 0:
            return
        self.hold = True
        self.indexb = self.indexn
        self.csell = 0

    def SellTerm(self):
        if type(self.df['현재가'][self.index]) == pd.Series:
            return False
        if self.df['등락율'][self.index] > 29:
            return True

        bg = self.buycount * self.buyprice
        cg = self.buycount * self.df['현재가'][self.index]
        eyun, per = self.GetEyunPer(bg, cg)

        # 전략 비공개

        return False

    def Sell(self):
        if self.df['매수잔량1'][self.index] >= self.buycount:
            self.sellprice = self.df['매수호가1'][self.index]
        else:
            b1hg = self.df['매수호가1'][self.index]
            b1jr = self.df['매수잔량1'][self.index]
            b2hg = self.df['매수호가2'][self.index]
            nc = self.buycount - b1jr
            self.sellprice = round((b1hg * b1jr + b2hg * nc) / self.buycount, 2)
        self.hold = False
        self.CalculationEyun()
        self.indexb = 0

    def CalculationEyun(self):
        self.totalcount += 1
        bg = self.buycount * self.buyprice
        cg = self.buycount * self.sellprice
        eyun, per = self.GetEyunPer(bg, cg)
        self.totalper = round(self.totalper + per, 2)
        self.totaleyun = int(self.totaleyun + eyun)
        self.totalholdday += self.indexn - self.indexb
        if per > 0:
            self.totalcount_p += 1
        else:
            self.totalcount_m += 1
        if self.high:
            self.q.put([self.index, self.ticker, per, eyun])

    # noinspection PyMethodMayBeStatic
    def GetEyunPer(self, bg, cg):
        gtexs = cg * 0.0023
        gsfee = cg * 0.00015
        gbfee = bg * 0.00015
        texs = gtexs - (gtexs % 1)
        sfee = gsfee - (gsfee % 10)
        bfee = gbfee - (gbfee % 10)
        pg = int(cg - texs - sfee - bfee)
        eyun = pg - bg
        per = round(eyun / bg * 100, 2)
        return eyun, per

    def Report(self, count, tcount):
        if self.totalcount > 0:
            plus_per = round((self.totalcount_p / self.totalcount) * 100, 2)
            avgholdday = round(self.totalholdday / self.totalcount, 2)
            self.q.put([self.ticker, self.totalcount, avgholdday, self.totalcount_p, self.totalcount_m,
                        plus_per, self.totalper, self.totaleyun])
            ticker, totalcount, avgholdday, totalcount_p, totalcount_m, plus_per, totalper, totaleyun = \
                self.GetTotal(plus_per, avgholdday)
            print(f" 종목코드 {ticker} | 평균보유기간 {avgholdday}초 | 거래횟수 {totalcount}회 | "
                  f" 익절 {totalcount_p}회 | 손절 {totalcount_m}회 | 승률 {plus_per}% |"
                  f" 수익률 {totalper}% | 수익금 {totaleyun}원 [{count}/{tcount}]")
        else:
            self.q.put([self.ticker, 0, 0, 0, 0, 0., 0., 0])

    def GetTotal(self, plus_per, avgholdday):
        ticker = str(self.ticker)
        ticker = ticker + '    ' if len(ticker) == 6 else ticker
        ticker = ticker + '   ' if len(ticker) == 7 else ticker
        ticker = ticker + '  ' if len(ticker) == 8 else ticker
        ticker = ticker + ' ' if len(ticker) == 9 else ticker
        totalcount = str(self.totalcount)
        totalcount = '  ' + totalcount if len(totalcount) == 1 else totalcount
        totalcount = ' ' + totalcount if len(totalcount) == 2 else totalcount
        avgholdday = str(avgholdday)
        avgholdday = '    ' + avgholdday if len(avgholdday.split('.')[0]) == 1 else avgholdday
        avgholdday = '   ' + avgholdday if len(avgholdday.split('.')[0]) == 2 else avgholdday
        avgholdday = '  ' + avgholdday if len(avgholdday.split('.')[0]) == 3 else avgholdday
        avgholdday = ' ' + avgholdday if len(avgholdday.split('.')[0]) == 4 else avgholdday
        avgholdday = avgholdday + '0' if len(avgholdday.split('.')[1]) == 1 else avgholdday
        totalcount_p = str(self.totalcount_p)
        totalcount_p = '  ' + totalcount_p if len(totalcount_p) == 1 else totalcount_p
        totalcount_p = ' ' + totalcount_p if len(totalcount_p) == 2 else totalcount_p
        totalcount_m = str(self.totalcount_m)
        totalcount_m = '  ' + totalcount_m if len(totalcount_m) == 1 else totalcount_m
        totalcount_m = ' ' + totalcount_m if len(totalcount_m) == 2 else totalcount_m
        plus_per = str(plus_per)
        plus_per = '  ' + plus_per if len(plus_per.split('.')[0]) == 1 else plus_per
        plus_per = ' ' + plus_per if len(plus_per.split('.')[0]) == 2 else plus_per
        plus_per = plus_per + '0' if len(plus_per.split('.')[1]) == 1 else plus_per
        totalper = str(self.totalper)
        totalper = '   ' + totalper if len(totalper.split('.')[0]) == 1 else totalper
        totalper = '  ' + totalper if len(totalper.split('.')[0]) == 2 else totalper
        totalper = ' ' + totalper if len(totalper.split('.')[0]) == 3 else totalper
        totalper = totalper + '0' if len(totalper.split('.')[1]) == 1 else totalper
        totaleyun = format(self.totaleyun, ',')
        if len(totaleyun.split(',')) == 1:
            totaleyun = '         ' + totaleyun if len(totaleyun.split(',')[0]) == 1 else totaleyun
            totaleyun = '        ' + totaleyun if len(totaleyun.split(',')[0]) == 2 else totaleyun
            totaleyun = '       ' + totaleyun if len(totaleyun.split(',')[0]) == 3 else totaleyun
            totaleyun = '      ' + totaleyun if len(totaleyun.split(',')[0]) == 4 else totaleyun
        elif len(totaleyun.split(',')) == 2:
            totaleyun = '     ' + totaleyun if len(totaleyun.split(',')[0]) == 1 else totaleyun
            totaleyun = '    ' + totaleyun if len(totaleyun.split(',')[0]) == 2 else totaleyun
            totaleyun = '   ' + totaleyun if len(totaleyun.split(',')[0]) == 3 else totaleyun
            totaleyun = '  ' + totaleyun if len(totaleyun.split(',')[0]) == 4 else totaleyun
        elif len(totaleyun.split(',')) == 3:
            totaleyun = ' ' + totaleyun if len(totaleyun.split(',')[0]) == 1 else totaleyun
        return ticker, totalcount, avgholdday, totalcount_p, totalcount_m, plus_per, totalper, totaleyun


class Total:
    def __init__(self, q_, last_, num_):
        super().__init__()
        self.q = q_
        self.last = last_

        if type(num_[3]) == list:
            self.batting = num_[0]
            self.testperiod = num_[1]
            self.totaltime = num_[2]
            self.gap_ch = num_[3][0]
            self.avg_time = num_[4][0]
            self.gap_sm = num_[5][0]
            self.ch_low = num_[6][0]
            self.dm_low = num_[7][0]
            self.per_low = num_[8][0]
            self.per_high = num_[9][0]
            self.cs_per = num_[10][0]
        else:
            self.batting = num_[0]
            self.testperiod = num_[1]
            self.totaltime = num_[2]
            self.gap_ch = num_[3]
            self.avg_time = num_[4]
            self.gap_sm = num_[5]
            self.ch_low = num_[6]
            self.dm_low = num_[7]
            self.per_low = num_[8]
            self.per_high = num_[9]
            self.cs_per = num_[10]

        self.Start()

    def Start(self):
        columns1 = ['거래횟수', '평균보유기간', '익절', '손절', '승률', '수익률', '수익금']
        columns2 = ['필요자금', '종목출현빈도수', '거래횟수', '평균보유기간', '익절', '손절', '승률',
                    '평균수익률', '수익률합계', '수익금합계', '체결강도차이', '평균시간', '거래대금차이',
                    '체결강도하한', '누적거래대금하한', '등락율하한', '등락율상한', '청산수익률']
        df_back = pd.DataFrame(columns=columns1)
        df_tsg = pd.DataFrame(columns=['종목명', 'per', 'ttsg'])
        k = 0
        while True:
            data = self.q.get()
            if len(data) == 4:
                if data[0] in df_tsg.index:
                    df_tsg.at[data[0]] = df_tsg['종목명'][data[0]] + ';' + data[1], \
                                         df_tsg['per'][data[0]] + data[2], \
                                         df_tsg['ttsg'][data[0]] + data[3]
                else:
                    df_tsg.at[data[0]] = data[1], data[2], data[3]
            else:
                df_back.at[data[0]] = data[1], data[2], data[3], data[4], data[5], data[6], data[7]
                k += 1
            if k == self.last:
                break

        tsp = 0
        if len(df_back) > 0:
            text = [self.gap_ch, self.avg_time, self.gap_sm, self.ch_low, self.dm_low,
                    self.per_low, self.per_high, self.cs_per]
            print(f' {text}')
            tc = df_back['거래횟수'].sum()
            if tc != 0:
                pc = df_back['익절'].sum()
                mc = df_back['손절'].sum()
                pper = round(pc / tc * 100, 2)
                df_back_ = df_back[df_back['평균보유기간'] != 0]
                avghold = round(df_back_['평균보유기간'].sum() / len(df_back_), 2)
                avgsp = round(df_back['수익률'].sum() / tc, 2)
                tsg = int(df_back['수익금'].sum())
                onedaycount = round(tc / self.totaltime, 4)
                onegm = int(self.batting * onedaycount * avghold)
                if onegm < self.batting:
                    onegm = self.batting
                tsp = round(tsg / onegm * 100, 4)
                text = f" 종목당 배팅금액 {format(self.batting, ',')}원, 필요자금 {format(onegm, ',')}원, "\
                       f" 종목출현빈도수 {onedaycount}개/초, 거래횟수 {tc}회, 평균보유기간 {avghold}초,\n 익절 {pc}회, "\
                       f" 손절 {mc}회, 승률 {pper}%, 평균수익률 {avgsp}%, 수익률합계 {tsp}%, 수익금합계 {format(tsg, ',')}원"
                print(text)
                df_back = pd.DataFrame(
                    [[onegm, onedaycount, tc, avghold, pc, mc, pper, avgsp, tsp, tsg, self.gap_ch, self.avg_time,
                      self.gap_sm, self.ch_low, self.dm_low, self.per_low, self.per_high, self.cs_per]],
                    columns=columns2, index=[strf_time('%Y%m%d%H%M%S')])
                conn = sqlite3.connect(db_backtest)
                df_back.to_sql(f"{strf_time('%Y%m%d')}_2c", conn, if_exists='append', chunksize=1000)
                conn.close()

        if len(df_tsg) > 0:
            df_tsg['체결시간'] = df_tsg.index
            df_tsg.sort_values(by=['체결시간'], inplace=True)
            df_tsg['ttsg_cumsum'] = df_tsg['ttsg'].cumsum()
            df_tsg[['ttsg', 'ttsg_cumsum']] = df_tsg[['ttsg', 'ttsg_cumsum']].astype(int)
            conn = sqlite3.connect(db_backtest)
            df_tsg.to_sql(f"{strf_time('%Y%m%d')}_2t", conn, if_exists='replace', chunksize=1000)
            conn.close()
            df_tsg.plot(figsize=(12, 9), rot=45)
            plt.savefig(f"{graph_path}/C{strf_time('%Y%m%d')}_2.png")
            conn = sqlite3.connect(db_setting)
            cur = conn.cursor()
            query = f"UPDATE coin SET 체결강도차이2 = {self.gap_ch}, 평균시간2 = {self.avg_time}, "\
                    f"거래대금차이2 = {self.gap_sm}, 체결강도하한2 = {self.ch_low}, 누적거래대금하한2 = {self.dm_low}, "\
                    f"등락율하한2 = {self.per_low}, 등락율상한2 = {self.per_high}, 청산수익률2 = {self.cs_per}"
            cur.execute(query)
            conn.commit()
            conn.close()
        else:
            self.q.put(tsp)


if __name__ == "__main__":
    start = now()

    con = sqlite3.connect(db_coin_tick)
    df = pd.read_sql("SELECT name FROM sqlite_master WHERE TYPE = 'table'", con)
    con.close()

    table_list = list(df['name'].values)
    last = len(table_list)

    q = Queue()
    batting = int(sys.argv[1]) * 1000000
    testperiod = int(sys.argv[2])
    totaltime = int(sys.argv[3])
    gap_chs = [float(sys.argv[4]), float(sys.argv[5]), float(sys.argv[6]),
               float(sys.argv[7]), float(sys.argv[8]), float(sys.argv[9]), float(sys.argv[10])]
    avg_times = [int(sys.argv[13]), int(sys.argv[14]), int(sys.argv[15]),
                 int(sys.argv[16]), int(sys.argv[17]), int(sys.argv[18])]
    htsp = -1000
    high_var = []

    print(int(sys.argv[21]))
    for gap_ch in gap_chs:
        for avg_time in avg_times:
            num = [batting, testperiod, totaltime, gap_ch, avg_time, int(sys.argv[21]), float(sys.argv[25]),
                   int(sys.argv[29]), float(sys.argv[33]), float(sys.argv[37]), float(sys.argv[41])]
            w = Process(target=Total, args=(q, last, num))
            w.start()
            procs = []
            workcount = int(last / int(sys.argv[45])) + 1
            for j in range(0, last, workcount):
                ticker_list = table_list[j:j + workcount]
                p = Process(target=BackTester2Coin, args=(q, ticker_list, num, False))
                procs.append(p)
                p.start()
            for p in procs:
                p.join()
            w.join()
            sp = q.get()
            if sp >= htsp:
                htsp = sp
                high_var = num
                print(f' 최고수익률 갱신 {htsp}%')

    gap_ch = [high_var[3] - float(sys.argv[11]) * 9, high_var[3] + float(sys.argv[11]) * 9,
              float(sys.argv[11]), float(sys.argv[12])]
    avg_time = [high_var[4], high_var[4], int(sys.argv[19]), int(sys.argv[20])]
    gap_sm = [int(sys.argv[21]), int(sys.argv[22]), int(sys.argv[23]), int(sys.argv[24])]
    ch_low = [float(sys.argv[25]), float(sys.argv[26]), float(sys.argv[27]), float(sys.argv[28])]
    dm_low = [int(sys.argv[29]), int(sys.argv[30]), int(sys.argv[31]), int(sys.argv[32])]
    per_low = [float(sys.argv[33]), float(sys.argv[34]), float(sys.argv[35]), float(sys.argv[36])]
    per_high = [float(sys.argv[37]), float(sys.argv[38]), float(sys.argv[39]), float(sys.argv[40])]
    cs_per = [float(sys.argv[41]), float(sys.argv[42]), float(sys.argv[43]), float(sys.argv[44])]
    num = [batting, testperiod, totaltime, gap_ch, avg_time, gap_sm, ch_low, dm_low, per_low, per_high, cs_per]

    ogin_var = high_var[3]
    high_var = high_var[3]

    i = 3
    while True:
        w = Process(target=Total, args=(q, last, num))
        w.start()
        procs = []
        workcount = int(last / int(sys.argv[45])) + 1
        for j in range(0, last, workcount):
            ticker_list = table_list[j:j + workcount]
            p = Process(target=BackTester2Coin, args=(q, ticker_list, num, False))
            procs.append(p)
            p.start()
        for p in procs:
            p.join()
        w.join()
        sp = q.get()
        if sp >= htsp:
            htsp = sp
            high_var = num[i][0]
            print(f' 최고수익률 갱신 {htsp}%')
        if num[i][0] == num[i][1]:
            num[i][0] = high_var
            if num[i][2] != num[i][3]:
                if num[i][0] != ogin_var:
                    num[i][0] -= num[i][2]
                    num[i][1] = round(num[i][0] + num[i][2] * 2 - num[i][3], 1)
                else:
                    num[i][1] = round(num[i][0] + num[i][2] - num[i][3], 1)
                num[i][2] = num[i][3]
            elif i < len(num) - 1:
                i += 1
                ogin_var = num[i][0]
                high_var = num[i][0]
                if i == 4:
                    if num[i][0] != int(sys.argv[13]):
                        num[i][0] -= num[i][2]
                        num[i][1] = round(num[i][0] + num[i][2] * 2 - num[i][3], 1)
                    else:
                        num[i][1] = round(num[i][0] + num[i][2] - num[i][3], 1)
                    num[i][2] = num[i][3]
            else:
                break
        num[i][0] = round(num[i][0] + num[i][2], 1)

    w = Process(target=Total, args=(q, last, num))
    w.start()
    procs = []
    workcount = int(last / float(sys.argv[45])) + 1
    for j in range(0, last, workcount):
        db_list = table_list[j:j + workcount]
        p = Process(target=BackTester2Coin, args=(q, db_list, num, True))
        procs.append(p)
        p.start()
    for p in procs:
        p.join()
    w.join()

    end = now()
    print(f" 백테스팅 소요시간 {end - start}")
