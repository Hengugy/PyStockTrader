from PyQt5.QtGui import QFont, QColor

openapi_path = 'D:/OpenAPI'
system_path = 'D:/PythonProjects/PyStockTrader'
graph_path = f'{system_path}/backtester/graph'
db_setting = f'{system_path}/database/setting.db'
db_backtest = f'{system_path}/database/backtest.db'
db_tradelist = f'{system_path}/database/tradelist.db'
db_stock_tick = f'{system_path}/database/stock_tick.db'
db_coin_tick = f'{system_path}/database/coin_tick.db'

qfont = QFont()
qfont.setFamily('나눔고딕')
qfont.setPixelSize(12)

stock_vjup_time = 84500
stock_alg2_time = 84700
stock_coll_time = 84800
stock_alg1_time = 84900
stock_trad_time = 85000
stock_init_time = 90000
stock_csan_time = 95900
stock_exit_time = 100000

coin_coll_time = 95900
coin_trad_time = 100000
coin_csan_time = 55800
coin_exit_time = 55900

backtest_time = 60000

sn_brrq = 1000
sn_brrd = 1001
sn_cond = 1002
sn_oper = 1003
sn_jscg = 1004
sn_vijc = 1005
sn_cthg = 1006
sn_short = 1100
sn_jchj = 2000

color_fg_bt = QColor(230, 230, 235)
color_fg_bc = QColor(190, 190, 195)
color_fg_dk = QColor(150, 150, 155)
color_fg_bk = QColor(110, 110, 115)

color_bg_bt = QColor(50, 50, 55)
color_bg_bc = QColor(40, 40, 45)
color_bg_dk = QColor(30, 30, 35)
color_bg_bk = QColor(20, 20, 25)
color_bg_ld = (50, 50, 55, 150)

color_bf_bt = QColor(110, 110, 115)
color_bf_dk = QColor(70, 70, 75)

color_cifl = QColor(230, 230, 255)
color_pluss = QColor(230, 230, 235)
color_minus = QColor(120, 120, 125)

color_chuse1 = QColor(35, 35, 40)
color_chuse2 = QColor(30, 30, 35)
color_ema05 = QColor(230, 230, 235)
color_ema10 = QColor(200, 200, 205)
color_ema20 = QColor(170, 170, 175)
color_ema40 = QColor(140, 140, 145)
color_ema60 = QColor(110, 110, 115)
color_ema120 = QColor(80, 80, 85)
color_ema240 = QColor(70, 70, 75)
color_ema480 = QColor(60, 60, 65)

style_fc_bt = 'color: rgb(230, 230, 235);'
style_fc_dk = 'color: rgb(150, 150, 155);'
style_bc_bt = 'background-color: rgb(50, 50, 55);'
style_bc_md = 'background-color: rgb(40, 40, 45);'
style_bc_dk = 'background-color: rgb(30, 30, 35);'

ui_num = {'설정텍스트': 0, 'S단순텍스트': 1, 'S로그텍스트': 2, 'S종목명딕셔너리': 3, 'C단순텍스트': 4, 'C로그텍스트': 5,
          '실현손익': 11, '거래목록': 12, '잔고평가': 13, '잔고목록': 14, '체결목록': 15,
          '당일합계': 16, '당일상세': 17, '누적합계': 18, '누적상세': 19, '관심종목': 20}

columns_tt = ['거래횟수', '총매수금액', '총매도금액', '총수익금액', '총손실금액', '수익률', '수익금합계']
columns_td = ['종목명', '매수금액', '매도금액', '주문수량', '수익률', '수익금', '체결시간']
columns_tj = ['추정예탁자산', '추정예수금', '보유종목수', '수익률', '총평가손익', '총매입금액', '총평가금액']
columns_jg = ['종목명', '매입가', '현재가', '수익률', '평가손익', '매입금액', '평가금액', '보유수량']
columns_cj = ['종목명', '주문구분', '주문수량', '미체결수량', '주문가격', '체결가', '체결시간']
columns_gj1 = ['등락율', '고저평균대비등락율', '거래대금', '누적거래대금', '체결강도', '최고체결강도']
columns_gj2 = ['등락율', '고저평균대비등락율', '거래대금', '누적거래대금', '체결강도']
columns_gj3 = ['종목명', 'per', 'hmlper', 'smoney', 'dmoney', 'ch', 'smavg', 'chavg', 'chhigh']

columns_dt = ['거래일자', '누적매수금액', '누적매도금액', '누적수익금액', '누적손실금액', '수익률', '누적수익금']
columns_dd = ['체결시간', '종목명', '매수금액', '매도금액', '주문수량', '수익률', '수익금']
columns_nt = ['기간', '누적매수금액', '누적매도금액', '누적수익금액', '누적손실금액', '수익률', '누적수익금']
columns_nd = ['일자', '총매수금액', '총매도금액', '총수익금액', '총손실금액', '수익률', '수익금합계']

columns_sm = ['키움콜렉터', '키움트레이더', '업비트콜렉터', '업비트트레이더']
columns_sk = ['아이디1', '비밀번호1', '인증서비밀번호1', '계좌비밀번호1', '아이디2', '비밀번호2', '인증서비밀번호2', '계좌비밀번호2']
columns_sc = ['Access_key', 'Secret_key']
columns_ss = ['모의투자', '알림소리', '체결강도차이', '평균시간', '거래대금차이', '체결강도하한',
              '누적거래대금하한', '등락율하한', '등락율상한', '청산수익률']
columns_st = ['str_bot', 'int_id']
