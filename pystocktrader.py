import sys
import psutil
import sqlite3
import logging
import subprocess
import pandas as pd
from PyQt5.QtTest import QTest
from multiprocessing import Process, Queue
from trader.trader_upbit import TraderUpbit
from trader.trader_kiwoom import TraderKiwoom
from trader.strategy_coin import StrategyCoin
from trader.strategy_stock import StrategyStock
from collector.collector_tick_kiwoom import UpdaterTickKiwoom, CollectorTickKiwoom
from collector.collector_tick_upbit import WebsTicker, WebsOrderbook, UpdaterTickUpbit
from utility.setui import *
from utility.sound import Sound
from utility.query import Query
from utility.telegram_msg import TelegramMsg
from utility.static import now, strf_time, strp_time, changeFormat, thread_decorator

conn = sqlite3.connect(db_setting)
dfs = pd.read_sql('SELECT * FROM kiwoom', conn)
dfs = dfs.set_index('index')

KIWOOM_ACCOUNT1 = True if len(dfs) > 0 and dfs['아이디1'][0] != '' else False
KIWOOM_ACCOUNT2 = True if len(dfs) > 0 and dfs['아이디2'][0] != '' else False

dfs = pd.read_sql('SELECT * FROM upbit', conn)
dfs = dfs.set_index('index')

UPBIT_ACCOUNT = True if len(dfs) > 0 and dfs['Access_key'][0] != '' else False

dfs = pd.read_sql('SELECT * FROM main', conn)
dfs = dfs.set_index('index')
conn.close()

if len(dfs) > 0:
    KIWOOM_COLLECTOR = dfs['키움콜렉터'][0]
    KIWOOM_TRADER = dfs['키움트레이더'][0]
    UPBIT_COLLECTOR = dfs['업비트콜렉터'][0]
    UPBIT_TRADER = dfs['업비트트레이더'][0]
else:
    KIWOOM_COLLECTOR = False
    KIWOOM_TRADER = False
    UPBIT_COLLECTOR = False
    UPBIT_TRADER = False


class Window(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        self.log1 = logging.getLogger('Stock')
        self.log1.setLevel(logging.INFO)
        filehandler = logging.FileHandler(filename=f"{system_path}/log/S{strf_time('%Y%m%d')}.txt", encoding='utf-8')
        self.log1.addHandler(filehandler)

        self.log2 = logging.getLogger('Coin')
        self.log2.setLevel(logging.INFO)
        filehandler = logging.FileHandler(filename=f"{system_path}/log/C{strf_time('%Y%m%d')}.txt", encoding='utf-8')
        self.log2.addHandler(filehandler)

        SetUI(self)

        self.cpu_per = 0
        self.int_time = int(strf_time('%H%M%S'))
        self.dict_name = {}
        self.dict_intg = {}

        con = sqlite3.connect(db_setting)
        df = pd.read_sql('SELECT * FROM stock', con)
        df = df.set_index('index')
        self.dict_intg['체결강도차이1'] = df['체결강도차이'][0]
        self.dict_intg['평균시간1'] = df['평균시간'][0]
        self.dict_intg['거래대금차이1'] = df['거래대금차이'][0]
        self.dict_intg['체결강도하한1'] = df['체결강도하한'][0]
        self.dict_intg['누적거래대금하한1'] = df['누적거래대금하한'][0]
        self.dict_intg['등락율하한1'] = df['등락율하한'][0]
        self.dict_intg['등락율상한1'] = df['등락율상한'][0]
        self.dict_intg['청산수익률1'] = df['청산수익률'][0]
        con.close()

        con = sqlite3.connect(db_setting)
        df = pd.read_sql('SELECT * FROM coin', con)
        df = df.set_index('index')
        self.dict_intg['체결강도차이2'] = df['체결강도차이'][0]
        self.dict_intg['평균시간2'] = df['평균시간'][0]
        self.dict_intg['거래대금차이2'] = df['거래대금차이'][0]
        self.dict_intg['체결강도하한2'] = df['체결강도하한'][0]
        self.dict_intg['누적거래대금하한2'] = df['누적거래대금하한'][0]
        self.dict_intg['등락율하한2'] = df['등락율하한'][0]
        self.dict_intg['등락율상한2'] = df['등락율상한'][0]
        self.dict_intg['청산수익률2'] = df['청산수익률'][0]
        con.close()

        self.writer = Writer()
        self.writer.data1.connect(self.UpdateTexedit)
        self.writer.data2.connect(self.UpdateTablewidget)
        self.writer.data3.connect(self.UpdateGaonsimJongmok)
        self.writer.start()

        self.qtimer1 = QtCore.QTimer()
        self.qtimer1.setInterval(1000)
        self.qtimer1.timeout.connect(self.ProcessStart)
        self.qtimer1.start()

        self.qtimer2 = QtCore.QTimer()
        self.qtimer2.setInterval(500)
        self.qtimer2.timeout.connect(self.UpdateProgressBar)
        self.qtimer2.start()

        self.qtimer3 = QtCore.QTimer()
        self.qtimer3.setInterval(500)
        self.qtimer3.timeout.connect(self.UpdateCpuper)
        self.qtimer3.start()

        self.websocket_ticker = WebsTicker(tick9Q, tick10Q)
        self.websocket_orderbook = WebsOrderbook(tick9Q, tick10Q)
        self.trader_upbit = TraderUpbit(windowQ, coinQ, queryQ, soundQ, cstgQ, teleQ)

        self.backtester_count = 0
        self.backtester_process = None
        self.strategy_process = Process(target=StrategyCoin, args=(windowQ, coinQ, queryQ, cstgQ), daemon=True)
        self.coin_tickupdater1_process = Process(target=UpdaterTickUpbit, args=(windowQ, queryQ, tick9Q), daemon=True)
        self.coin_tickupdater2_process = Process(target=UpdaterTickUpbit, args=(windowQ, queryQ, tick10Q), daemon=True)

    def ProcessStart(self):
        if now().weekday() not in [6, 7]:
            if KIWOOM_COLLECTOR and self.int_time < stock_vjup_time <= int(strf_time('%H%M%S')):
                self.backtester_count = 0
                self.backtester_process = None
                if KIWOOM_ACCOUNT2:
                    subprocess.Popen(f'python {system_path}/login_kiwoom/versionupdater.py')
                else:
                    text = '키움증권 두번째 계정이 설정되지 않아 버전 업그레이드를 실행할 수 없습니다.'
                    windowQ.put([ui_num['S단순텍스트'], text])

            if KIWOOM_COLLECTOR and self.int_time < stock_alg2_time <= int(strf_time('%H%M%S')):
                if KIWOOM_ACCOUNT2:
                    subprocess.Popen(f'python {system_path}/login_kiwoom/autologin2.py')
                else:
                    text = '키움증권 두번째 계정이 설정되지 않아 자동로그인설정을 실행할 수 없습니다.'
                    windowQ.put([ui_num['S단순텍스트'], text])

            if KIWOOM_COLLECTOR and self.int_time < stock_coll_time <= int(strf_time('%H%M%S')):
                Process(target=UpdaterTickKiwoom, args=(windowQ, queryQ, tick1Q), daemon=True).start()
                Process(target=UpdaterTickKiwoom, args=(windowQ, queryQ, tick2Q), daemon=True).start()
                Process(target=UpdaterTickKiwoom, args=(windowQ, queryQ, tick3Q), daemon=True).start()
                Process(target=UpdaterTickKiwoom, args=(windowQ, queryQ, tick4Q), daemon=True).start()
                Process(target=UpdaterTickKiwoom, args=(windowQ, queryQ, tick5Q), daemon=True).start()
                Process(target=UpdaterTickKiwoom, args=(windowQ, queryQ, tick6Q), daemon=True).start()
                Process(target=UpdaterTickKiwoom, args=(windowQ, queryQ, tick7Q), daemon=True).start()
                Process(target=UpdaterTickKiwoom, args=(windowQ, queryQ, tick8Q), daemon=True).start()
                Process(target=CollectorTickKiwoom,
                        args=(windowQ, collectorQ, soundQ, queryQ, teleQ, tick1Q, tick2Q, tick3Q,
                              tick4Q, tick5Q, tick6Q, tick7Q, tick8Q), daemon=True).start()
                text = '주식 콜렉터를 시작하였습니다.'
                soundQ.put(text)
                teleQ.put(text)

            if KIWOOM_TRADER and self.int_time < stock_alg1_time <= int(strf_time('%H%M%S')):
                if KIWOOM_ACCOUNT1:
                    subprocess.Popen(f'python {system_path}/login_kiwoom/autologin1.py')
                else:
                    text = '키움증권 첫번째 계정이 설정되지 않아 자동로그인설정을 실행할 수 없습니다.'
                    windowQ.put([ui_num['S로그텍스트'], text])

            if KIWOOM_TRADER and self.int_time < stock_trad_time <= int(strf_time('%H%M%S')):
                if KIWOOM_ACCOUNT1:
                    self.SetColumnsGJ('S')
                    Process(target=StrategyStock, args=(windowQ, stockQ, sstgQ), daemon=True).start()
                    Process(target=TraderKiwoom, args=(windowQ, stockQ, sstgQ, soundQ, queryQ, teleQ),
                            daemon=True).start()
                    text = '주식 트레이더를 시작하였습니다.'
                    soundQ.put(text)
                    teleQ.put(text)
                else:
                    text = '키움증권 첫번째 계정이 설정되지 않아 트레이더를 실행할 수 없습니다.'
                    windowQ.put([ui_num['S로그텍스트'], text])

        if backtest_time < self.int_time < stock_vjup_time:
            if self.backtester_count == 0 and (self.backtester_process is None or self.backtester_process.poll() == 0):
                self.ButtonClicked_8()
                QTest.qWait(3000)
                self.ButtonClicked_9()
                self.backtester_count = 1
            if self.backtester_count == 1 and (self.backtester_process is None or self.backtester_process.poll() == 0):
                self.ButtonClicked_13()
                QTest.qWait(3000)
                self.ButtonClicked_14()
                self.backtester_count = 2

        if UPBIT_COLLECTOR and (self.int_time < coin_exit_time or coin_coll_time + 100 < self.int_time):
            if not self.websocket_ticker.isRunning():
                self.websocket_ticker.start()
            if not self.websocket_orderbook.isRunning():
                self.websocket_orderbook.start()
            if not self.coin_tickupdater1_process.is_alive():
                self.coin_tickupdater1_process.start()
            if not self.coin_tickupdater2_process.is_alive():
                self.coin_tickupdater2_process.start()
                text = '코인 콜렉터를 재시작하였습니다.'
                soundQ.put(text)
                teleQ.put(text)

        if UPBIT_TRADER and (self.int_time < coin_exit_time or coin_trad_time + 100 < self.int_time):
            if UPBIT_ACCOUNT:
                if not self.strategy_process.is_alive():
                    self.SetColumnsGJ('C')
                    self.strategy_process.start()
                if not self.trader_upbit.isRunning():
                    self.trader_upbit.start()
                    text = '코인 트레이더를 재시작하였습니다.'
                    soundQ.put(text)
                    teleQ.put(text)
            else:
                text = '업비트 계정이 설정되지 않아 트레이더를 실행할 수 없습니다.'
                windowQ.put([ui_num['C로그텍스트'], text])

        self.int_time = int(strf_time('%H%M%S'))

    def SetColumnsGJ(self, gubun):
        if gubun == 'S':
            self.gj_tableWidget.setColumnWidth(0, 122)
            self.gj_tableWidget.setColumnWidth(1, 68)
            self.gj_tableWidget.setColumnWidth(2, 68)
            self.gj_tableWidget.setColumnWidth(3, 68)
            self.gj_tableWidget.setColumnWidth(4, 68)
            self.gj_tableWidget.setColumnWidth(5, 68)
            self.gj_tableWidget.setColumnWidth(6, 68)
            self.gj_tableWidget.setColumnWidth(7, 68)
            self.gj_tableWidget.setColumnWidth(8, 68)
        elif gubun == 'C':
            self.gj_tableWidget.setColumnWidth(0, 85)
            self.gj_tableWidget.setColumnWidth(1, 55)
            self.gj_tableWidget.setColumnWidth(2, 55)
            self.gj_tableWidget.setColumnWidth(3, 90)
            self.gj_tableWidget.setColumnWidth(4, 126)
            self.gj_tableWidget.setColumnWidth(5, 55)
            self.gj_tableWidget.setColumnWidth(6, 90)
            self.gj_tableWidget.setColumnWidth(7, 55)
            self.gj_tableWidget.setColumnWidth(8, 55)

    def UpdateProgressBar(self):
        self.progressBar.setValue(int(self.cpu_per))

    @thread_decorator
    def UpdateCpuper(self):
        self.cpu_per = psutil.cpu_percent(interval=1)

    def ButtonClicked_1(self):
        if self.main_tabWidget.currentWidget() == self.td_tab:
            if not self.calendarWidget.isVisible():
                boolean1 = False
                boolean2 = True
                self.tt_pushButton.setStyleSheet(style_bc_dk)
            else:
                boolean1 = True
                boolean2 = False
                self.tt_pushButton.setStyleSheet(style_bc_bt)
            self.tt_tableWidget.setVisible(boolean1)
            self.td_tableWidget.setVisible(boolean1)
            self.tj_tableWidget.setVisible(boolean1)
            self.jg_tableWidget.setVisible(boolean1)
            self.gj_tableWidget.setVisible(boolean1)
            self.cj_tableWidget.setVisible(boolean1)
            self.calendarWidget.setVisible(boolean2)
            self.dt_tableWidget.setVisible(boolean2)
            self.ds_tableWidget.setVisible(boolean2)
            self.nt_pushButton_01.setVisible(boolean2)
            self.nt_pushButton_02.setVisible(boolean2)
            self.nt_pushButton_03.setVisible(boolean2)
            self.nt_tableWidget.setVisible(boolean2)
            self.ns_tableWidget.setVisible(boolean2)

    def ButtonClicked_2(self):
        if self.geometry().width() > 1000:
            self.setGeometry(self.geometry().x(), self.geometry().y(), 722, 383)
            self.zo_pushButton.setStyleSheet(style_bc_dk)
        else:
            self.setGeometry(self.geometry().x(), self.geometry().y(), 1403, 763)
            self.zo_pushButton.setStyleSheet(style_bc_bt)

    def ButtonClicked_4(self):
        buttonReply = QtWidgets.QMessageBox.warning(
            self, '최적화 백테스터 초기화', '최적화 백테스터의 기본값이 모두 초기화됩니다.\n계속하시겠습니까?\n',
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No
        )
        if buttonReply == QtWidgets.QMessageBox.Yes:
            columns = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25,
                       26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45]
            data = [10, 14, 36000, 3, 4, 5, 6, 7, 8, 9, 0.1, 0.1, 30, 60, 90, 120, 150, 180, 30, 3, 0, 500, 50, 10,
                    50, 100, 10, 10, 0, 100000, 10000, 1000, 0, 10, 1, 0.1, 25, 15, -1, -1, 3, 10, 1, 0.2, 6]
            df = pd.DataFrame([data], columns=columns, index=[0])
            queryQ.put([1, df, 'stockback_jcv', 'replace'])
            data = [10, 14, 1008000, 3, 4, 5, 6, 7, 8, 9, 0.1, 0.1, 30, 60, 90, 120, 150, 180, 30, 3,
                    0, 100000000, 10000000, 10000000, 50, 100, 10, 10, 0, 1000000000, 100000000, 100000000,
                    0, 10, 1, 0.1, 25, 15, -1, -1, 3, 10, 1, 0.2, 6]
            df = pd.DataFrame([data], columns=columns, index=[0])
            queryQ.put([1, df, 'coinback_jjv', 'replace'])

    def ButtonClicked_5(self):
        buttonReply = QtWidgets.QMessageBox.warning(
            self, '데이터베이스 초기화', '체결목록, 잔고목록, 거래목록, 일별목록이 모두 초기화됩니다.\n계속하시겠습니까?\n',
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No
        )
        if buttonReply == QtWidgets.QMessageBox.Yes:
            queryQ.put([2, 'DELETE FROM jangolist'])
            queryQ.put([2, 'DELETE FROM tradelist'])
            queryQ.put([2, 'DELETE FROM chegeollist'])
            queryQ.put([2, 'DELETE FROM totaltradelist'])

    def ButtonClicked_6(self):
        buttonReply = QtWidgets.QMessageBox.warning(
            self, '계정 설정 초기화', '계정 설정 항목이 모두 초기화됩니다.\n계속하시겠습니까?\n',
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No
        )
        if buttonReply == QtWidgets.QMessageBox.Yes:
            queryQ.put([1, 'DELETE FROM kiwoom'])
            queryQ.put([1, 'DELETE FROM upbit'])
            queryQ.put([1, 'DELETE FROM telegram'])

    # noinspection PyMethodMayBeStatic
    def ButtonClicked_7(self, cmd):
        if '집계' in cmd:
            con = sqlite3.connect(db_tradelist)
            df = pd.read_sql('SELECT * FROM totaltradelist', con)
            con.close()
            df = df[::-1]
            if len(df) > 0:
                sd = strp_time('%Y%m%d', df['index'][df.index[0]])
                ld = strp_time('%Y%m%d', df['index'][df.index[-1]])
                pr = str((sd - ld).days + 1) + '일'
                nbg, nsg = df['총매수금액'].sum(), df['총매도금액'].sum()
                sp = round((nsg / nbg - 1) * 100, 2)
                npg, nmg = df['총수익금액'].sum(), df['총손실금액'].sum()
                nsig = df['수익금합계'].sum()
                df2 = pd.DataFrame(columns=columns_nt)
                df2.at[0] = pr, nbg, nsg, npg, nmg, sp, nsig
                self.UpdateTablewidget([ui_num['누적합계'], df2])
            else:
                QtWidgets.QMessageBox.critical(self, '오류 알림', '거래목록이 존재하지 않습니다.\n')
                return
            if cmd == '일별집계':
                df = df.rename(columns={'index': '일자'})
                self.UpdateTablewidget([ui_num['누적상세'], df])
            elif cmd == '월별집계':
                df['일자'] = df['index'].apply(lambda x: x[:6])
                df2 = pd.DataFrame(columns=columns_nd)
                lastmonth = df['일자'][df.index[-1]]
                month = strf_time('%Y%m')
                while int(month) >= int(lastmonth):
                    df3 = df[df['일자'] == month]
                    if len(df3) > 0:
                        tbg, tsg = df3['총매수금액'].sum(), df3['총매도금액'].sum()
                        sp = round((tsg / tbg - 1) * 100, 2)
                        tpg, tmg = df3['총수익금액'].sum(), df3['총손실금액'].sum()
                        ttsg = df3['수익금합계'].sum()
                        df2.at[month] = month, tbg, tsg, tpg, tmg, sp, ttsg
                    month = str(int(month) - 89) if int(month[4:]) == 1 else str(int(month) - 1)
                self.UpdateTablewidget([ui_num['누적상세'], df2])
            elif cmd == '연도별집계':
                df['일자'] = df['index'].apply(lambda x: x[:4])
                df2 = pd.DataFrame(columns=columns_nd)
                lastyear = df['일자'][df.index[-1]]
                year = strf_time('%Y')
                while int(year) >= int(lastyear):
                    df3 = df[df['일자'] == year]
                    if len(df3) > 0:
                        tbg, tsg = df3['총매수금액'].sum(), df3['총매도금액'].sum()
                        sp = round((tsg / tbg - 1) * 100, 2)
                        tpg, tmg = df3['총수익금액'].sum(), df3['총손실금액'].sum()
                        ttsg = df3['수익금합계'].sum()
                        df2.at[year] = year, tbg, tsg, tpg, tmg, sp, ttsg
                    year = str(int(year) - 1)
                self.UpdateTablewidget([ui_num['누적상세'], df2])

    def ButtonClicked_8(self):
        con = sqlite3.connect(db_setting)
        df = pd.read_sql('SELECT * FROM stockback_jcv', con)
        df = df.set_index('index')
        con.close()
        self.sb_jcvc_lineEdit_01.setText(str(df['1'][0]))
        self.sb_jcvc_lineEdit_02.setText(str(df['2'][0]))
        self.sb_jcvc_lineEdit_03.setText(str(df['3'][0]))
        self.sb_jcvc_lineEdit_04.setText(str(df['4'][0]))
        self.sb_jcvc_lineEdit_05.setText(str(df['5'][0]))
        self.sb_jcvc_lineEdit_06.setText(str(df['6'][0]))
        self.sb_jcvc_lineEdit_07.setText(str(df['7'][0]))
        self.sb_jcvc_lineEdit_08.setText(str(df['8'][0]))
        self.sb_jcvc_lineEdit_09.setText(str(df['9'][0]))
        self.sb_jcvc_lineEdit_10.setText(str(df['10'][0]))
        self.sb_jcvc_lineEdit_11.setText(str(df['11'][0]))
        self.sb_jcvc_lineEdit_12.setText(str(df['12'][0]))
        self.sb_jcvc_lineEdit_13.setText(str(df['13'][0]))
        self.sb_jcvc_lineEdit_14.setText(str(df['14'][0]))
        self.sb_jcvc_lineEdit_15.setText(str(df['15'][0]))
        self.sb_jcvc_lineEdit_16.setText(str(df['16'][0]))
        self.sb_jcvc_lineEdit_17.setText(str(df['17'][0]))
        self.sb_jcvc_lineEdit_18.setText(str(df['18'][0]))
        self.sb_jcvc_lineEdit_19.setText(str(df['19'][0]))
        self.sb_jcvc_lineEdit_20.setText(str(df['20'][0]))
        self.sb_jcvc_lineEdit_21.setText(str(df['21'][0]))
        self.sb_jcvc_lineEdit_22.setText(str(df['22'][0]))
        self.sb_jcvc_lineEdit_23.setText(str(df['23'][0]))
        self.sb_jcvc_lineEdit_24.setText(str(df['24'][0]))
        self.sb_jcvc_lineEdit_25.setText(str(df['25'][0]))
        self.sb_jcvc_lineEdit_26.setText(str(df['26'][0]))
        self.sb_jcvc_lineEdit_27.setText(str(df['27'][0]))
        self.sb_jcvc_lineEdit_28.setText(str(df['28'][0]))
        self.sb_jcvc_lineEdit_29.setText(str(df['29'][0]))
        self.sb_jcvc_lineEdit_30.setText(str(df['30'][0]))
        self.sb_jcvc_lineEdit_31.setText(str(df['31'][0]))
        self.sb_jcvc_lineEdit_32.setText(str(df['32'][0]))
        self.sb_jcvc_lineEdit_33.setText(str(df['33'][0]))
        self.sb_jcvc_lineEdit_34.setText(str(df['34'][0]))
        self.sb_jcvc_lineEdit_35.setText(str(df['35'][0]))
        self.sb_jcvc_lineEdit_36.setText(str(df['36'][0]))
        self.sb_jcvc_lineEdit_37.setText(str(df['37'][0]))
        self.sb_jcvc_lineEdit_38.setText(str(df['38'][0]))
        self.sb_jcvc_lineEdit_39.setText(str(df['39'][0]))
        self.sb_jcvc_lineEdit_40.setText(str(df['40'][0]))
        self.sb_jcvc_lineEdit_41.setText(str(df['41'][0]))
        self.sb_jcvc_lineEdit_42.setText(str(df['42'][0]))
        self.sb_jcvc_lineEdit_43.setText(str(df['43'][0]))
        self.sb_jcvc_lineEdit_44.setText(str(df['44'][0]))
        self.sb_jcvc_lineEdit_45.setText(str(df['45'][0]))

    def ButtonClicked_9(self):
        if self.backtester_process is not None and self.backtester_process.poll() != 0:
            QtWidgets.QMessageBox.critical(self, '오류 알림', '현재 백테스터가 실행중입니다.\n중복 실행할 수 없습니다.\n')
            return
        textfull = True
        if self.sb_jcvc_lineEdit_01.text() == '':
            textfull = False
        elif self.sb_jcvc_lineEdit_02.text() == '':
            textfull = False
        elif self.sb_jcvc_lineEdit_03.text() == '':
            textfull = False
        elif self.sb_jcvc_lineEdit_04.text() == '':
            textfull = False
        elif self.sb_jcvc_lineEdit_05.text() == '':
            textfull = False
        elif self.sb_jcvc_lineEdit_06.text() == '':
            textfull = False
        elif self.sb_jcvc_lineEdit_07.text() == '':
            textfull = False
        elif self.sb_jcvc_lineEdit_08.text() == '':
            textfull = False
        elif self.sb_jcvc_lineEdit_09.text() == '':
            textfull = False
        elif self.sb_jcvc_lineEdit_10.text() == '':
            textfull = False
        elif self.sb_jcvc_lineEdit_11.text() == '':
            textfull = False
        elif self.sb_jcvc_lineEdit_12.text() == '':
            textfull = False
        elif self.sb_jcvc_lineEdit_13.text() == '':
            textfull = False
        elif self.sb_jcvc_lineEdit_14.text() == '':
            textfull = False
        elif self.sb_jcvc_lineEdit_15.text() == '':
            textfull = False
        elif self.sb_jcvc_lineEdit_16.text() == '':
            textfull = False
        elif self.sb_jcvc_lineEdit_17.text() == '':
            textfull = False
        elif self.sb_jcvc_lineEdit_18.text() == '':
            textfull = False
        elif self.sb_jcvc_lineEdit_19.text() == '':
            textfull = False
        elif self.sb_jcvc_lineEdit_20.text() == '':
            textfull = False
        elif self.sb_jcvc_lineEdit_21.text() == '':
            textfull = False
        elif self.sb_jcvc_lineEdit_22.text() == '':
            textfull = False
        elif self.sb_jcvc_lineEdit_23.text() == '':
            textfull = False
        elif self.sb_jcvc_lineEdit_24.text() == '':
            textfull = False
        elif self.sb_jcvc_lineEdit_25.text() == '':
            textfull = False
        elif self.sb_jcvc_lineEdit_26.text() == '':
            textfull = False
        elif self.sb_jcvc_lineEdit_27.text() == '':
            textfull = False
        elif self.sb_jcvc_lineEdit_28.text() == '':
            textfull = False
        elif self.sb_jcvc_lineEdit_29.text() == '':
            textfull = False
        elif self.sb_jcvc_lineEdit_30.text() == '':
            textfull = False
        elif self.sb_jcvc_lineEdit_31.text() == '':
            textfull = False
        elif self.sb_jcvc_lineEdit_32.text() == '':
            textfull = False
        elif self.sb_jcvc_lineEdit_33.text() == '':
            textfull = False
        elif self.sb_jcvc_lineEdit_34.text() == '':
            textfull = False
        elif self.sb_jcvc_lineEdit_35.text() == '':
            textfull = False
        elif self.sb_jcvc_lineEdit_36.text() == '':
            textfull = False
        elif self.sb_jcvc_lineEdit_37.text() == '':
            textfull = False
        elif self.sb_jcvc_lineEdit_38.text() == '':
            textfull = False
        elif self.sb_jcvc_lineEdit_39.text() == '':
            textfull = False
        elif self.sb_jcvc_lineEdit_40.text() == '':
            textfull = False
        elif self.sb_jcvc_lineEdit_41.text() == '':
            textfull = False
        elif self.sb_jcvc_lineEdit_42.text() == '':
            textfull = False
        elif self.sb_jcvc_lineEdit_43.text() == '':
            textfull = False
        elif self.sb_jcvc_lineEdit_44.text() == '':
            textfull = False
        elif self.sb_jcvc_lineEdit_45.text() == '':
            textfull = False
        if not textfull:
            QtWidgets.QMessageBox.critical(self, '오류 알림', '일부 변수값이 입력되지 않았습니다.\n')
            return
        self.backtester_process = subprocess.Popen(
            f'python {system_path}/backtester/backtester_stock_vc.py '
            f'{self.sb_jcvc_lineEdit_01.text()} {self.sb_jcvc_lineEdit_02.text()} {self.sb_jcvc_lineEdit_03.text()} '
            f'{self.sb_jcvc_lineEdit_04.text()} {self.sb_jcvc_lineEdit_05.text()} {self.sb_jcvc_lineEdit_06.text()} '
            f'{self.sb_jcvc_lineEdit_07.text()} {self.sb_jcvc_lineEdit_08.text()} {self.sb_jcvc_lineEdit_09.text()} '
            f'{self.sb_jcvc_lineEdit_10.text()} {self.sb_jcvc_lineEdit_11.text()} {self.sb_jcvc_lineEdit_12.text()} '
            f'{self.sb_jcvc_lineEdit_13.text()} {self.sb_jcvc_lineEdit_14.text()} {self.sb_jcvc_lineEdit_15.text()} '
            f'{self.sb_jcvc_lineEdit_16.text()} {self.sb_jcvc_lineEdit_17.text()} {self.sb_jcvc_lineEdit_18.text()} '
            f'{self.sb_jcvc_lineEdit_19.text()} {self.sb_jcvc_lineEdit_20.text()} {self.sb_jcvc_lineEdit_21.text()} '
            f'{self.sb_jcvc_lineEdit_22.text()} {self.sb_jcvc_lineEdit_23.text()} {self.sb_jcvc_lineEdit_24.text()} '
            f'{self.sb_jcvc_lineEdit_25.text()} {self.sb_jcvc_lineEdit_26.text()} {self.sb_jcvc_lineEdit_27.text()} '
            f'{self.sb_jcvc_lineEdit_28.text()} {self.sb_jcvc_lineEdit_29.text()} {self.sb_jcvc_lineEdit_30.text()} '
            f'{self.sb_jcvc_lineEdit_31.text()} {self.sb_jcvc_lineEdit_32.text()} {self.sb_jcvc_lineEdit_33.text()} '
            f'{self.sb_jcvc_lineEdit_34.text()} {self.sb_jcvc_lineEdit_35.text()} {self.sb_jcvc_lineEdit_36.text()} '
            f'{self.sb_jcvc_lineEdit_37.text()} {self.sb_jcvc_lineEdit_38.text()} {self.sb_jcvc_lineEdit_39.text()} '
            f'{self.sb_jcvc_lineEdit_40.text()} {self.sb_jcvc_lineEdit_41.text()} {self.sb_jcvc_lineEdit_42.text()} '
            f'{self.sb_jcvc_lineEdit_43.text()} {self.sb_jcvc_lineEdit_44.text()} {self.sb_jcvc_lineEdit_45.text()}'
        )

    def ButtonClicked_10(self):
        textfull = True
        if self.sb_jcvc_lineEdit_01.text() == '':
            textfull = False
        elif self.sb_jcvc_lineEdit_02.text() == '':
            textfull = False
        elif self.sb_jcvc_lineEdit_03.text() == '':
            textfull = False
        elif self.sb_jcvc_lineEdit_04.text() == '':
            textfull = False
        elif self.sb_jcvc_lineEdit_05.text() == '':
            textfull = False
        elif self.sb_jcvc_lineEdit_06.text() == '':
            textfull = False
        elif self.sb_jcvc_lineEdit_07.text() == '':
            textfull = False
        elif self.sb_jcvc_lineEdit_08.text() == '':
            textfull = False
        elif self.sb_jcvc_lineEdit_09.text() == '':
            textfull = False
        elif self.sb_jcvc_lineEdit_10.text() == '':
            textfull = False
        elif self.sb_jcvc_lineEdit_11.text() == '':
            textfull = False
        elif self.sb_jcvc_lineEdit_12.text() == '':
            textfull = False
        elif self.sb_jcvc_lineEdit_13.text() == '':
            textfull = False
        elif self.sb_jcvc_lineEdit_14.text() == '':
            textfull = False
        elif self.sb_jcvc_lineEdit_15.text() == '':
            textfull = False
        elif self.sb_jcvc_lineEdit_16.text() == '':
            textfull = False
        elif self.sb_jcvc_lineEdit_17.text() == '':
            textfull = False
        elif self.sb_jcvc_lineEdit_18.text() == '':
            textfull = False
        elif self.sb_jcvc_lineEdit_19.text() == '':
            textfull = False
        elif self.sb_jcvc_lineEdit_20.text() == '':
            textfull = False
        elif self.sb_jcvc_lineEdit_21.text() == '':
            textfull = False
        elif self.sb_jcvc_lineEdit_22.text() == '':
            textfull = False
        elif self.sb_jcvc_lineEdit_23.text() == '':
            textfull = False
        elif self.sb_jcvc_lineEdit_24.text() == '':
            textfull = False
        elif self.sb_jcvc_lineEdit_25.text() == '':
            textfull = False
        elif self.sb_jcvc_lineEdit_26.text() == '':
            textfull = False
        elif self.sb_jcvc_lineEdit_27.text() == '':
            textfull = False
        elif self.sb_jcvc_lineEdit_28.text() == '':
            textfull = False
        elif self.sb_jcvc_lineEdit_29.text() == '':
            textfull = False
        elif self.sb_jcvc_lineEdit_30.text() == '':
            textfull = False
        elif self.sb_jcvc_lineEdit_31.text() == '':
            textfull = False
        elif self.sb_jcvc_lineEdit_32.text() == '':
            textfull = False
        elif self.sb_jcvc_lineEdit_33.text() == '':
            textfull = False
        elif self.sb_jcvc_lineEdit_34.text() == '':
            textfull = False
        elif self.sb_jcvc_lineEdit_35.text() == '':
            textfull = False
        elif self.sb_jcvc_lineEdit_36.text() == '':
            textfull = False
        elif self.sb_jcvc_lineEdit_37.text() == '':
            textfull = False
        elif self.sb_jcvc_lineEdit_38.text() == '':
            textfull = False
        elif self.sb_jcvc_lineEdit_39.text() == '':
            textfull = False
        elif self.sb_jcvc_lineEdit_40.text() == '':
            textfull = False
        elif self.sb_jcvc_lineEdit_41.text() == '':
            textfull = False
        elif self.sb_jcvc_lineEdit_42.text() == '':
            textfull = False
        elif self.sb_jcvc_lineEdit_43.text() == '':
            textfull = False
        elif self.sb_jcvc_lineEdit_44.text() == '':
            textfull = False
        elif self.sb_jcvc_lineEdit_45.text() == '':
            textfull = False
        if not textfull:
            QtWidgets.QMessageBox.critical(self, '오류 알림', '일부 변수값이 입력되지 않았습니다.\n')
            return
        data = [
            self.sb_jcvc_lineEdit_01.text(), self.sb_jcvc_lineEdit_02.text(), self.sb_jcvc_lineEdit_03.text(),
            self.sb_jcvc_lineEdit_04.text(), self.sb_jcvc_lineEdit_05.text(), self.sb_jcvc_lineEdit_06.text(),
            self.sb_jcvc_lineEdit_07.text(), self.sb_jcvc_lineEdit_08.text(), self.sb_jcvc_lineEdit_09.text(),
            self.sb_jcvc_lineEdit_10.text(), self.sb_jcvc_lineEdit_11.text(), self.sb_jcvc_lineEdit_12.text(),
            self.sb_jcvc_lineEdit_13.text(), self.sb_jcvc_lineEdit_14.text(), self.sb_jcvc_lineEdit_15.text(),
            self.sb_jcvc_lineEdit_16.text(), self.sb_jcvc_lineEdit_17.text(), self.sb_jcvc_lineEdit_18.text(),
            self.sb_jcvc_lineEdit_19.text(), self.sb_jcvc_lineEdit_20.text(), self.sb_jcvc_lineEdit_21.text(),
            self.sb_jcvc_lineEdit_22.text(), self.sb_jcvc_lineEdit_23.text(), self.sb_jcvc_lineEdit_24.text(),
            self.sb_jcvc_lineEdit_25.text(), self.sb_jcvc_lineEdit_26.text(), self.sb_jcvc_lineEdit_27.text(),
            self.sb_jcvc_lineEdit_28.text(), self.sb_jcvc_lineEdit_29.text(), self.sb_jcvc_lineEdit_30.text(),
            self.sb_jcvc_lineEdit_31.text(), self.sb_jcvc_lineEdit_32.text(), self.sb_jcvc_lineEdit_33.text(),
            self.sb_jcvc_lineEdit_34.text(), self.sb_jcvc_lineEdit_35.text(), self.sb_jcvc_lineEdit_36.text(),
            self.sb_jcvc_lineEdit_37.text(), self.sb_jcvc_lineEdit_38.text(), self.sb_jcvc_lineEdit_39.text(),
            self.sb_jcvc_lineEdit_40.text(), self.sb_jcvc_lineEdit_41.text(), self.sb_jcvc_lineEdit_42.text(),
            self.sb_jcvc_lineEdit_43.text(), self.sb_jcvc_lineEdit_44.text(), self.sb_jcvc_lineEdit_45.text()
        ]
        columns = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25,
                   26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45]
        df = pd.DataFrame([data], columns=columns, index=[0])
        queryQ.put([1, df, 'stockback_jcv', 'replace'])

    def ButtonClicked_11(self):
        con = sqlite3.connect(db_setting)
        df = pd.read_sql('SELECT * FROM stock', con)
        df = df.set_index('index')
        con.close()
        self.sb_jcvj_lineEdit_01.setText('5')
        self.sb_jcvj_lineEdit_02.setText('14')
        self.sb_jcvj_lineEdit_03.setText('36000')
        self.sb_jcvj_lineEdit_04.setText(str(df['체결강도차이'][0]))
        self.sb_jcvj_lineEdit_05.setText(str(df['평균시간'][0]))
        self.sb_jcvj_lineEdit_06.setText(str(df['거래대금차이'][0]))
        self.sb_jcvj_lineEdit_07.setText(str(df['체결강도하한'][0]))
        self.sb_jcvj_lineEdit_08.setText(str(df['누적거래대금하한'][0]))
        self.sb_jcvj_lineEdit_09.setText(str(df['등락율하한'][0]))
        self.sb_jcvj_lineEdit_10.setText(str(df['등락율상한'][0]))
        self.sb_jcvj_lineEdit_11.setText(str(df['청산수익률'][0]))
        self.sb_jcvj_lineEdit_12.setText('6')

    def ButtonClicked_12(self):
        if self.backtester_process is not None and self.backtester_process.poll() != 0:
            QtWidgets.QMessageBox.critical(self, '오류 알림', '현재 백테스터가 실행중입니다.\n중복 실행할 수 없습니다.\n')
            return
        textfull = True
        if self.sb_jcvj_lineEdit_01.text() == '':
            textfull = False
        elif self.sb_jcvj_lineEdit_02.text() == '':
            textfull = False
        elif self.sb_jcvj_lineEdit_03.text() == '':
            textfull = False
        elif self.sb_jcvj_lineEdit_04.text() == '':
            textfull = False
        elif self.sb_jcvj_lineEdit_05.text() == '':
            textfull = False
        elif self.sb_jcvj_lineEdit_06.text() == '':
            textfull = False
        elif self.sb_jcvj_lineEdit_07.text() == '':
            textfull = False
        elif self.sb_jcvj_lineEdit_08.text() == '':
            textfull = False
        elif self.sb_jcvj_lineEdit_09.text() == '':
            textfull = False
        elif self.sb_jcvj_lineEdit_10.text() == '':
            textfull = False
        elif self.sb_jcvj_lineEdit_11.text() == '':
            textfull = False
        elif self.sb_jcvj_lineEdit_12.text() == '':
            textfull = False
        if not textfull:
            QtWidgets.QMessageBox.critical(self, '오류 알림', '일부 변수값이 입력되지 않았습니다.\n')
            return
        self.backtester_process = subprocess.Popen(
            f'python {system_path}/backtester/backtester_stock_vj.py '
            f'{self.sb_jcvj_lineEdit_01.text()} {self.sb_jcvj_lineEdit_02.text()} {self.sb_jcvj_lineEdit_03.text()} '
            f'{self.sb_jcvj_lineEdit_04.text()} {self.sb_jcvj_lineEdit_05.text()} {self.sb_jcvj_lineEdit_06.text()} '
            f'{self.sb_jcvj_lineEdit_07.text()} {self.sb_jcvj_lineEdit_08.text()} {self.sb_jcvj_lineEdit_09.text()} '
            f'{self.sb_jcvj_lineEdit_10.text()} {self.sb_jcvj_lineEdit_11.text()} {self.sb_jcvj_lineEdit_12.text()}'
        )

    def ButtonClicked_13(self):
        con = sqlite3.connect(db_setting)
        df = pd.read_sql('SELECT * FROM coinback_jjv', con)
        df = df.set_index('index')
        con.close()
        self.cb_jjvc_lineEdit_01.setText(str(df['1'][0]))
        self.cb_jjvc_lineEdit_02.setText(str(df['2'][0]))
        self.cb_jjvc_lineEdit_03.setText(str(df['3'][0]))
        self.cb_jjvc_lineEdit_04.setText(str(df['4'][0]))
        self.cb_jjvc_lineEdit_05.setText(str(df['5'][0]))
        self.cb_jjvc_lineEdit_06.setText(str(df['6'][0]))
        self.cb_jjvc_lineEdit_07.setText(str(df['7'][0]))
        self.cb_jjvc_lineEdit_08.setText(str(df['8'][0]))
        self.cb_jjvc_lineEdit_09.setText(str(df['9'][0]))
        self.cb_jjvc_lineEdit_10.setText(str(df['10'][0]))
        self.cb_jjvc_lineEdit_11.setText(str(df['11'][0]))
        self.cb_jjvc_lineEdit_12.setText(str(df['12'][0]))
        self.cb_jjvc_lineEdit_13.setText(str(df['13'][0]))
        self.cb_jjvc_lineEdit_14.setText(str(df['14'][0]))
        self.cb_jjvc_lineEdit_15.setText(str(df['15'][0]))
        self.cb_jjvc_lineEdit_16.setText(str(df['16'][0]))
        self.cb_jjvc_lineEdit_17.setText(str(df['17'][0]))
        self.cb_jjvc_lineEdit_18.setText(str(df['18'][0]))
        self.cb_jjvc_lineEdit_19.setText(str(df['19'][0]))
        self.cb_jjvc_lineEdit_20.setText(str(df['20'][0]))
        self.cb_jjvc_lineEdit_21.setText(str(df['21'][0]))
        self.cb_jjvc_lineEdit_22.setText(str(df['22'][0]))
        self.cb_jjvc_lineEdit_23.setText(str(df['23'][0]))
        self.cb_jjvc_lineEdit_24.setText(str(df['24'][0]))
        self.cb_jjvc_lineEdit_25.setText(str(df['25'][0]))
        self.cb_jjvc_lineEdit_26.setText(str(df['26'][0]))
        self.cb_jjvc_lineEdit_27.setText(str(df['27'][0]))
        self.cb_jjvc_lineEdit_28.setText(str(df['28'][0]))
        self.cb_jjvc_lineEdit_29.setText(str(df['29'][0]))
        self.cb_jjvc_lineEdit_30.setText(str(df['30'][0]))
        self.cb_jjvc_lineEdit_31.setText(str(df['31'][0]))
        self.cb_jjvc_lineEdit_32.setText(str(df['32'][0]))
        self.cb_jjvc_lineEdit_33.setText(str(df['33'][0]))
        self.cb_jjvc_lineEdit_34.setText(str(df['34'][0]))
        self.cb_jjvc_lineEdit_35.setText(str(df['35'][0]))
        self.cb_jjvc_lineEdit_36.setText(str(df['36'][0]))
        self.cb_jjvc_lineEdit_37.setText(str(df['37'][0]))
        self.cb_jjvc_lineEdit_38.setText(str(df['38'][0]))
        self.cb_jjvc_lineEdit_39.setText(str(df['39'][0]))
        self.cb_jjvc_lineEdit_40.setText(str(df['40'][0]))
        self.cb_jjvc_lineEdit_41.setText(str(df['41'][0]))
        self.cb_jjvc_lineEdit_42.setText(str(df['42'][0]))
        self.cb_jjvc_lineEdit_43.setText(str(df['43'][0]))
        self.cb_jjvc_lineEdit_44.setText(str(df['44'][0]))
        self.cb_jjvc_lineEdit_45.setText(str(df['45'][0]))

    def ButtonClicked_14(self):
        if self.backtester_process is not None and self.backtester_process.poll() != 0:
            QtWidgets.QMessageBox.critical(self, '오류 알림', '현재 백테스터가 실행중입니다.\n중복 실행할 수 없습니다.\n')
            return
        textfull = True
        if self.cb_jjvc_lineEdit_01.text() == '':
            textfull = False
        elif self.cb_jjvc_lineEdit_02.text() == '':
            textfull = False
        elif self.cb_jjvc_lineEdit_03.text() == '':
            textfull = False
        elif self.cb_jjvc_lineEdit_04.text() == '':
            textfull = False
        elif self.cb_jjvc_lineEdit_05.text() == '':
            textfull = False
        elif self.cb_jjvc_lineEdit_06.text() == '':
            textfull = False
        elif self.cb_jjvc_lineEdit_07.text() == '':
            textfull = False
        elif self.cb_jjvc_lineEdit_08.text() == '':
            textfull = False
        elif self.cb_jjvc_lineEdit_09.text() == '':
            textfull = False
        elif self.cb_jjvc_lineEdit_10.text() == '':
            textfull = False
        elif self.cb_jjvc_lineEdit_11.text() == '':
            textfull = False
        elif self.cb_jjvc_lineEdit_12.text() == '':
            textfull = False
        elif self.cb_jjvc_lineEdit_13.text() == '':
            textfull = False
        elif self.cb_jjvc_lineEdit_14.text() == '':
            textfull = False
        elif self.cb_jjvc_lineEdit_15.text() == '':
            textfull = False
        elif self.cb_jjvc_lineEdit_16.text() == '':
            textfull = False
        elif self.cb_jjvc_lineEdit_17.text() == '':
            textfull = False
        elif self.cb_jjvc_lineEdit_18.text() == '':
            textfull = False
        elif self.cb_jjvc_lineEdit_19.text() == '':
            textfull = False
        elif self.cb_jjvc_lineEdit_20.text() == '':
            textfull = False
        elif self.cb_jjvc_lineEdit_21.text() == '':
            textfull = False
        elif self.cb_jjvc_lineEdit_22.text() == '':
            textfull = False
        elif self.cb_jjvc_lineEdit_23.text() == '':
            textfull = False
        elif self.cb_jjvc_lineEdit_24.text() == '':
            textfull = False
        elif self.cb_jjvc_lineEdit_25.text() == '':
            textfull = False
        elif self.cb_jjvc_lineEdit_26.text() == '':
            textfull = False
        elif self.cb_jjvc_lineEdit_27.text() == '':
            textfull = False
        elif self.cb_jjvc_lineEdit_28.text() == '':
            textfull = False
        elif self.cb_jjvc_lineEdit_29.text() == '':
            textfull = False
        elif self.cb_jjvc_lineEdit_30.text() == '':
            textfull = False
        elif self.cb_jjvc_lineEdit_31.text() == '':
            textfull = False
        elif self.cb_jjvc_lineEdit_32.text() == '':
            textfull = False
        elif self.cb_jjvc_lineEdit_33.text() == '':
            textfull = False
        elif self.cb_jjvc_lineEdit_34.text() == '':
            textfull = False
        elif self.cb_jjvc_lineEdit_35.text() == '':
            textfull = False
        elif self.cb_jjvc_lineEdit_36.text() == '':
            textfull = False
        elif self.cb_jjvc_lineEdit_37.text() == '':
            textfull = False
        elif self.cb_jjvc_lineEdit_38.text() == '':
            textfull = False
        elif self.cb_jjvc_lineEdit_39.text() == '':
            textfull = False
        elif self.cb_jjvc_lineEdit_40.text() == '':
            textfull = False
        elif self.cb_jjvc_lineEdit_41.text() == '':
            textfull = False
        elif self.cb_jjvc_lineEdit_42.text() == '':
            textfull = False
        elif self.cb_jjvc_lineEdit_43.text() == '':
            textfull = False
        elif self.cb_jjvc_lineEdit_44.text() == '':
            textfull = False
        elif self.cb_jjvc_lineEdit_45.text() == '':
            textfull = False
        if not textfull:
            QtWidgets.QMessageBox.critical(self, '오류 알림', '일부 변수값이 입력되지 않았습니다.\n')
            return
        self.backtester_process = subprocess.Popen(
            f'python {system_path}/backtester/backtester_coin_vc.py '
            f'{self.cb_jjvc_lineEdit_01.text()} {self.cb_jjvc_lineEdit_02.text()} {self.cb_jjvc_lineEdit_03.text()} '
            f'{self.cb_jjvc_lineEdit_04.text()} {self.cb_jjvc_lineEdit_05.text()} {self.cb_jjvc_lineEdit_06.text()} '
            f'{self.cb_jjvc_lineEdit_07.text()} {self.cb_jjvc_lineEdit_08.text()} {self.cb_jjvc_lineEdit_09.text()} '
            f'{self.cb_jjvc_lineEdit_10.text()} {self.cb_jjvc_lineEdit_11.text()} {self.cb_jjvc_lineEdit_12.text()} '
            f'{self.cb_jjvc_lineEdit_13.text()} {self.cb_jjvc_lineEdit_14.text()} {self.cb_jjvc_lineEdit_15.text()} '
            f'{self.cb_jjvc_lineEdit_16.text()} {self.cb_jjvc_lineEdit_17.text()} {self.cb_jjvc_lineEdit_18.text()} '
            f'{self.cb_jjvc_lineEdit_19.text()} {self.cb_jjvc_lineEdit_20.text()} {self.cb_jjvc_lineEdit_21.text()} '
            f'{self.cb_jjvc_lineEdit_22.text()} {self.cb_jjvc_lineEdit_23.text()} {self.cb_jjvc_lineEdit_24.text()} '
            f'{self.cb_jjvc_lineEdit_25.text()} {self.cb_jjvc_lineEdit_26.text()} {self.cb_jjvc_lineEdit_27.text()} '
            f'{self.cb_jjvc_lineEdit_28.text()} {self.cb_jjvc_lineEdit_29.text()} {self.cb_jjvc_lineEdit_30.text()} '
            f'{self.cb_jjvc_lineEdit_31.text()} {self.cb_jjvc_lineEdit_32.text()} {self.cb_jjvc_lineEdit_33.text()} '
            f'{self.cb_jjvc_lineEdit_34.text()} {self.cb_jjvc_lineEdit_35.text()} {self.cb_jjvc_lineEdit_36.text()} '
            f'{self.cb_jjvc_lineEdit_37.text()} {self.cb_jjvc_lineEdit_38.text()} {self.cb_jjvc_lineEdit_39.text()} '
            f'{self.cb_jjvc_lineEdit_40.text()} {self.cb_jjvc_lineEdit_41.text()} {self.cb_jjvc_lineEdit_42.text()} '
            f'{self.cb_jjvc_lineEdit_43.text()} {self.cb_jjvc_lineEdit_44.text()} {self.cb_jjvc_lineEdit_45.text()}'
        )

    def ButtonClicked_15(self):
        textfull = True
        if self.cb_jjvc_lineEdit_01.text() == '':
            textfull = False
        elif self.cb_jjvc_lineEdit_02.text() == '':
            textfull = False
        elif self.cb_jjvc_lineEdit_03.text() == '':
            textfull = False
        elif self.cb_jjvc_lineEdit_04.text() == '':
            textfull = False
        elif self.cb_jjvc_lineEdit_05.text() == '':
            textfull = False
        elif self.cb_jjvc_lineEdit_06.text() == '':
            textfull = False
        elif self.cb_jjvc_lineEdit_07.text() == '':
            textfull = False
        elif self.cb_jjvc_lineEdit_08.text() == '':
            textfull = False
        elif self.cb_jjvc_lineEdit_09.text() == '':
            textfull = False
        elif self.cb_jjvc_lineEdit_10.text() == '':
            textfull = False
        elif self.cb_jjvc_lineEdit_11.text() == '':
            textfull = False
        elif self.cb_jjvc_lineEdit_12.text() == '':
            textfull = False
        elif self.cb_jjvc_lineEdit_13.text() == '':
            textfull = False
        elif self.cb_jjvc_lineEdit_14.text() == '':
            textfull = False
        elif self.cb_jjvc_lineEdit_15.text() == '':
            textfull = False
        elif self.cb_jjvc_lineEdit_16.text() == '':
            textfull = False
        elif self.cb_jjvc_lineEdit_17.text() == '':
            textfull = False
        elif self.cb_jjvc_lineEdit_18.text() == '':
            textfull = False
        elif self.cb_jjvc_lineEdit_19.text() == '':
            textfull = False
        elif self.cb_jjvc_lineEdit_20.text() == '':
            textfull = False
        elif self.cb_jjvc_lineEdit_21.text() == '':
            textfull = False
        elif self.cb_jjvc_lineEdit_22.text() == '':
            textfull = False
        elif self.cb_jjvc_lineEdit_23.text() == '':
            textfull = False
        elif self.cb_jjvc_lineEdit_24.text() == '':
            textfull = False
        elif self.cb_jjvc_lineEdit_25.text() == '':
            textfull = False
        elif self.cb_jjvc_lineEdit_26.text() == '':
            textfull = False
        elif self.cb_jjvc_lineEdit_27.text() == '':
            textfull = False
        elif self.cb_jjvc_lineEdit_28.text() == '':
            textfull = False
        elif self.cb_jjvc_lineEdit_29.text() == '':
            textfull = False
        elif self.cb_jjvc_lineEdit_30.text() == '':
            textfull = False
        elif self.cb_jjvc_lineEdit_31.text() == '':
            textfull = False
        elif self.cb_jjvc_lineEdit_32.text() == '':
            textfull = False
        elif self.cb_jjvc_lineEdit_33.text() == '':
            textfull = False
        elif self.cb_jjvc_lineEdit_34.text() == '':
            textfull = False
        elif self.cb_jjvc_lineEdit_35.text() == '':
            textfull = False
        elif self.cb_jjvc_lineEdit_36.text() == '':
            textfull = False
        elif self.cb_jjvc_lineEdit_37.text() == '':
            textfull = False
        elif self.cb_jjvc_lineEdit_38.text() == '':
            textfull = False
        elif self.cb_jjvc_lineEdit_39.text() == '':
            textfull = False
        elif self.cb_jjvc_lineEdit_40.text() == '':
            textfull = False
        elif self.cb_jjvc_lineEdit_41.text() == '':
            textfull = False
        elif self.cb_jjvc_lineEdit_42.text() == '':
            textfull = False
        elif self.cb_jjvc_lineEdit_43.text() == '':
            textfull = False
        elif self.cb_jjvc_lineEdit_44.text() == '':
            textfull = False
        elif self.cb_jjvc_lineEdit_45.text() == '':
            textfull = False
        if not textfull:
            QtWidgets.QMessageBox.critical(self, '오류 알림', '일부 변수값이 입력되지 않았습니다.\n')
            return
        data = [
            self.cb_jjvc_lineEdit_01.text(), self.cb_jjvc_lineEdit_02.text(), self.cb_jjvc_lineEdit_03.text(),
            self.cb_jjvc_lineEdit_04.text(), self.cb_jjvc_lineEdit_05.text(), self.cb_jjvc_lineEdit_06.text(),
            self.cb_jjvc_lineEdit_07.text(), self.cb_jjvc_lineEdit_08.text(), self.cb_jjvc_lineEdit_09.text(),
            self.cb_jjvc_lineEdit_10.text(), self.cb_jjvc_lineEdit_11.text(), self.cb_jjvc_lineEdit_12.text(),
            self.cb_jjvc_lineEdit_13.text(), self.cb_jjvc_lineEdit_14.text(), self.cb_jjvc_lineEdit_15.text(),
            self.cb_jjvc_lineEdit_16.text(), self.cb_jjvc_lineEdit_17.text(), self.cb_jjvc_lineEdit_18.text(),
            self.cb_jjvc_lineEdit_19.text(), self.cb_jjvc_lineEdit_20.text(), self.cb_jjvc_lineEdit_21.text(),
            self.cb_jjvc_lineEdit_22.text(), self.cb_jjvc_lineEdit_23.text(), self.cb_jjvc_lineEdit_24.text(),
            self.cb_jjvc_lineEdit_25.text(), self.cb_jjvc_lineEdit_26.text(), self.cb_jjvc_lineEdit_27.text(),
            self.cb_jjvc_lineEdit_28.text(), self.cb_jjvc_lineEdit_29.text(), self.cb_jjvc_lineEdit_30.text(),
            self.cb_jjvc_lineEdit_31.text(), self.cb_jjvc_lineEdit_32.text(), self.cb_jjvc_lineEdit_33.text(),
            self.cb_jjvc_lineEdit_34.text(), self.cb_jjvc_lineEdit_35.text(), self.cb_jjvc_lineEdit_36.text(),
            self.cb_jjvc_lineEdit_37.text(), self.cb_jjvc_lineEdit_38.text(), self.cb_jjvc_lineEdit_39.text(),
            self.cb_jjvc_lineEdit_40.text(), self.cb_jjvc_lineEdit_41.text(), self.cb_jjvc_lineEdit_42.text(),
            self.cb_jjvc_lineEdit_43.text(), self.cb_jjvc_lineEdit_44.text(), self.cb_jjvc_lineEdit_45.text()
        ]
        columns = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25,
                   26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45]
        df = pd.DataFrame([data], columns=columns, index=[0])
        queryQ.put([1, df, 'coinback_jjv', 'replace'])

    def ButtonClicked_16(self):
        con = sqlite3.connect(db_setting)
        df = pd.read_sql('SELECT * FROM coin', con)
        df = df.set_index('index')
        con.close()
        self.cb_jjvj_lineEdit_01.setText('5')
        self.cb_jjvj_lineEdit_02.setText('14')
        self.cb_jjvj_lineEdit_03.setText('1008000')
        self.cb_jjvj_lineEdit_04.setText(str(df['체결강도차이'][0]))
        self.cb_jjvj_lineEdit_05.setText(str(df['평균시간'][0]))
        self.cb_jjvj_lineEdit_06.setText(str(df['거래대금차이'][0]))
        self.cb_jjvj_lineEdit_07.setText(str(df['체결강도하한'][0]))
        self.cb_jjvj_lineEdit_08.setText(str(df['누적거래대금하한'][0]))
        self.cb_jjvj_lineEdit_09.setText(str(df['등락율하한'][0]))
        self.cb_jjvj_lineEdit_10.setText(str(df['등락율상한'][0]))
        self.cb_jjvj_lineEdit_11.setText(str(df['청산수익률'][0]))
        self.cb_jjvj_lineEdit_12.setText('6')

    def ButtonClicked_17(self):
        if self.backtester_process is not None and self.backtester_process.poll() != 0:
            QtWidgets.QMessageBox.critical(self, '오류 알림', '현재 백테스터가 실행중입니다.\n중복 실행할 수 없습니다.\n')
            return
        textfull = True
        if self.cb_jjvj_lineEdit_01.text() == '':
            textfull = False
        elif self.cb_jjvj_lineEdit_02.text() == '':
            textfull = False
        elif self.cb_jjvj_lineEdit_03.text() == '':
            textfull = False
        elif self.cb_jjvj_lineEdit_04.text() == '':
            textfull = False
        elif self.cb_jjvj_lineEdit_05.text() == '':
            textfull = False
        elif self.cb_jjvj_lineEdit_06.text() == '':
            textfull = False
        elif self.cb_jjvj_lineEdit_07.text() == '':
            textfull = False
        elif self.cb_jjvj_lineEdit_08.text() == '':
            textfull = False
        elif self.cb_jjvj_lineEdit_09.text() == '':
            textfull = False
        elif self.cb_jjvj_lineEdit_10.text() == '':
            textfull = False
        elif self.cb_jjvj_lineEdit_11.text() == '':
            textfull = False
        elif self.cb_jjvj_lineEdit_12.text() == '':
            textfull = False
        if not textfull:
            QtWidgets.QMessageBox.critical(self, '오류 알림', '일부 변수값이 입력되지 않았습니다.\n')
            return
        self.backtester_process = subprocess.Popen(
            f'python {system_path}/backtester/backtester_coin_vj.py '
            f'{self.cb_jjvj_lineEdit_01.text()} {self.cb_jjvj_lineEdit_02.text()} {self.cb_jjvj_lineEdit_03.text()} '
            f'{self.cb_jjvj_lineEdit_04.text()} {self.cb_jjvj_lineEdit_05.text()} {self.cb_jjvj_lineEdit_06.text()} '
            f'{self.cb_jjvj_lineEdit_07.text()} {self.cb_jjvj_lineEdit_08.text()} {self.cb_jjvj_lineEdit_09.text()} '
            f'{self.cb_jjvj_lineEdit_10.text()} {self.cb_jjvj_lineEdit_11.text()} {self.cb_jjvj_lineEdit_12.text()}'
        )

    def ButtonClicked_18(self):
        con = sqlite3.connect(db_setting)
        df = pd.read_sql('SELECT * FROM main', con)
        df = df.set_index('index')
        con.close()
        if len(df) > 0:
            self.sj_main_checkBox_01.setChecked(True) if df['키움콜렉터'][0] else self.sj_main_checkBox_01.setChecked(False)
            self.sj_main_checkBox_02.setChecked(True) if df['키움트레이더'][0] else self.sj_main_checkBox_02.setChecked(False)
            self.sj_main_checkBox_03.setChecked(True) if df['업비트콜렉터'][0] else self.sj_main_checkBox_03.setChecked(False)
            self.sj_main_checkBox_04.setChecked(True) if df['업비트트레이더'][0] else self.sj_main_checkBox_04.setChecked(False)
            self.UpdateTexedit([ui_num['설정텍스트'], '시스템 기본 설정값 불러오기 완료'])
        else:
            QtWidgets.QMessageBox.critical(self, '오류 알림', '시스템 기본 설정값이\n존재하지 않습니다.\n')

    def ButtonClicked_19(self):
        con = sqlite3.connect(db_setting)
        df = pd.read_sql('SELECT * FROM kiwoom', con)
        df = df.set_index('index')
        con.close()
        if len(df) > 0:
            self.sj_sacc_lineEdit_01.setText(df['아이디1'][0])
            self.sj_sacc_lineEdit_02.setText(df['비밀번호1'][0])
            self.sj_sacc_lineEdit_03.setText(df['인증서비밀번호1'][0])
            self.sj_sacc_lineEdit_04.setText(df['계좌비밀번호1'][0])
            self.sj_sacc_lineEdit_05.setText(df['아이디2'][0])
            self.sj_sacc_lineEdit_06.setText(df['비밀번호2'][0])
            self.sj_sacc_lineEdit_07.setText(df['인증서비밀번호2'][0])
            self.sj_sacc_lineEdit_08.setText(df['계좌비밀번호2'][0])
            self.UpdateTexedit([ui_num['설정텍스트'], '키움증권 계정 설정값 불러오기 완료'])
        else:
            QtWidgets.QMessageBox.critical(self, '오류 알림', '키움증권 계정 설정값이\n존재하지 않습니다.\n')

    def ButtonClicked_20(self):
        con = sqlite3.connect(db_setting)
        df = pd.read_sql('SELECT * FROM upbit', con)
        df = df.set_index('index')
        con.close()
        if len(df) > 0:
            self.sj_cacc_lineEdit_01.setText(df['Access_key'][0])
            self.sj_cacc_lineEdit_02.setText(df['Secret_key'][0])
            self.UpdateTexedit([ui_num['설정텍스트'], '업비트 계정 설정값 불러오기 완료'])
        else:
            QtWidgets.QMessageBox.critical(self, '오류 알림', '업비트 계정 설정값이\n존재하지 않습니다.\n')

    def ButtonClicked_21(self):
        con = sqlite3.connect(db_setting)
        df = pd.read_sql('SELECT * FROM telegram', con)
        df = df.set_index('index')
        con.close()
        if len(df) > 0:
            self.sj_tele_lineEdit_01.setText(df['str_bot'][0])
            self.sj_tele_lineEdit_02.setText(df['int_id'][0])
            self.UpdateTexedit([ui_num['설정텍스트'], '텔레그램 봇토큰 및 사용자 아이디 설정값 불러오기 완료'])
        else:
            QtWidgets.QMessageBox.critical(self, '오류 알림', '텔레그램 봇토큰 및 사용자 아이디\n설정값이 존재하지 않습니다.\n')

    def ButtonClicked_22(self):
        con = sqlite3.connect(db_setting)
        df = pd.read_sql('SELECT * FROM stock', con)
        df = df.set_index('index')
        con.close()
        if len(df) > 0:
            self.sj_stock_checkBox_01.setChecked(True) if df['모의투자'][0] else self.sj_stock_checkBox_01.setChecked(False)
            self.sj_stock_checkBox_02.setChecked(True) if df['알림소리'][0] else self.sj_stock_checkBox_02.setChecked(False)
            self.sj_stock_lineEdit_01.setText(str(df['체결강도차이'][0]))
            self.sj_stock_lineEdit_02.setText(str(df['평균시간'][0]))
            self.sj_stock_lineEdit_03.setText(str(df['거래대금차이'][0]))
            self.sj_stock_lineEdit_04.setText(str(df['체결강도하한'][0]))
            self.sj_stock_lineEdit_05.setText(str(df['누적거래대금하한'][0]))
            self.sj_stock_lineEdit_06.setText(str(df['등락율하한'][0]))
            self.sj_stock_lineEdit_07.setText(str(df['등락율상한'][0]))
            self.sj_stock_lineEdit_08.setText(str(df['청산수익률'][0]))
            self.UpdateTexedit([ui_num['설정텍스트'], '주식 전략 설정값 불러오기 완료'])
        else:
            QtWidgets.QMessageBox.critical(self, '오류 알림', '주식 전략 설정값이\n존재하지 않습니다.\n')

    def ButtonClicked_23(self):
        con = sqlite3.connect(db_setting)
        df = pd.read_sql('SELECT * FROM coin', con)
        df = df.set_index('index')
        con.close()
        if len(df) > 0:
            self.sj_coin_checkBox_01.setChecked(True) if df['모의투자'][0] else self.sj_coin_checkBox_01.setChecked(False)
            self.sj_coin_checkBox_02.setChecked(True) if df['알림소리'][0] else self.sj_coin_checkBox_02.setChecked(False)
            self.sj_coin_lineEdit_01.setText(str(df['체결강도차이'][0]))
            self.sj_coin_lineEdit_02.setText(str(df['평균시간'][0]))
            self.sj_coin_lineEdit_03.setText(str(df['거래대금차이'][0]))
            self.sj_coin_lineEdit_04.setText(str(df['체결강도하한'][0]))
            self.sj_coin_lineEdit_05.setText(str(df['누적거래대금하한'][0]))
            self.sj_coin_lineEdit_06.setText(str(df['등락율하한'][0]))
            self.sj_coin_lineEdit_07.setText(str(df['등락율상한'][0]))
            self.sj_coin_lineEdit_08.setText(str(df['청산수익률'][0]))
            self.UpdateTexedit([ui_num['설정텍스트'], '코인 전략 설정값 불러오기 완료'])
        else:
            QtWidgets.QMessageBox.critical(self, '오류 알림', '코인 전략 설정값이\n존재하지 않습니다.\n')

    def ButtonClicked_24(self):
        kc = 1 if self.sj_main_checkBox_01.isChecked() else 0
        kt = 1 if self.sj_main_checkBox_02.isChecked() else 0
        cc = 1 if self.sj_main_checkBox_03.isChecked() else 0
        ct = 1 if self.sj_main_checkBox_04.isChecked() else 0
        df = pd.DataFrame([[kc, kt, cc, ct]], columns=columns_sm, index=[0])
        queryQ.put([1, df, 'main', 'replace'])
        self.UpdateTexedit([ui_num['설정텍스트'], '시스템 기본 설정값 저장하기 완료'])

    def ButtonClicked_25(self):
        id1 = self.sj_sacc_lineEdit_01.text()
        ps1 = self.sj_sacc_lineEdit_02.text()
        cp1 = self.sj_sacc_lineEdit_03.text()
        ap1 = self.sj_sacc_lineEdit_04.text()
        id2 = self.sj_sacc_lineEdit_05.text()
        ps2 = self.sj_sacc_lineEdit_06.text()
        cp2 = self.sj_sacc_lineEdit_07.text()
        ap2 = self.sj_sacc_lineEdit_08.text()
        if id1 == '' or ps1 == '' or cp1 == '' or ap1 == '' or id2 == '' or ps2 == '' or cp2 == '' or ap2 == '':
            QtWidgets.QMessageBox.critical(self, '오류 알림', '일부 변수값이 입력되지 않았습니다.\n')
        else:
            df = pd.DataFrame([[id1, ps1, cp1, ap1, id2, ps2, cp2, ap2]], columns=columns_sk, index=[0])
            queryQ.put([1, df, 'kiwoom', 'replace'])
            self.UpdateTexedit([ui_num['설정텍스트'], '키움증권 계정 설정값 저장하기 완료'])

    def ButtonClicked_26(self):
        access_key = self.sj_cacc_lineEdit_01.text()
        secret_key = self.sj_cacc_lineEdit_02.text()
        if access_key == '' or secret_key == '':
            QtWidgets.QMessageBox.critical(self, '오류 알림', '일부 변수값이 입력되지 않았습니다.\n')
        else:
            df = pd.DataFrame([[access_key, secret_key]], columns=columns_sc, index=[0])
            queryQ.put([1, df, 'upbit', 'replace'])
            self.UpdateTexedit([ui_num['설정텍스트'], '업비트 계정 설정값 저장하기 완료'])

    def ButtonClicked_27(self):
        str_bot = self.sj_tele_lineEdit_01.text()
        int_id = self.sj_tele_lineEdit_02.text()
        if str_bot == '' or int_id == '':
            QtWidgets.QMessageBox.critical(self, '오류 알림', '일부 변수값이 입력되지 않았습니다.\n')
        else:
            df = pd.DataFrame([[str_bot, int_id]], columns=columns_st, index=[0])
            queryQ.put([1, df, 'telegram', 'replace'])
            self.UpdateTexedit([ui_num['설정텍스트'], '텔레그램 봇토큰 및 사용자 아이디 설정값 저장하기 완료'])

    def ButtonClicked_28(self):
        me = 1 if self.sj_stock_checkBox_01.isChecked() else 0
        sd = 1 if self.sj_stock_checkBox_02.isChecked() else 0
        gapch = self.sj_stock_lineEdit_01.text()
        avgtime = self.sj_stock_lineEdit_02.text()
        gapsm = self.sj_stock_lineEdit_03.text()
        chlow = self.sj_stock_lineEdit_04.text()
        dmlow = self.sj_stock_lineEdit_05.text()
        plow = self.sj_stock_lineEdit_06.text()
        phigh = self.sj_stock_lineEdit_07.text()
        csper = self.sj_stock_lineEdit_08.text()
        if gapch == '' or avgtime == '' or gapsm == '' or chlow == '' or \
                dmlow == '' or plow == '' or phigh == '' or csper == '':
            QtWidgets.QMessageBox.critical(self, '오류 알림', '일부 변수값이 입력되지 않았습니다.\n')
        else:
            data = [me, sd, float(gapch), int(avgtime), int(gapsm), float(chlow),
                    int(dmlow), float(plow), float(phigh), float(csper)]
            df = pd.DataFrame([data], columns=columns_ss, index=[0])
            queryQ.put([1, df, 'stock', 'replace'])
            self.UpdateTexedit([ui_num['설정텍스트'], '주식 전략 설정값 저장하기 완료'])

    def ButtonClicked_29(self):
        me = 1 if self.sj_coin_checkBox_01.isChecked() else 0
        sd = 1 if self.sj_coin_checkBox_02.isChecked() else 0
        gapch = self.sj_coin_lineEdit_01.text()
        avgtime = self.sj_coin_lineEdit_02.text()
        gapsm = self.sj_coin_lineEdit_03.text()
        chlow = self.sj_coin_lineEdit_04.text()
        dmlow = self.sj_coin_lineEdit_05.text()
        plow = self.sj_coin_lineEdit_06.text()
        phigh = self.sj_coin_lineEdit_07.text()
        csper = self.sj_coin_lineEdit_08.text()
        if gapch == '' or avgtime == '' or gapsm == '' or chlow == '' or \
                dmlow == '' or plow == '' or phigh == '' or csper == '':
            QtWidgets.QMessageBox.critical(self, '오류 알림', '일부 변수값이 입력되지 않았습니다.\n')
        else:
            data = [me, sd, float(gapch), int(avgtime), int(gapsm), float(chlow),
                    int(dmlow), float(plow), float(phigh), float(csper)]
            df = pd.DataFrame([data], columns=columns_ss, index=[0])
            queryQ.put([1, df, 'coin', 'replace'])
            self.UpdateTexedit([ui_num['설정텍스트'], '코인 전략 설정값 저장하기 완료'])

    def UpdateTexedit(self, data):
        text = f'[{now()}] {data[1]}'
        if data[0] == ui_num['설정텍스트']:
            self.sj_textEdit.append(text)
        elif data[0] == ui_num['S로그텍스트']:
            self.st_textEdit.append(text)
            self.log1.info(text)
        elif data[0] == ui_num['S단순텍스트']:
            self.sc_textEdit.append(text)
        elif data[0] == ui_num['C로그텍스트']:
            self.ct_textEdit.append(text)
            self.log2.info(text)
        elif data[0] == ui_num['C단순텍스트']:
            self.cc_textEdit.append(text)
        elif data[0] == ui_num['S종목명딕셔너리']:
            self.dict_name = data[1]

    def UpdateTablewidget(self, data):
        gubun = data[0]
        df = data[1]

        tableWidget = None
        if gubun == ui_num['실현손익']:
            tableWidget = self.tt_tableWidget
        elif gubun == ui_num['거래목록']:
            tableWidget = self.td_tableWidget
        elif gubun == ui_num['잔고평가']:
            tableWidget = self.tj_tableWidget
        elif gubun == ui_num['잔고목록']:
            tableWidget = self.jg_tableWidget
        elif gubun == ui_num['체결목록']:
            tableWidget = self.cj_tableWidget
        elif gubun == ui_num['당일합계']:
            tableWidget = self.dt_tableWidget
        elif gubun == ui_num['당일상세']:
            tableWidget = self.ds_tableWidget
        elif gubun == ui_num['누적합계']:
            tableWidget = self.nt_tableWidget
        elif gubun == ui_num['누적상세']:
            tableWidget = self.ns_tableWidget
        if tableWidget is None:
            return

        if len(df) == 0:
            tableWidget.clearContents()
            return

        tableWidget.setRowCount(len(df))
        for j, index in enumerate(df.index):
            for i, column in enumerate(df.columns):
                if column == '체결시간':
                    cgtime = df[column][index]
                    cgtime = f'{cgtime[8:10]}:{cgtime[10:12]}:{cgtime[12:14]}'
                    item = QtWidgets.QTableWidgetItem(cgtime)
                elif column in ['거래일자', '일자']:
                    day = df[column][index]
                    if '.' not in day:
                        day = day[:4] + '.' + day[4:6] + '.' + day[6:]
                    item = QtWidgets.QTableWidgetItem(day)
                elif column in ['종목명', '주문구분', '기간']:
                    item = QtWidgets.QTableWidgetItem(str(df[column][index]))
                elif column not in ['수익률', '등락율', '고저평균대비등락율', '체결강도', '최고체결강도']:
                    item = QtWidgets.QTableWidgetItem(changeFormat(df[column][index]).split('.')[0])
                else:
                    item = QtWidgets.QTableWidgetItem(changeFormat(df[column][index]))

                if column == '종목명':
                    item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
                elif column in ['거래횟수', '추정예탁자산', '추정예수금', '보유종목수',
                                '주문구분', '체결시간', '거래일자', '기간', '일자']:
                    item.setTextAlignment(Qt.AlignVCenter | Qt.AlignCenter)
                else:
                    item.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)

                if '수익률' in df.columns:
                    if df['수익률'][index] >= 0:
                        item.setForeground(color_fg_bt)
                    else:
                        item.setForeground(color_fg_dk)
                elif gubun == ui_num['체결목록']:
                    if df['주문구분'][index] == '매수':
                        item.setForeground(color_fg_bt)
                    elif df['주문구분'][index] == '매도':
                        item.setForeground(color_fg_dk)
                    elif df['주문구분'][index] in ['매도취소', '매수취소']:
                        item.setForeground(color_fg_bc)
                tableWidget.setItem(j, i, item)

        if len(df) < 13 and gubun in [ui_num['거래목록'], ui_num['잔고목록']]:
            tableWidget.setRowCount(13)
        elif len(df) < 15 and gubun == ui_num['체결목록']:
            tableWidget.setRowCount(15)
        elif len(df) < 19 and gubun == ui_num['당일상세']:
            tableWidget.setRowCount(19)
        elif len(df) < 28 and gubun == ui_num['누적상세']:
            tableWidget.setRowCount(28)

    def UpdateGaonsimJongmok(self, data):
        dict_df = data[1]

        tn = 1 if 80000 < int(strf_time('%H%M%S')) < 100000 else 2

        if len(dict_df) == 0:
            self.gj_tableWidget.clearContents()
            return

        self.gj_tableWidget.setRowCount(len(dict_df))
        for j, code in enumerate(list(dict_df.keys())):
            try:
                item = QtWidgets.QTableWidgetItem(self.dict_name[code])
            except KeyError:
                item = QtWidgets.QTableWidgetItem(code)
            item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
            self.gj_tableWidget.setItem(j, 0, item)

            smavg = dict_df[code]['거래대금'][self.dict_intg[f'평균시간{tn}'] + 1]
            item = QtWidgets.QTableWidgetItem(changeFormat(smavg).split('.')[0])
            item.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
            self.gj_tableWidget.setItem(j, columns_gj3.index('smavg'), item)

            chavg = dict_df[code]['체결강도'][self.dict_intg[f'평균시간{tn}'] + 1]
            item = QtWidgets.QTableWidgetItem(changeFormat(chavg))
            item.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
            self.gj_tableWidget.setItem(j, columns_gj3.index('chavg'), item)

            chhigh = dict_df[code]['최고체결강도'][self.dict_intg[f'평균시간{tn}'] + 1]
            item = QtWidgets.QTableWidgetItem(changeFormat(chhigh))
            item.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
            self.gj_tableWidget.setItem(j, columns_gj3.index('chhigh'), item)

            for i, column in enumerate(columns_gj2):
                if column in ['거래대금', '누적거래대금']:
                    item = QtWidgets.QTableWidgetItem(changeFormat(dict_df[code][column][0]).split('.')[0])
                else:
                    item = QtWidgets.QTableWidgetItem(changeFormat(dict_df[code][column][0]))
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
                if column == '등락율':
                    if self.dict_intg[f'등락율하한{tn}'] <= dict_df[code][column][0] <= \
                            self.dict_intg[f'등락율상한{tn}']:
                        item.setForeground(color_fg_bt)
                    else:
                        item.setForeground(color_fg_dk)
                elif column == '고저평균대비등락율':
                    if dict_df[code][column][0] >= 0:
                        item.setForeground(color_fg_bt)
                    else:
                        item.setForeground(color_fg_dk)
                elif column == '거래대금':
                    if dict_df[code][column][0] >= smavg + self.dict_intg[f'거래대금차이{tn}']:
                        item.setForeground(color_fg_bt)
                    else:
                        item.setForeground(color_fg_dk)
                elif column == '누적거래대금':
                    if dict_df[code][column][0] >= self.dict_intg[f'누적거래대금하한{tn}']:
                        item.setForeground(color_fg_bt)
                    else:
                        item.setForeground(color_fg_dk)
                elif column == '체결강도':
                    if dict_df[code][column][0] >= self.dict_intg[f'체결강도하한{tn}'] and \
                            dict_df[code][column][0] >= chavg + self.dict_intg[f'체결강도차이{tn}']:
                        item.setForeground(color_fg_bt)
                    else:
                        item.setForeground(color_fg_dk)
                self.gj_tableWidget.setItem(j, i + 1, item)

        if len(dict_df) < 15:
            self.gj_tableWidget.setRowCount(15)

    def CalendarClicked(self):
        searchday = self.calendarWidget.selectedDate().toString('yyyyMMdd')
        con = sqlite3.connect(db_tradelist)
        df = pd.read_sql(f"SELECT * FROM tradelist WHERE 체결시간 LIKE '{searchday}%'", con)
        con.close()
        if len(df) > 0:
            df = df.set_index('index')
            df.sort_values(by=['체결시간'], ascending=True, inplace=True)
            df = df[['체결시간', '종목명', '매수금액', '매도금액', '주문수량', '수익률', '수익금']].copy()
            nbg, nsg = df['매수금액'].sum(), df['매도금액'].sum()
            sp = round((nsg / nbg - 1) * 100, 2)
            npg, nmg, nsig = df[df['수익금'] > 0]['수익금'].sum(), df[df['수익금'] < 0]['수익금'].sum(), df['수익금'].sum()
            df2 = pd.DataFrame(columns=columns_dt)
            df2.at[0] = searchday, nbg, nsg, npg, nmg, sp, nsig
        else:
            df = pd.DataFrame(columns=columns_dt)
            df2 = pd.DataFrame(columns=columns_dd)
        self.UpdateTablewidget([ui_num['당일합계'], df2])
        self.UpdateTablewidget([ui_num['당일상세'], df])

    def closeEvent(self, a):
        buttonReply = QtWidgets.QMessageBox.question(
            self, "프로그램 종료", "프로그램을 종료하겠습니까?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No
        )
        if buttonReply == QtWidgets.QMessageBox.Yes:
            if sound_process.is_alive():
                sound_process.kill()
            if query_process.is_alive():
                query_process.kill()
            if telefram_process.is_alive():
                telefram_process.kill()
            a.accept()
        else:
            a.ignore()


class Writer(QtCore.QThread):
    data1 = QtCore.pyqtSignal(list)
    data2 = QtCore.pyqtSignal(list)
    data3 = QtCore.pyqtSignal(list)

    def __init__(self):
        super().__init__()

    def run(self):
        while True:
            data = windowQ.get()
            if data[0] <= 5:
                self.data1.emit(data)
            elif data[0] < 20:
                self.data2.emit(data)
            elif data[0] == 20:
                self.data3.emit(data)


if __name__ == '__main__':
    windowQ, stockQ, coinQ, sstgQ, cstgQ, soundQ, queryQ, teleQ, collectorQ, tick1Q, tick2Q, tick3Q, tick4Q, tick5Q, \
        tick6Q, tick7Q, tick8Q, tick9Q, tick10Q = Queue(), Queue(), Queue(), Queue(), Queue(), Queue(), Queue(), \
        Queue(), Queue(), Queue(), Queue(), Queue(), Queue(), Queue(), Queue(), Queue(), Queue(), Queue(), Queue()

    sound_process = Process(target=Sound, args=(soundQ,), daemon=True)
    query_process = Process(target=Query, args=(windowQ, collectorQ, queryQ), daemon=True)
    telefram_process = Process(target=TelegramMsg, args=(windowQ, stockQ, coinQ, teleQ), daemon=True)
    sound_process.start()
    query_process.start()
    telefram_process.start()

    app = QtWidgets.QApplication(sys.argv)
    app.setStyle(ProxyStyle())
    app.setStyle('fusion')
    palette = QtGui.QPalette()
    palette.setColor(QtGui.QPalette.Window, color_bg_bc)
    palette.setColor(QtGui.QPalette.Background, color_bg_bc)
    palette.setColor(QtGui.QPalette.WindowText, color_fg_bc)
    palette.setColor(QtGui.QPalette.Base, color_bg_bc)
    palette.setColor(QtGui.QPalette.AlternateBase, color_bg_dk)
    palette.setColor(QtGui.QPalette.Text, color_fg_bc)
    palette.setColor(QtGui.QPalette.Button, color_bg_bc)
    palette.setColor(QtGui.QPalette.ButtonText, color_fg_bc)
    palette.setColor(QtGui.QPalette.Link, color_fg_bk)
    palette.setColor(QtGui.QPalette.Highlight, color_fg_bk)
    palette.setColor(QtGui.QPalette.HighlightedText, color_bg_bk)
    app.setPalette(palette)
    window = Window()
    window.show()
    app.exec_()
