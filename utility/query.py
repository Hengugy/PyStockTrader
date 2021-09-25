import sqlite3
from utility.setting import ui_num, db_tradelist, db_stock_tick, db_coin_tick, db_setting


class Query:
    def __init__(self, windowQ, collectorQ, queryQ):
        self.windowQ = windowQ
        self.collectorQ = collectorQ
        self.queryQ = queryQ
        self.con1 = sqlite3.connect(db_setting)
        self.cur1 = self.con1.cursor()
        self.con2 = sqlite3.connect(db_tradelist)
        self.cur2 = self.con2.cursor()
        self.con3 = sqlite3.connect(db_stock_tick)
        self.con4 = sqlite3.connect(db_coin_tick)
        self.Start()

    def __del__(self):
        self.con1.close()
        self.con2.close()
        self.con3.close()
        self.con4.close()

    def Start(self):
        k = 1
        while True:
            query = self.queryQ.get()
            if len(query) == 2:
                if query[0] == 1:
                    try:
                        self.cur1.execute(query[1])
                    except Exception as e:
                        self.windowQ.put([ui_num['설정텍스트'], f'시스템 명령 오류 알림 - 입력값이 잘못되었습니다. {e}'])
                    else:
                        self.con1.commit()
                elif query[0] == 2:
                    try:
                        self.cur2.execute(query[1])
                    except Exception as e:
                        self.windowQ.put([ui_num['S로그텍스트'], f'시스템 명령 오류 알림 - 입력값이 잘못되었습니다. {e}'])
                    else:
                        self.con2.commit()
                elif query[0] == 3:
                    j = 1
                    for code in list(query[1].keys()):
                        query[1][code].to_sql(code, self.con3, if_exists='append', chunksize=1000)
                        text = f'시스템 명령 실행 알림 - 틱데이터 저장 중...Proc[{k}/8] Dict[{j}/{len(query)}]'
                        self.windowQ.put([ui_num['S단순텍스트'], text])
                        j += 1
                    k += 1
                    if k == 9:
                        self.collectorQ.put('틱데이터 저장 완료')
                elif query[0] == 4:
                    for ticker in list(query[1].keys()):
                        query[1][ticker].to_sql(ticker, self.con4, if_exists='append', chunksize=1000)
                    text = f'시스템 명령 실행 알림 - 틱데이터 저장 완료'
                    self.windowQ.put([ui_num['C단순텍스트'], text])
            elif len(query) == 4:
                if query[0] == 1:
                    query[1].to_sql(query[2], self.con1, if_exists=query[3], chunksize=1000)
                elif query[0] == 2:
                    query[1].to_sql(query[2], self.con2, if_exists=query[3], chunksize=1000)
                elif query[0] == 3:
                    query[1].to_sql(query[2], self.con3, if_exists=query[3], chunksize=1000)
