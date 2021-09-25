import os
import sys
import time
import sqlite3
import warnings
import pythoncom
import numpy as np
import pandas as pd
from PyQt5 import QtWidgets
from PyQt5.QAxContainer import QAxWidget
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
from utility.static import *
from utility.setting import *
warnings.filterwarnings("ignore", category=np.VisibleDeprecationWarning)


class UpdaterTickKiwoom:
    def __init__(self, windowQ, queryQ, tickQ):
        self.windowQ = windowQ
        self.queryQ = queryQ
        self.tickQ = tickQ

        self.dict_df = {}
        self.time_info = now()
        self.str_tday = strf_time('%Y%m%d')
        self.Start()

    def Start(self):
        while True:
            tick = self.tickQ.get()
            if len(tick) != 2:
                self.UpdateTickData(tick[0], tick[1], tick[2], tick[3], tick[4], tick[5], tick[6], tick[7],
                                    tick[8], tick[9], tick[10], tick[11], tick[12], tick[13], tick[14],
                                    tick[15], tick[16], tick[17], tick[18], tick[19], tick[20])
            elif tick[0] == '틱데이터저장':
                self.PutTickData(tick[1])

    def UpdateTickData(self, code, c, o, h, low, per, dm, ch, vp, vitime, vid5,
                       s1jr, s2jr, b1jr, b2jr, s1hg, s2hg, b1hg, b2hg, d, receiv_time):
        try:
            hlm = int(round((h + low) / 2))
            hlmp = round((c / hlm - 1) * 100, 2)
        except ZeroDivisionError:
            return
        d = self.str_tday + d
        if code not in self.dict_df.keys():
            self.dict_df[code] = pd.DataFrame(
                [[c, o, h, per, hlmp, dm, dm, ch, vp, vitime, vid5, s1jr, s2jr, b1jr, b2jr, s1hg, s2hg, b1hg, b2hg]],
                columns=['현재가', '시가', '고가', '등락율', '고저평균대비등락율', '거래대금', '누적거래대금', '체결강도',
                         '전일거래량대비', 'VI발동시간', '상승VID5가격', '매도호가2', '매도호가1', '매수호가1', '매수호가2',
                         '매도잔량2', '매도잔량1', '매수잔량1', '매수잔량2'],
                index=[d])
        else:
            sm = int(dm - self.dict_df[code]['누적거래대금'][-1])
            self.dict_df[code].at[d] = \
                c, o, h, per, hlmp, sm, dm, ch, vp, vitime, vid5, s1jr, s2jr, b1jr, b2jr, s1hg, s2hg, b1hg, b2hg

        if now() > self.time_info:
            self.UpdateInfo(receiv_time)
            self.time_info = timedelta_sec(60)

    def UpdateInfo(self, receiv_time):
        gap = (now() - receiv_time).total_seconds()
        self.windowQ.put([ui_num['S단순텍스트'], f'수신시간과 갱신시간의 차이는 [{gap}]초입니다.'])

    def PutTickData(self, codes):
        for code in list(self.dict_df.keys()):
            if code in codes:
                columns = ['현재가', '시가', '고가', '거래대금', '누적거래대금', '상승VID5가격',
                           '매도호가2', '매도호가1', '매수호가1', '매수호가2', '매도잔량2', '매도잔량1', '매수잔량1', '매수잔량2']
                self.dict_df[code][columns] = self.dict_df[code][columns].astype(int)
            else:
                del self.dict_df[code]
        self.queryQ.put([3, self.dict_df])
        sys.exit()


class CollectorTickKiwoom:
    app = QtWidgets.QApplication(sys.argv)

    def __init__(self, windowQ, collectorQ, soundQ, queryQ, teleQ,
                 tick1Q, tick2Q, tick3Q, tick4Q, tick5Q, tick6Q, tick7Q, tick8Q):
        self.windowQ = windowQ
        self.collectorQ = collectorQ
        self.soundQ = soundQ
        self.queryQ = queryQ
        self.teleQ = teleQ
        self.tick1Q = tick1Q
        self.tick2Q = tick2Q
        self.tick3Q = tick3Q
        self.tick4Q = tick4Q
        self.tick5Q = tick5Q
        self.tick6Q = tick6Q
        self.tick7Q = tick7Q
        self.tick8Q = tick8Q

        self.dict_code = {
            '틱0': [],
            '틱1': [],
            '틱2': [],
            '틱3': [],
            '틱4': [],
            '틱5': [],
            '틱6': [],
            '틱7': [],
            '틱8': []
        }
        self.dict_bool = {
            '알림소리': False,

            'TR수신': False,
            'TR다음': False,
            'CD수신': False,
            'CR수신': False
        }
        self.dict_intg = {'장운영상태': 1}

        self.df_mt = pd.DataFrame(columns=['거래대금상위100'])
        self.df_tr = None
        self.dict_item = None
        self.dict_vipr = {}
        self.dict_tick = {}
        self.dict_cond = {}
        self.name_code = {}
        self.list_code = []
        self.list_trcd = []
        self.list_kosd = None
        self.time_mtop = now()
        self.str_trname = None
        self.str_tday = strf_time('%Y%m%d')
        self.str_jcct = self.str_tday + '090000'

        remaintime = (strp_time('%Y%m%d%H%M%S', self.str_tday + '090100') - now()).total_seconds()
        exittime = timedelta_sec(remaintime) if remaintime > 0 else timedelta_sec(600)
        self.dict_time = {'휴무종료': exittime}

        self.ocx = QAxWidget('KHOPENAPI.KHOpenAPICtrl.1')
        self.ocx.OnEventConnect.connect(self.OnEventConnect)
        self.ocx.OnReceiveTrData.connect(self.OnReceiveTrData)
        self.ocx.OnReceiveRealData.connect(self.OnReceiveRealData)
        self.ocx.OnReceiveTrCondition.connect(self.OnReceiveTrCondition)
        self.ocx.OnReceiveConditionVer.connect(self.OnReceiveConditionVer)
        self.ocx.OnReceiveRealCondition.connect(self.OnReceiveRealCondition)
        self.Start()

    def Start(self):
        self.CommConnect()
        self.EventLoop()

    def CommConnect(self):
        self.ocx.dynamicCall('CommConnect()')
        while not self.dict_bool['로그인']:
            pythoncom.PumpWaitingMessages()

        self.dict_bool['CD수신'] = False
        self.ocx.dynamicCall('GetConditionLoad()')
        while not self.dict_bool['CD수신']:
            pythoncom.PumpWaitingMessages()

        self.list_kosd = self.GetCodeListByMarket('10')
        list_code = self.GetCodeListByMarket('0') + self.list_kosd
        df = pd.DataFrame(columns=['종목명'])
        for code in list_code:
            name = self.GetMasterCodeName(code)
            df.at[code] = name
            self.name_code[name] = code

        self.queryQ.put([3, df, 'codename', 'replace'])

        data = self.ocx.dynamicCall('GetConditionNameList()')
        conditions = data.split(';')[:-1]
        for condition in conditions:
            cond_index, cond_name = condition.split('^')
            self.dict_cond[int(cond_index)] = cond_name

        con = sqlite3.connect(db_setting)
        df = pd.read_sql('SELECT * FROM stock', con)
        df = df.set_index('index')
        self.dict_bool['알림소리'] = df['알림소리'][0]
        con.close()

        self.windowQ.put([ui_num['S단순텍스트'], '시스템 명령 실행 알림 - OpenAPI 로그인 완료'])

    def EventLoop(self):
        self.OperationRealreg()
        self.ViRealreg()
        int_time = int(strf_time('%H%M%S'))
        while True:
            if not self.collectorQ.empty():
                work = self.collectorQ.get()
                if type(work) == list:
                    self.UpdateRealreg(work)
                elif type(work) == str:
                    self.RunWork(work)
            if self.dict_intg['장운영상태'] == 1 and now() > self.dict_time['휴무종료']:
                break
            if self.dict_intg['장운영상태'] == 3:
                if int_time < stock_init_time <= int(strf_time('%H%M%S')):
                    self.ConditionSearchStart()
                if int_time < stock_exit_time + 100 <= int(strf_time('%H%M%S')):
                    self.ConditionSearchStop()
                    self.RemoveRealreg()
                    self.SaveDatabase()
                    break

            if now() > self.time_mtop:
                if len(self.df_mt) > 0:
                    self.UpdateMoneyTop()
                self.time_mtop = timedelta_sec(+1)

            time_loop = timedelta_sec(0.25)
            while now() < time_loop:
                pythoncom.PumpWaitingMessages()
                time.sleep(0.0001)

            int_time = int(strf_time('%H%M%S'))

        self.windowQ.put([ui_num['S단순텍스트'], '시스템 명령 실행 알림 - 콜렉터를 종료합니다.'])
        if self.dict_bool['알림소리']:
            self.soundQ.put('주식 콜렉터를 종료합니다.')
        self.teleQ.put('주식 콜렉터를 종료하였습니다.')
        sys.exit()

    def UpdateRealreg(self, rreg):
        sn = rreg[0]
        if len(rreg) == 2:
            self.ocx.dynamicCall('SetRealRemove(QString, QString)', rreg)
            self.windowQ.put([ui_num['S단순텍스트'], f'실시간 알림 중단 완료 - 모든 실시간 데이터 수신 중단'])
        elif len(rreg) == 4:
            ret = self.ocx.dynamicCall('SetRealReg(QString, QString, QString, QString)', rreg)
            result = '완료' if ret == 0 else '실패'
            if sn == sn_oper:
                self.windowQ.put([ui_num['S단순텍스트'], f'실시간 알림 등록 {result} - 장운영시간 [{sn}]'])
            else:
                self.windowQ.put([ui_num['S단순텍스트'], f"실시간 알림 등록 {result} - [{sn}] 종목갯수 {len(rreg[1].split(';'))}"])

    def RunWork(self, work):
        if work == '틱데이터 저장 완료':
            self.dict_bool['틱데이터저장'] = True

    def OperationRealreg(self):
        self.collectorQ.put([sn_oper, ' ', '215;20;214', 0])
        self.dict_code['틱0'] = self.SendCondition(sn_oper, self.dict_cond[1], 1, 0)
        self.dict_code['틱1'] = [code for i, code in enumerate(self.dict_code['틱0']) if i % 8 == 0]
        self.dict_code['틱2'] = [code for i, code in enumerate(self.dict_code['틱0']) if i % 8 == 1]
        self.dict_code['틱3'] = [code for i, code in enumerate(self.dict_code['틱0']) if i % 8 == 2]
        self.dict_code['틱4'] = [code for i, code in enumerate(self.dict_code['틱0']) if i % 8 == 3]
        self.dict_code['틱5'] = [code for i, code in enumerate(self.dict_code['틱0']) if i % 8 == 4]
        self.dict_code['틱6'] = [code for i, code in enumerate(self.dict_code['틱0']) if i % 8 == 5]
        self.dict_code['틱7'] = [code for i, code in enumerate(self.dict_code['틱0']) if i % 8 == 6]
        self.dict_code['틱8'] = [code for i, code in enumerate(self.dict_code['틱0']) if i % 8 == 7]
        k = 0
        for i in range(0, len(self.dict_code['틱0']), 100):
            self.collectorQ.put([sn_jchj + k, ';'.join(self.dict_code['틱0'][i:i + 100]),
                                 '10;12;14;30;228;41;61;71;81', 1])
            k += 1

    def ViRealreg(self):
        self.Block_Request('opt10054', 시장구분='000', 장전구분='1', 종목코드='', 발동구분='1', 제외종목='111111011',
                           거래량구분='0', 거래대금구분='0', 발동방향='0', output='발동종목', next=0)
        self.windowQ.put([ui_num['S단순텍스트'], '시스템 명령 실행 알림 - VI발동해제 등록 완료'])
        self.windowQ.put([ui_num['S단순텍스트'], '시스템 명령 실행 알림 - 시스템 시작 완료'])
        if self.dict_bool['알림소리']:
            self.soundQ.put('주식 콜렉터를 시작하였습니다.')

    def ConditionSearchStart(self):
        self.list_code = self.SendCondition(sn_cond, self.dict_cond[0], 0, 1)
        self.df_mt.at[self.str_tday + '090000'] = ';'.join(self.list_code)

    def ConditionSearchStop(self):
        self.ocx.dynamicCall("SendConditionStop(QString, QString, int)", sn_cond, self.dict_cond[0], 0)

    def RemoveRealreg(self):
        self.collectorQ.put(['ALL', 'ALL'])
        self.windowQ.put([ui_num['S단순텍스트'], '시스템 명령 실행 알림 - 실시간 데이터 중단 완료'])

    def SaveDatabase(self):
        self.queryQ.put([3, self.df_mt, 'moneytop', 'append'])
        con = sqlite3.connect(db_tradelist)
        df = pd.read_sql(f"SELECT * FROM tradelist WHERE 체결시간 LIKE '{self.str_tday}%'", con)
        con.close()
        df = df.set_index('index')
        codes = []
        for index in df.index:
            code = self.name_code[df['종목명'][index]]
            if code not in codes:
                codes.append(code)
        self.tick1Q.put(['틱데이터저장', codes])
        self.tick2Q.put(['틱데이터저장', codes])
        self.tick3Q.put(['틱데이터저장', codes])
        self.tick4Q.put(['틱데이터저장', codes])
        self.tick5Q.put(['틱데이터저장', codes])
        self.tick6Q.put(['틱데이터저장', codes])
        self.tick7Q.put(['틱데이터저장', codes])
        self.tick8Q.put(['틱데이터저장', codes])
        self.dict_bool['DB저장'] = True

    def OnEventConnect(self, err_code):
        if err_code == 0:
            self.dict_bool['로그인'] = True

    def OnReceiveConditionVer(self, ret, msg):
        if msg == '':
            return
        if ret == 1:
            self.dict_bool['CD수신'] = True

    def OnReceiveTrCondition(self, screen, code_list, cond_name, cond_index, nnext):
        if screen == "" and cond_name == "" and cond_index == "" and nnext == "":
            return
        codes = code_list.split(';')[:-1]
        self.list_trcd = codes
        self.dict_bool['CR수신'] = True

    def OnReceiveRealCondition(self, code, IorD, cname, cindex):
        if cname == "":
            return

        if IorD == "I" and cindex == "0" and code not in self.list_code:
            self.list_code.append(code)
        elif IorD == "D" and cindex == "0" and code in self.list_code:
            self.list_code.remove(code)

    def OnReceiveRealData(self, code, realtype, realdata):
        if realdata == '':
            return

        if realtype == '장시작시간':
            if self.dict_intg['장운영상태'] == 8:
                return
            try:
                self.dict_intg['장운영상태'] = int(self.GetCommRealData(code, 215))
                current = self.GetCommRealData(code, 20)
                remain = self.GetCommRealData(code, 214)
            except Exception as e:
                self.windowQ.put([ui_num['S단순텍스트'], f'OnReceiveRealData 장시작시간 {e}'])
            else:
                self.windowQ.put([ui_num['S단순텍스트'], f"장운영 시간 수신 알림 - {self.dict_intg['장운영상태']} "
                                                    f'{current[:2]}:{current[2:4]}:{current[4:]} '
                                                    f'남은시간 {remain[:2]}:{remain[2:4]}:{remain[4:]}'])
        elif realtype == 'VI발동/해제':
            try:
                code = self.GetCommRealData(code, 9001).strip('A').strip('Q')
                gubun = self.GetCommRealData(code, 9068)
                name = self.GetMasterCodeName(code)
            except Exception as e:
                self.windowQ.put([ui_num['S단순텍스트'], f'OnReceiveRealData VI발동/해제 {e}'])
            else:
                if gubun == '1' and code in self.dict_code['틱0'] and \
                        (code not in self.dict_vipr.keys() or
                         (self.dict_vipr[code][0] and now() > self.dict_vipr[code][1])):
                    self.UpdateViPriceDown5(code, name)
        elif realtype == '주식체결':
            try:
                d = self.GetCommRealData(code, 20)
            except Exception as e:
                self.windowQ.put([ui_num['S단순텍스트'], f'OnReceiveRealData 주식체결 {e}'])
            else:
                if d != self.str_jcct[8:]:
                    self.str_jcct = self.str_tday + d
                try:
                    c = abs(int(self.GetCommRealData(code, 10)))
                    o = abs(int(self.GetCommRealData(code, 16)))
                except Exception as e:
                    self.windowQ.put([ui_num['S단순텍스트'], f'OnReceiveRealData 주식체결 {e}'])
                else:
                    if code not in self.dict_vipr.keys():
                        self.InsertViPriceDown5(code, o)
                    if code in self.dict_vipr.keys() and not self.dict_vipr[code][0] and now() > self.dict_vipr[code][1]:
                        self.UpdateViPriceDown5(code, c)
                    if code in self.dict_tick.keys() and d == self.dict_tick[code][0]:
                        return
                    try:
                        h = abs(int(self.GetCommRealData(code, 17)))
                        low = abs(int(self.GetCommRealData(code, 18)))
                        per = float(self.GetCommRealData(code, 12))
                        dm = int(self.GetCommRealData(code, 14))
                        ch = float(self.GetCommRealData(code, 228))
                        vp = abs(float(self.GetCommRealData(code, 30)))
                    except Exception as e:
                        self.windowQ.put([ui_num['S단순텍스트'], f'OnReceiveRealData 주식체결 {e}'])
                    else:
                        self.UpdateTickData(code, c, o, h, low, per, dm, ch, vp, d)
        elif realtype == '주식호가잔량':
            try:
                s1jr = int(self.GetCommRealData(code, 61))
                s2jr = int(self.GetCommRealData(code, 62))
                b1jr = int(self.GetCommRealData(code, 71))
                b2jr = int(self.GetCommRealData(code, 72))
                s1hg = abs(int(self.GetCommRealData(code, 41)))
                s2hg = abs(int(self.GetCommRealData(code, 42)))
                b1hg = abs(int(self.GetCommRealData(code, 51)))
                b2hg = abs(int(self.GetCommRealData(code, 52)))
            except Exception as e:
                self.windowQ.put([ui_num['S단순텍스트'], f'OnReceiveRealData 주식호가잔량 {e}'])
            else:
                self.UpdateHoga(code, s1jr, s2jr, b1jr, b2jr, s1hg, s2hg, b1hg, b2hg)

    def InsertViPriceDown5(self, code, o):
        vid5 = self.GetVIPriceDown5(code, o)
        self.dict_vipr[code] = [True, timedelta_sec(-180), vid5]

    def GetVIPriceDown5(self, code, std_price):
        vi = std_price * 1.1
        x = self.GetHogaunit(code, vi)
        if vi % x != 0:
            vi = vi + (x - vi % x)
        return int(vi - x * 5)

    def GetHogaunit(self, code, price):
        if price < 1000:
            x = 1
        elif 1000 <= price < 5000:
            x = 5
        elif 5000 <= price < 10000:
            x = 10
        elif 10000 <= price < 50000:
            x = 50
        elif code in self.list_kosd:
            x = 100
        elif 50000 <= price < 100000:
            x = 100
        elif 100000 <= price < 500000:
            x = 500
        else:
            x = 1000
        return x

    def UpdateViPriceDown5(self, code, key):
        if type(key) == str:
            if code in self.dict_vipr.keys():
                self.dict_vipr[code][0] = False
                self.dict_vipr[code][1] = timedelta_sec(5)
            else:
                self.dict_vipr[code] = [False, timedelta_sec(5), 0]
        elif type(key) == int:
            vid5 = self.GetVIPriceDown5(code, key)
            self.dict_vipr[code] = [True, timedelta_sec(5), vid5]

    def UpdateTickData(self, code, c, o, h, low, per, dm, ch, vp, d):
        vitime = strf_time('%Y%m%d%H%M%S', self.dict_vipr[code][1])
        vi = self.dict_vipr[code][2]
        try:
            s1jr, s2jr, b1jr, b2jr, s1hg, s2hg, b1hg, b2hg = self.dict_tick[code][1:]
            self.dict_tick[code][0] = d
        except KeyError:
            s1jr, s2jr, b1jr, b2jr, s1hg, s2hg, b1hg, b2hg = 0, 0, 0, 0, 0, 0, 0, 0
            self.dict_tick[code] = [d, 0, 0, 0, 0, 0, 0, 0, 0]
        data = [code, c, o, h, low, per, dm, ch, vp, vitime, vi,
                s1jr, s2jr, b1jr, b2jr, s1hg, s2hg, b1hg, b2hg, d, now()]
        if code in self.dict_code['틱1']:
            self.tick1Q.put(data)
        elif code in self.dict_code['틱2']:
            self.tick2Q.put(data)
        elif code in self.dict_code['틱3']:
            self.tick3Q.put(data)
        elif code in self.dict_code['틱4']:
            self.tick4Q.put(data)
        elif code in self.dict_code['틱5']:
            self.tick5Q.put(data)
        elif code in self.dict_code['틱6']:
            self.tick6Q.put(data)
        elif code in self.dict_code['틱7']:
            self.tick7Q.put(data)
        elif code in self.dict_code['틱8']:
            self.tick8Q.put(data)

    def UpdateHoga(self, code, s1jr, s2jr, b1jr, b2jr, s1hg, s2hg, b1hg, b2hg):
        try:
            d = self.dict_tick[code][0]
        except KeyError:
            d = '090000'
        self.dict_tick[code] = [d, s1jr, s2jr, b1jr, b2jr, s1hg, s2hg, b1hg, b2hg]

    def UpdateMoneyTop(self):
        timetype = '%Y%m%d%H%M%S'
        list_text = ';'.join(self.list_code)
        curr_datetime = strp_time(timetype, self.str_jcct)
        last_datetime = strp_time(timetype, self.df_mt.index[-1])
        gap_seconds = (curr_datetime - last_datetime).total_seconds()
        pre_time2 = strf_time(timetype, timedelta_sec(-2, curr_datetime))
        pre_time1 = strf_time(timetype, timedelta_sec(-1, curr_datetime))
        if 1 <= gap_seconds < 2:
            self.df_mt.at[pre_time1] = list_text
        elif 2 <= gap_seconds < 3:
            self.df_mt.at[pre_time2] = list_text
            self.df_mt.at[pre_time1] = list_text
        self.df_mt.at[self.str_jcct] = list_text

    def OnReceiveTrData(self, screen, rqname, trcode, record, nnext):
        if screen == '' and record == '':
            return
        items = None
        self.dict_bool['TR다음'] = True if nnext == '2' else False
        for output in self.dict_item['output']:
            record = list(output.keys())[0]
            items = list(output.values())[0]
            if record == self.str_trname:
                break
        rows = self.ocx.dynamicCall('GetRepeatCnt(QString, QString)', trcode, rqname)
        if rows == 0:
            rows = 1
        df2 = []
        for row in range(rows):
            row_data = []
            for item in items:
                data = self.ocx.dynamicCall('GetCommData(QString, QString, int, QString)', trcode, rqname, row, item)
                row_data.append(data.strip())
            df2.append(row_data)
        df = pd.DataFrame(data=df2, columns=items)
        self.df_tr = df
        self.dict_bool['TR수신'] = True

    def Block_Request(self, *args, **kwargs):
        trcode = args[0].lower()
        lines = readEnc(trcode)
        self.dict_item = parseDat(trcode, lines)
        self.str_trname = kwargs['output']
        nnext = kwargs['next']
        for i in kwargs:
            if i.lower() != 'output' and i.lower() != 'next':
                self.ocx.dynamicCall('SetInputValue(QString, QString)', i, kwargs[i])
        self.dict_bool['TR수신'] = False
        self.dict_bool['TR다음'] = False
        self.ocx.dynamicCall('CommRqData(QString, QString, int, QString)', self.str_trname, trcode, nnext, sn_brrq)
        sleeptime = timedelta_sec(0.25)
        while not self.dict_bool['TR수신'] or now() < sleeptime:
            pythoncom.PumpWaitingMessages()
        return self.df_tr

    def SendCondition(self, screen, cond_name, cond_index, search):
        self.dict_bool['CR수신'] = False
        self.ocx.dynamicCall('SendCondition(QString, QString, int, int)', screen, cond_name, cond_index, search)
        while not self.dict_bool['CR수신']:
            pythoncom.PumpWaitingMessages()
        return self.list_trcd

    def GetMasterCodeName(self, code):
        return self.ocx.dynamicCall('GetMasterCodeName(QString)', code)

    def GetCodeListByMarket(self, market):
        data = self.ocx.dynamicCall('GetCodeListByMarket(QString)', market)
        tokens = data.split(';')[:-1]
        return tokens

    def GetCommRealData(self, code, fid):
        return self.ocx.dynamicCall('GetCommRealData(QString, int)', code, fid)
