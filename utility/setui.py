from PyQt5.QtCore import Qt
from PyQt5 import QtCore, QtGui, QtWidgets
from utility.setting import *


class TabBar(QtWidgets.QTabBar):
    def tabSizeHint(self, index):
        s = QtWidgets.QTabBar.tabSizeHint(self, index)
        s.setWidth(50)
        s.setHeight(40)
        s.transpose()
        return s

    def paintEvent(self, event):
        painter = QtWidgets.QStylePainter(self)
        opt = QtWidgets.QStyleOptionTab()

        for i in range(self.count()):
            self.initStyleOption(opt, i)
            painter.drawControl(QtWidgets.QStyle.CE_TabBarTabShape, opt)
            painter.save()

            s = opt.rect.size()
            s.transpose()
            r = QtCore.QRect(QtCore.QPoint(), s)
            r.moveCenter(opt.rect.center())
            opt.rect = r

            c = self.tabRect(i).center()
            painter.translate(c)
            painter.rotate(90)
            painter.translate(-c)
            painter.drawControl(QtWidgets.QStyle.CE_TabBarTabLabel, opt)
            painter.restore()


class TabWidget(QtWidgets.QTabWidget):
    def __init__(self, *args, **kwargs):
        QtWidgets.QTabWidget.__init__(self, *args, **kwargs)
        self.setTabBar(TabBar(self))
        self.setTabPosition(QtWidgets.QTabWidget.West)


class ProxyStyle(QtWidgets.QProxyStyle):
    def drawControl(self, element, opt, painter, widget=None):
        if element == QtWidgets.QStyle.CE_TabBarTabLabel:
            ic = self.pixelMetric(QtWidgets.QStyle.PM_TabBarIconSize)
            r = QtCore.QRect(opt.rect)
            w = 0 if opt.icon.isNull() else opt.rect.width() + ic
            r.setHeight(opt.fontMetrics.width(opt.text) + w)
            r.moveBottom(opt.rect.bottom())
            opt.rect = r
        QtWidgets.QProxyStyle.drawControl(self, element, opt, painter, widget)


def SetUI(self):
    def setPushbutton(name, box=None, click=None, cmd=None):
        if box is not None:
            pushbutton = QtWidgets.QPushButton(name, box)
        else:
            pushbutton = QtWidgets.QPushButton(name, self)
        pushbutton.setStyleSheet(style_bc_bt)
        pushbutton.setFont(qfont)
        if click is not None:
            if cmd is not None:
                pushbutton.clicked.connect(lambda: click(cmd))
            else:
                pushbutton.clicked.connect(click)
        return pushbutton

    def setTextEdit(tab):
        textedit = QtWidgets.QTextEdit(tab)
        textedit.setReadOnly(True)
        textedit.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        textedit.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        textedit.setStyleSheet(style_bc_dk)
        return textedit

    def setLineedit(groupbox):
        lineedit = QtWidgets.QLineEdit(groupbox)
        lineedit.setAlignment(Qt.AlignRight)
        lineedit.setStyleSheet(style_fc_bt)
        lineedit.setFont(qfont)
        return lineedit

    def setTablewidget(tab, columns, colcount, rowcount, sectionsize=None, clicked=None, color=False):
        tableWidget = QtWidgets.QTableWidget(tab)
        if sectionsize is not None:
            tableWidget.verticalHeader().setDefaultSectionSize(sectionsize)
        else:
            tableWidget.verticalHeader().setDefaultSectionSize(23)
        tableWidget.verticalHeader().setVisible(False)
        tableWidget.setAlternatingRowColors(True)
        tableWidget.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        tableWidget.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        tableWidget.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        tableWidget.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        tableWidget.setColumnCount(len(columns))
        tableWidget.setRowCount(rowcount)
        tableWidget.setHorizontalHeaderLabels(columns)
        if columns[-1] == 'chhigh':
            tableWidget.setColumnWidth(0, 122)
            tableWidget.setColumnWidth(1, 68)
            tableWidget.setColumnWidth(2, 68)
            tableWidget.setColumnWidth(3, 68)
            tableWidget.setColumnWidth(4, 68)
            tableWidget.setColumnWidth(5, 68)
            tableWidget.setColumnWidth(6, 68)
            tableWidget.setColumnWidth(7, 68)
            tableWidget.setColumnWidth(8, 68)
        else:
            if columns[0] in ['기간', '일자']:
                tableWidget.setColumnWidth(0, 100)
                tableWidget.setColumnWidth(1, 100)
                tableWidget.setColumnWidth(2, 100)
                tableWidget.setColumnWidth(3, 100)
                tableWidget.setColumnWidth(4, 100)
                tableWidget.setColumnWidth(5, 66)
                tableWidget.setColumnWidth(6, 100)
            else:
                tableWidget.setColumnWidth(0, 126)
                tableWidget.setColumnWidth(1, 90)
                tableWidget.setColumnWidth(2, 90)
                tableWidget.setColumnWidth(3, 90)
                tableWidget.setColumnWidth(4, 90)
                tableWidget.setColumnWidth(5, 90)
                tableWidget.setColumnWidth(6, 90)
            if colcount >= 8:
                tableWidget.setColumnWidth(7, 90)
        if clicked is not None:
            tableWidget.cellClicked.connect(clicked)
        if color:
            for i in range(22):
                tableitem = QtWidgets.QTableWidgetItem()
                tableitem.setBackground(color_bg_bt)
                tableWidget.setItem(i, 0, tableitem)
        return tableWidget

    self.setFont(qfont)
    self.setWindowTitle('PyStockTrader')
    self.setWindowIcon(QtGui.QIcon(f'{system_path}/icon/python.png'))

    self.main_tabWidget = TabWidget(self)
    self.td_tab = QtWidgets.QWidget()
    self.bt_tab = QtWidgets.QWidget()
    self.sj_tab = QtWidgets.QWidget()
    self.lg_tab = QtWidgets.QWidget()

    self.main_tabWidget.addTab(self.td_tab, 'TD')
    self.main_tabWidget.addTab(self.bt_tab, 'BT')
    self.main_tabWidget.addTab(self.sj_tab, 'SJ')
    self.main_tabWidget.addTab(self.lg_tab, 'LO')

    self.tt_pushButton = setPushbutton('T', click=self.ButtonClicked_1)
    self.zo_pushButton = setPushbutton('Z', click=self.ButtonClicked_2)
    self.bd_pushButton = setPushbutton('BD', click=self.ButtonClicked_4)
    self.dd_pushButton = setPushbutton('DD', click=self.ButtonClicked_5)
    self.sd_pushButton = setPushbutton('AD', click=self.ButtonClicked_6)

    self.progressBar = QtWidgets.QProgressBar(self)
    self.progressBar.setAlignment(Qt.AlignCenter)
    self.progressBar.setOrientation(Qt.Vertical)
    self.progressBar.setRange(0, 100)
    self.progressBar.setStyleSheet(
        'QProgressBar {background-color: #28282d;} QProgressBar::chunk {background-color: #5a5a5f;}'
    )

    self.tt_tableWidget = setTablewidget(self.td_tab, columns_tt, len(columns_tt), 1)
    self.td_tableWidget = setTablewidget(self.td_tab, columns_td, len(columns_td), 13)
    self.tj_tableWidget = setTablewidget(self.td_tab, columns_tj, len(columns_tj), 1)
    self.jg_tableWidget = setTablewidget(self.td_tab, columns_jg, len(columns_jg), 13)
    self.gj_tableWidget = setTablewidget(self.td_tab, columns_gj3, len(columns_gj3), 15)
    self.cj_tableWidget = setTablewidget(self.td_tab, columns_cj, len(columns_cj), 15)

    self.calendarWidget = QtWidgets.QCalendarWidget(self.td_tab)
    todayDate = QtCore.QDate.currentDate()
    self.calendarWidget.setCurrentPage(todayDate.year(), todayDate.month())
    self.calendarWidget.clicked.connect(self.CalendarClicked)
    self.dt_tableWidget = setTablewidget(self.td_tab, columns_dt, len(columns_dt), 1)
    self.ds_tableWidget = setTablewidget(self.td_tab, columns_dd, len(columns_dd), 19)

    self.nt_pushButton_01 = setPushbutton('일별집계', box=self.td_tab, click=self.ButtonClicked_7, cmd='S일별집계')
    self.nt_pushButton_02 = setPushbutton('월별집계', box=self.td_tab, click=self.ButtonClicked_7, cmd='S월별집계')
    self.nt_pushButton_03 = setPushbutton('연도별집계', box=self.td_tab, click=self.ButtonClicked_7, cmd='S연도별집계')
    self.nt_tableWidget = setTablewidget(self.td_tab, columns_nt, len(columns_nt), 1)
    self.ns_tableWidget = setTablewidget(self.td_tab, columns_nd, len(columns_nd), 28)

    self.calendarWidget.setVisible(False)
    self.dt_tableWidget.setVisible(False)
    self.ds_tableWidget.setVisible(False)
    self.nt_pushButton_01.setVisible(False)
    self.nt_pushButton_02.setVisible(False)
    self.nt_pushButton_03.setVisible(False)
    self.nt_tableWidget.setVisible(False)
    self.ns_tableWidget.setVisible(False)

    self.sb_groupBox_01 = QtWidgets.QGroupBox(' 주식 변수최적화 백테스터', self.bt_tab)
    self.sb_groupBox_02 = QtWidgets.QGroupBox(' 주식 변수지정 백테스터', self.bt_tab)
    self.cb_groupBox_01 = QtWidgets.QGroupBox(' 코인 변수최적화 백테스터', self.bt_tab)
    self.cb_groupBox_02 = QtWidgets.QGroupBox(' 코인 변수지정 백테스터', self.bt_tab)

    self.sb_jcvc_labellll_01 = QtWidgets.QLabel('종목당투자금', self.sb_groupBox_01)
    self.sb_jcvc_labellll_02 = QtWidgets.QLabel('백테스팅기간', self.sb_groupBox_01)
    self.sb_jcvc_labellll_03 = QtWidgets.QLabel('백테스팅시간', self.sb_groupBox_01)
    text = '체결강도차이  [                   ,                   ,                   ,                   ,' \
           '                   ,                   ,                   ]                   ,                   ]'
    self.sb_jcvc_labellll_04 = QtWidgets.QLabel(text, self.sb_groupBox_01)
    text = '평균시간         [                   ,                   ,                   ,                   ,' \
           '                   ,                   ]                   ,                   ]'
    self.sb_jcvc_labellll_05 = QtWidgets.QLabel(text, self.sb_groupBox_01)
    text = '거래대금차이  [                                       ,                                       ,' \
           '                                       ,                                       ]'
    self.sb_jcvc_labellll_06 = QtWidgets.QLabel(text, self.sb_groupBox_01)
    text = '체결강도하한  [                   ,                   ,                   ,                   ]'
    self.sb_jcvc_labellll_07 = QtWidgets.QLabel(text, self.sb_groupBox_01)
    text = '거래대금하한  [                                       ,                                       ,' \
           '                                       ,                                       ]'
    self.sb_jcvc_labellll_08 = QtWidgets.QLabel(text, self.sb_groupBox_01)
    text = '등락율하한      [                   ,                   ,                   ,                   ]'
    self.sb_jcvc_labellll_09 = QtWidgets.QLabel(text, self.sb_groupBox_01)
    text = '등락율상한      [                   ,                   ,                   ,                   ]'
    self.sb_jcvc_labellll_10 = QtWidgets.QLabel(text, self.sb_groupBox_01)
    text = '청산수익률      [                   ,                   ,                   ,                   ]'
    self.sb_jcvc_labellll_11 = QtWidgets.QLabel(text, self.sb_groupBox_01)
    self.sb_jcvc_labellll_12 = QtWidgets.QLabel('멀티 프로세스', self.sb_groupBox_01)

    self.sb_jcvc_lineEdit_01 = setLineedit(self.sb_groupBox_01)
    self.sb_jcvc_lineEdit_02 = setLineedit(self.sb_groupBox_01)
    self.sb_jcvc_lineEdit_03 = setLineedit(self.sb_groupBox_01)
    self.sb_jcvc_lineEdit_04 = setLineedit(self.sb_groupBox_01)
    self.sb_jcvc_lineEdit_05 = setLineedit(self.sb_groupBox_01)
    self.sb_jcvc_lineEdit_06 = setLineedit(self.sb_groupBox_01)
    self.sb_jcvc_lineEdit_07 = setLineedit(self.sb_groupBox_01)
    self.sb_jcvc_lineEdit_08 = setLineedit(self.sb_groupBox_01)
    self.sb_jcvc_lineEdit_09 = setLineedit(self.sb_groupBox_01)
    self.sb_jcvc_lineEdit_10 = setLineedit(self.sb_groupBox_01)
    self.sb_jcvc_lineEdit_11 = setLineedit(self.sb_groupBox_01)
    self.sb_jcvc_lineEdit_12 = setLineedit(self.sb_groupBox_01)
    self.sb_jcvc_lineEdit_13 = setLineedit(self.sb_groupBox_01)
    self.sb_jcvc_lineEdit_14 = setLineedit(self.sb_groupBox_01)
    self.sb_jcvc_lineEdit_15 = setLineedit(self.sb_groupBox_01)
    self.sb_jcvc_lineEdit_16 = setLineedit(self.sb_groupBox_01)
    self.sb_jcvc_lineEdit_17 = setLineedit(self.sb_groupBox_01)
    self.sb_jcvc_lineEdit_18 = setLineedit(self.sb_groupBox_01)
    self.sb_jcvc_lineEdit_19 = setLineedit(self.sb_groupBox_01)
    self.sb_jcvc_lineEdit_20 = setLineedit(self.sb_groupBox_01)
    self.sb_jcvc_lineEdit_21 = setLineedit(self.sb_groupBox_01)
    self.sb_jcvc_lineEdit_22 = setLineedit(self.sb_groupBox_01)
    self.sb_jcvc_lineEdit_23 = setLineedit(self.sb_groupBox_01)
    self.sb_jcvc_lineEdit_24 = setLineedit(self.sb_groupBox_01)
    self.sb_jcvc_lineEdit_25 = setLineedit(self.sb_groupBox_01)
    self.sb_jcvc_lineEdit_26 = setLineedit(self.sb_groupBox_01)
    self.sb_jcvc_lineEdit_27 = setLineedit(self.sb_groupBox_01)
    self.sb_jcvc_lineEdit_28 = setLineedit(self.sb_groupBox_01)
    self.sb_jcvc_lineEdit_29 = setLineedit(self.sb_groupBox_01)
    self.sb_jcvc_lineEdit_30 = setLineedit(self.sb_groupBox_01)
    self.sb_jcvc_lineEdit_31 = setLineedit(self.sb_groupBox_01)
    self.sb_jcvc_lineEdit_32 = setLineedit(self.sb_groupBox_01)
    self.sb_jcvc_lineEdit_33 = setLineedit(self.sb_groupBox_01)
    self.sb_jcvc_lineEdit_34 = setLineedit(self.sb_groupBox_01)
    self.sb_jcvc_lineEdit_35 = setLineedit(self.sb_groupBox_01)
    self.sb_jcvc_lineEdit_36 = setLineedit(self.sb_groupBox_01)
    self.sb_jcvc_lineEdit_37 = setLineedit(self.sb_groupBox_01)
    self.sb_jcvc_lineEdit_38 = setLineedit(self.sb_groupBox_01)
    self.sb_jcvc_lineEdit_39 = setLineedit(self.sb_groupBox_01)
    self.sb_jcvc_lineEdit_40 = setLineedit(self.sb_groupBox_01)
    self.sb_jcvc_lineEdit_41 = setLineedit(self.sb_groupBox_01)
    self.sb_jcvc_lineEdit_42 = setLineedit(self.sb_groupBox_01)
    self.sb_jcvc_lineEdit_43 = setLineedit(self.sb_groupBox_01)
    self.sb_jcvc_lineEdit_44 = setLineedit(self.sb_groupBox_01)
    self.sb_jcvc_lineEdit_45 = setLineedit(self.sb_groupBox_01)

    self.sb_jcvc_pushButton_01 = setPushbutton('기본값 불러오기', box=self.sb_groupBox_01, click=self.ButtonClicked_8)
    self.sb_jcvc_pushButton_02 = setPushbutton('백테스터 시작', box=self.sb_groupBox_01, click=self.ButtonClicked_9)
    self.sb_jcvc_pushButton_03 = setPushbutton('기본값 변경하기', box=self.sb_groupBox_01, click=self.ButtonClicked_10)

    text = '종목당투자금                       백만'
    self.sb_jcvj_labellll_01 = QtWidgets.QLabel(text, self.sb_groupBox_02)
    text = '백테스팅기간                       일 : 거래일수X, 14일이면 10거래일'
    self.sb_jcvj_labellll_02 = QtWidgets.QLabel(text, self.sb_groupBox_02)
    text = '백테스팅시간                                            초 : 하루 1시간 3600초 * 거래일수'
    self.sb_jcvj_labellll_03 = QtWidgets.QLabel(text, self.sb_groupBox_02)
    text = '체결강도차이                        % : 1초전 평균체결강도 대비 증가한 초당 체결강도'
    self.sb_jcvj_labellll_04 = QtWidgets.QLabel(text, self.sb_groupBox_02)
    text = '평균시간                               초 : 체결강도 및 초당 거래대금의 평균값 계산용 시간'
    self.sb_jcvj_labellll_05 = QtWidgets.QLabel(text, self.sb_groupBox_02)
    text = '거래대금차이                                            백만 : 1초전 평균거래대금 대비 증가한 초당 거래대금'
    self.sb_jcvj_labellll_06 = QtWidgets.QLabel(text, self.sb_groupBox_02)
    text = '체결강도하한                        % : 초당 체결강도'
    self.sb_jcvj_labellll_07 = QtWidgets.QLabel(text, self.sb_groupBox_02)
    text = '거래대금하한                                            백만 : 당일 거래대금'
    self.sb_jcvj_labellll_08 = QtWidgets.QLabel(text, self.sb_groupBox_02)
    text = '등락율하한                           % : 전일종가 대비 등락율'
    self.sb_jcvj_labellll_09 = QtWidgets.QLabel(text, self.sb_groupBox_02)
    text = '등락율상한                           % : 전일종가 대비 등락율'
    self.sb_jcvj_labellll_10 = QtWidgets.QLabel(text, self.sb_groupBox_02)
    text = '청산수익률                           % : 매수가 대비 수익률'
    self.sb_jcvj_labellll_11 = QtWidgets.QLabel(text, self.sb_groupBox_02)
    text = '멀티 프로세스                       개'
    self.sb_jcvj_labellll_12 = QtWidgets.QLabel(text, self.sb_groupBox_02)

    self.sb_jcvj_lineEdit_01 = setLineedit(self.sb_groupBox_02)
    self.sb_jcvj_lineEdit_02 = setLineedit(self.sb_groupBox_02)
    self.sb_jcvj_lineEdit_03 = setLineedit(self.sb_groupBox_02)
    self.sb_jcvj_lineEdit_04 = setLineedit(self.sb_groupBox_02)
    self.sb_jcvj_lineEdit_05 = setLineedit(self.sb_groupBox_02)
    self.sb_jcvj_lineEdit_06 = setLineedit(self.sb_groupBox_02)
    self.sb_jcvj_lineEdit_07 = setLineedit(self.sb_groupBox_02)
    self.sb_jcvj_lineEdit_08 = setLineedit(self.sb_groupBox_02)
    self.sb_jcvj_lineEdit_09 = setLineedit(self.sb_groupBox_02)
    self.sb_jcvj_lineEdit_10 = setLineedit(self.sb_groupBox_02)
    self.sb_jcvj_lineEdit_11 = setLineedit(self.sb_groupBox_02)
    self.sb_jcvj_lineEdit_12 = setLineedit(self.sb_groupBox_02)

    self.sb_jcvj_pushButton_01 = setPushbutton('최적값 불러오기', box=self.sb_groupBox_02, click=self.ButtonClicked_11)
    self.sb_jcvj_pushButton_02 = setPushbutton('백테스터 시작', box=self.sb_groupBox_02, click=self.ButtonClicked_12)

    self.cb_jjvc_labellll_01 = QtWidgets.QLabel('종목당투자금', self.cb_groupBox_01)
    self.cb_jjvc_labellll_02 = QtWidgets.QLabel('백테스팅기간', self.cb_groupBox_01)
    self.cb_jjvc_labellll_03 = QtWidgets.QLabel('백테스팅시간', self.cb_groupBox_01)
    text = '체결강도차이  [                   ,                   ,                   ,                   ,' \
           '                   ,                   ,                   ]                   ,                   ]'
    self.cb_jjvc_labellll_04 = QtWidgets.QLabel(text, self.cb_groupBox_01)
    text = '평균시간         [                   ,                   ,                   ,                   ,' \
           '                   ,                   ]                   ,                   ]'
    self.cb_jjvc_labellll_05 = QtWidgets.QLabel(text, self.cb_groupBox_01)
    text = '거래대금차이  [                                       ,                                       ,' \
           '                                       ,                                       ]'
    self.cb_jjvc_labellll_06 = QtWidgets.QLabel(text, self.cb_groupBox_01)
    text = '체결강도하한  [                   ,                   ,                   ,                   ]'
    self.cb_jjvc_labellll_07 = QtWidgets.QLabel(text, self.cb_groupBox_01)
    text = '거래대금하한  [                                       ,                                       ,' \
           '                                       ,                                       ]'
    self.cb_jjvc_labellll_08 = QtWidgets.QLabel(text, self.cb_groupBox_01)
    text = '등락율하한      [                   ,                   ,                   ,                   ]'
    self.cb_jjvc_labellll_09 = QtWidgets.QLabel(text, self.cb_groupBox_01)
    text = '등락율상한      [                   ,                   ,                   ,                   ]'
    self.cb_jjvc_labellll_10 = QtWidgets.QLabel(text, self.cb_groupBox_01)
    text = '청산수익률      [                   ,                   ,                   ,                   ]'
    self.cb_jjvc_labellll_11 = QtWidgets.QLabel(text, self.cb_groupBox_01)
    self.cb_jjvc_labellll_12 = QtWidgets.QLabel('멀티 프로세스', self.cb_groupBox_01)

    self.cb_jjvc_lineEdit_01 = setLineedit(self.cb_groupBox_01)
    self.cb_jjvc_lineEdit_02 = setLineedit(self.cb_groupBox_01)
    self.cb_jjvc_lineEdit_03 = setLineedit(self.cb_groupBox_01)
    self.cb_jjvc_lineEdit_04 = setLineedit(self.cb_groupBox_01)
    self.cb_jjvc_lineEdit_05 = setLineedit(self.cb_groupBox_01)
    self.cb_jjvc_lineEdit_06 = setLineedit(self.cb_groupBox_01)
    self.cb_jjvc_lineEdit_07 = setLineedit(self.cb_groupBox_01)
    self.cb_jjvc_lineEdit_08 = setLineedit(self.cb_groupBox_01)
    self.cb_jjvc_lineEdit_09 = setLineedit(self.cb_groupBox_01)
    self.cb_jjvc_lineEdit_10 = setLineedit(self.cb_groupBox_01)
    self.cb_jjvc_lineEdit_11 = setLineedit(self.cb_groupBox_01)
    self.cb_jjvc_lineEdit_12 = setLineedit(self.cb_groupBox_01)
    self.cb_jjvc_lineEdit_13 = setLineedit(self.cb_groupBox_01)
    self.cb_jjvc_lineEdit_14 = setLineedit(self.cb_groupBox_01)
    self.cb_jjvc_lineEdit_15 = setLineedit(self.cb_groupBox_01)
    self.cb_jjvc_lineEdit_16 = setLineedit(self.cb_groupBox_01)
    self.cb_jjvc_lineEdit_17 = setLineedit(self.cb_groupBox_01)
    self.cb_jjvc_lineEdit_18 = setLineedit(self.cb_groupBox_01)
    self.cb_jjvc_lineEdit_19 = setLineedit(self.cb_groupBox_01)
    self.cb_jjvc_lineEdit_20 = setLineedit(self.cb_groupBox_01)
    self.cb_jjvc_lineEdit_21 = setLineedit(self.cb_groupBox_01)
    self.cb_jjvc_lineEdit_22 = setLineedit(self.cb_groupBox_01)
    self.cb_jjvc_lineEdit_23 = setLineedit(self.cb_groupBox_01)
    self.cb_jjvc_lineEdit_24 = setLineedit(self.cb_groupBox_01)
    self.cb_jjvc_lineEdit_25 = setLineedit(self.cb_groupBox_01)
    self.cb_jjvc_lineEdit_26 = setLineedit(self.cb_groupBox_01)
    self.cb_jjvc_lineEdit_27 = setLineedit(self.cb_groupBox_01)
    self.cb_jjvc_lineEdit_28 = setLineedit(self.cb_groupBox_01)
    self.cb_jjvc_lineEdit_29 = setLineedit(self.cb_groupBox_01)
    self.cb_jjvc_lineEdit_30 = setLineedit(self.cb_groupBox_01)
    self.cb_jjvc_lineEdit_31 = setLineedit(self.cb_groupBox_01)
    self.cb_jjvc_lineEdit_32 = setLineedit(self.cb_groupBox_01)
    self.cb_jjvc_lineEdit_33 = setLineedit(self.cb_groupBox_01)
    self.cb_jjvc_lineEdit_34 = setLineedit(self.cb_groupBox_01)
    self.cb_jjvc_lineEdit_35 = setLineedit(self.cb_groupBox_01)
    self.cb_jjvc_lineEdit_36 = setLineedit(self.cb_groupBox_01)
    self.cb_jjvc_lineEdit_37 = setLineedit(self.cb_groupBox_01)
    self.cb_jjvc_lineEdit_38 = setLineedit(self.cb_groupBox_01)
    self.cb_jjvc_lineEdit_39 = setLineedit(self.cb_groupBox_01)
    self.cb_jjvc_lineEdit_40 = setLineedit(self.cb_groupBox_01)
    self.cb_jjvc_lineEdit_41 = setLineedit(self.cb_groupBox_01)
    self.cb_jjvc_lineEdit_42 = setLineedit(self.cb_groupBox_01)
    self.cb_jjvc_lineEdit_43 = setLineedit(self.cb_groupBox_01)
    self.cb_jjvc_lineEdit_44 = setLineedit(self.cb_groupBox_01)
    self.cb_jjvc_lineEdit_45 = setLineedit(self.cb_groupBox_01)

    self.cb_jjvc_pushButton_01 = setPushbutton('기본값 불러오기', box=self.cb_groupBox_01, click=self.ButtonClicked_13)
    self.cb_jjvc_pushButton_02 = setPushbutton('백테스터 시작', box=self.cb_groupBox_01, click=self.ButtonClicked_14)
    self.cb_jjvc_pushButton_03 = setPushbutton('기본값 변경하기', box=self.cb_groupBox_01, click=self.ButtonClicked_15)

    text = '종목당투자금                       백만'
    self.cb_jjvj_labellll_01 = QtWidgets.QLabel(text, self.cb_groupBox_02)
    text = '백테스팅기간                       일 : 거래일수X, 14일이면 10거래일'
    self.cb_jjvj_labellll_02 = QtWidgets.QLabel(text, self.cb_groupBox_02)
    text = '백테스팅시간                                            초 : 하루 5.5시간 19800초 * 거래일수'
    self.cb_jjvj_labellll_03 = QtWidgets.QLabel(text, self.cb_groupBox_02)
    text = '체결강도차이                        % : 1초전 평균체결강도 대비 증가한 초당 체결강도'
    self.cb_jjvj_labellll_04 = QtWidgets.QLabel(text, self.cb_groupBox_02)
    text = '평균시간                               초 : 체결강도 및 초당 거래대금의 평균값 계산용 시간'
    self.cb_jjvj_labellll_05 = QtWidgets.QLabel(text, self.cb_groupBox_02)
    text = '거래대금차이                                            1초전 평균거래대금 대비 증가한 초당 거래대금'
    self.cb_jjvj_labellll_06 = QtWidgets.QLabel(text, self.cb_groupBox_02)
    text = '체결강도하한                        % : 초당 체결강도'
    self.cb_jjvj_labellll_07 = QtWidgets.QLabel(text, self.cb_groupBox_02)
    text = '거래대금하한                                            당일 거래대금'
    self.cb_jjvj_labellll_08 = QtWidgets.QLabel(text, self.cb_groupBox_02)
    text = '등락율하한                           % : 전일종가 대비 등락율'
    self.cb_jjvj_labellll_09 = QtWidgets.QLabel(text, self.cb_groupBox_02)
    text = '등락율상한                           % : 전일종가 대비 등락율'
    self.cb_jjvj_labellll_10 = QtWidgets.QLabel(text, self.cb_groupBox_02)
    text = '청산수익률                           % : 매수가 대비 수익률'
    self.cb_jjvj_labellll_11 = QtWidgets.QLabel(text, self.cb_groupBox_02)
    text = '멀티 프로세스                       개'
    self.cb_jjvj_labellll_12 = QtWidgets.QLabel(text, self.cb_groupBox_02)

    self.cb_jjvj_lineEdit_01 = setLineedit(self.cb_groupBox_02)
    self.cb_jjvj_lineEdit_02 = setLineedit(self.cb_groupBox_02)
    self.cb_jjvj_lineEdit_03 = setLineedit(self.cb_groupBox_02)
    self.cb_jjvj_lineEdit_04 = setLineedit(self.cb_groupBox_02)
    self.cb_jjvj_lineEdit_05 = setLineedit(self.cb_groupBox_02)
    self.cb_jjvj_lineEdit_06 = setLineedit(self.cb_groupBox_02)
    self.cb_jjvj_lineEdit_07 = setLineedit(self.cb_groupBox_02)
    self.cb_jjvj_lineEdit_08 = setLineedit(self.cb_groupBox_02)
    self.cb_jjvj_lineEdit_09 = setLineedit(self.cb_groupBox_02)
    self.cb_jjvj_lineEdit_10 = setLineedit(self.cb_groupBox_02)
    self.cb_jjvj_lineEdit_11 = setLineedit(self.cb_groupBox_02)
    self.cb_jjvj_lineEdit_12 = setLineedit(self.cb_groupBox_02)

    self.cb_jjvj_pushButton_01 = setPushbutton('최적값 불러오기', box=self.cb_groupBox_02, click=self.ButtonClicked_16)
    self.cb_jjvj_pushButton_02 = setPushbutton('백테스터 시작', box=self.cb_groupBox_02, click=self.ButtonClicked_17)

    title = ' 콜렉터 및 트레이더 : 프로그램 구동시 실행될 프로세스를 선택한다.'
    self.sj_groupBox_01 = QtWidgets.QGroupBox(title, self.sj_tab)
    title = ' 키움증권 계정 : 자동매매용 첫번째 계정과 틱수집 및 버전업용 두번째 계정을 설정한다.'
    self.sj_groupBox_02 = QtWidgets.QGroupBox(title, self.sj_tab)
    title = ' 업비트 계정 : 업비트 주문 및 주문 확인용 Access 키와 Srcret 키를 설정한다.'
    self.sj_groupBox_03 = QtWidgets.QGroupBox(title, self.sj_tab)
    title = ' 텔레그램 : 봇토큰 및 사용자 채팅 아이디를 설정한다.'
    self.sj_groupBox_04 = QtWidgets.QGroupBox(title, self.sj_tab)
    title = ' 주식 : 모의투자 모드와 알림소리, 전략의 세부 변수를 설정한다.'
    self.sj_groupBox_05 = QtWidgets.QGroupBox(title, self.sj_tab)
    title = ' 코인 : 모의투자 모드와 알림소리, 전략의 세부 변수를 설정한다.'
    self.sj_groupBox_06 = QtWidgets.QGroupBox(title, self.sj_tab)

    self.sj_textEdit = setTextEdit(self.sj_tab)

    self.sj_main_checkBox_01 = QtWidgets.QCheckBox('주식 콜렉터', self.sj_groupBox_01)
    self.sj_main_checkBox_02 = QtWidgets.QCheckBox('주식 트레이더', self.sj_groupBox_01)
    self.sj_main_checkBox_03 = QtWidgets.QCheckBox('코인 콜렉터', self.sj_groupBox_01)
    self.sj_main_checkBox_04 = QtWidgets.QCheckBox('코인 트레이더', self.sj_groupBox_01)

    self.sj_sacc_labellll_01 = QtWidgets.QLabel('첫번째 계정 아이디', self.sj_groupBox_02)
    self.sj_sacc_lineEdit_01 = setLineedit(self.sj_groupBox_02)
    self.sj_sacc_labellll_02 = QtWidgets.QLabel('비밀번호', self.sj_groupBox_02)
    self.sj_sacc_lineEdit_02 = setLineedit(self.sj_groupBox_02)
    self.sj_sacc_labellll_03 = QtWidgets.QLabel('인증서비밀번호', self.sj_groupBox_02)
    self.sj_sacc_lineEdit_03 = setLineedit(self.sj_groupBox_02)
    self.sj_sacc_labellll_04 = QtWidgets.QLabel('계좌비밀번호', self.sj_groupBox_02)
    self.sj_sacc_lineEdit_04 = setLineedit(self.sj_groupBox_02)
    self.sj_sacc_labellll_05 = QtWidgets.QLabel('두번째 계정 아이디', self.sj_groupBox_02)
    self.sj_sacc_lineEdit_05 = setLineedit(self.sj_groupBox_02)
    self.sj_sacc_labellll_06 = QtWidgets.QLabel('비밀번호', self.sj_groupBox_02)
    self.sj_sacc_lineEdit_06 = setLineedit(self.sj_groupBox_02)
    self.sj_sacc_labellll_07 = QtWidgets.QLabel('인증서비밀번호', self.sj_groupBox_02)
    self.sj_sacc_lineEdit_07 = setLineedit(self.sj_groupBox_02)
    self.sj_sacc_labellll_08 = QtWidgets.QLabel('계좌비밀번호', self.sj_groupBox_02)
    self.sj_sacc_lineEdit_08 = setLineedit(self.sj_groupBox_02)

    self.sj_cacc_labellll_01 = QtWidgets.QLabel('Access Key', self.sj_groupBox_03)
    self.sj_cacc_lineEdit_01 = setLineedit(self.sj_groupBox_03)
    self.sj_cacc_labellll_02 = QtWidgets.QLabel('Secret Key', self.sj_groupBox_03)
    self.sj_cacc_lineEdit_02 = setLineedit(self.sj_groupBox_03)

    self.sj_tele_labellll_01 = QtWidgets.QLabel('Bot Token', self.sj_groupBox_04)
    self.sj_tele_lineEdit_01 = setLineedit(self.sj_groupBox_04)
    self.sj_tele_labellll_02 = QtWidgets.QLabel('Chat Id', self.sj_groupBox_04)
    self.sj_tele_lineEdit_02 = setLineedit(self.sj_groupBox_04)

    self.sj_stock_checkBox_01 = QtWidgets.QCheckBox('모의투자', self.sj_groupBox_05)
    self.sj_stock_checkBox_02 = QtWidgets.QCheckBox('알림소리', self.sj_groupBox_05)
    self.sj_stock_labellll_01 = QtWidgets.QLabel('장초전략 체결강도차이', self.sj_groupBox_05)
    self.sj_stock_lineEdit_01 = setLineedit(self.sj_groupBox_05)
    self.sj_stock_labellll_02 = QtWidgets.QLabel('평균시간', self.sj_groupBox_05)
    self.sj_stock_lineEdit_02 = setLineedit(self.sj_groupBox_05)
    self.sj_stock_labellll_03 = QtWidgets.QLabel('거래대금차이', self.sj_groupBox_05)
    self.sj_stock_lineEdit_03 = setLineedit(self.sj_groupBox_05)
    self.sj_stock_labellll_04 = QtWidgets.QLabel('체결강도하한', self.sj_groupBox_05)
    self.sj_stock_lineEdit_04 = setLineedit(self.sj_groupBox_05)
    self.sj_stock_labellll_05 = QtWidgets.QLabel('누적거래대금하한', self.sj_groupBox_05)
    self.sj_stock_lineEdit_05 = setLineedit(self.sj_groupBox_05)
    self.sj_stock_labellll_06 = QtWidgets.QLabel('등락율하한', self.sj_groupBox_05)
    self.sj_stock_lineEdit_06 = setLineedit(self.sj_groupBox_05)
    self.sj_stock_labellll_07 = QtWidgets.QLabel('등락율상한', self.sj_groupBox_05)
    self.sj_stock_lineEdit_07 = setLineedit(self.sj_groupBox_05)
    self.sj_stock_labellll_08 = QtWidgets.QLabel('청산수익률', self.sj_groupBox_05)
    self.sj_stock_lineEdit_08 = setLineedit(self.sj_groupBox_05)

    self.sj_coin_checkBox_01 = QtWidgets.QCheckBox('모의투자', self.sj_groupBox_06)
    self.sj_coin_checkBox_02 = QtWidgets.QCheckBox('알림소리', self.sj_groupBox_06)
    self.sj_coin_labellll_01 = QtWidgets.QLabel('장중전략 체결강도차이', self.sj_groupBox_06)
    self.sj_coin_lineEdit_01 = setLineedit(self.sj_groupBox_06)
    self.sj_coin_labellll_02 = QtWidgets.QLabel('평균시간', self.sj_groupBox_06)
    self.sj_coin_lineEdit_02 = setLineedit(self.sj_groupBox_06)
    self.sj_coin_labellll_03 = QtWidgets.QLabel('거래대금차이', self.sj_groupBox_06)
    self.sj_coin_lineEdit_03 = setLineedit(self.sj_groupBox_06)
    self.sj_coin_labellll_04 = QtWidgets.QLabel('체결강도하한', self.sj_groupBox_06)
    self.sj_coin_lineEdit_04 = setLineedit(self.sj_groupBox_06)
    self.sj_coin_labellll_05 = QtWidgets.QLabel('누적거래대금하한', self.sj_groupBox_06)
    self.sj_coin_lineEdit_05 = setLineedit(self.sj_groupBox_06)
    self.sj_coin_labellll_06 = QtWidgets.QLabel('등락율하한', self.sj_groupBox_06)
    self.sj_coin_lineEdit_06 = setLineedit(self.sj_groupBox_06)
    self.sj_coin_labellll_07 = QtWidgets.QLabel('등락율상한', self.sj_groupBox_06)
    self.sj_coin_lineEdit_07 = setLineedit(self.sj_groupBox_06)
    self.sj_coin_labellll_08 = QtWidgets.QLabel('청산수익률', self.sj_groupBox_06)
    self.sj_coin_lineEdit_08 = setLineedit(self.sj_groupBox_06)

    self.sj_load_pushButton_01 = setPushbutton('불러오기', box=self.sj_groupBox_01, click=self.ButtonClicked_18)
    self.sj_load_pushButton_02 = setPushbutton('불러오기', box=self.sj_groupBox_02, click=self.ButtonClicked_19)
    self.sj_load_pushButton_03 = setPushbutton('불러오기', box=self.sj_groupBox_03, click=self.ButtonClicked_20)
    self.sj_load_pushButton_04 = setPushbutton('불러오기', box=self.sj_groupBox_04, click=self.ButtonClicked_21)
    self.sj_load_pushButton_05 = setPushbutton('불러오기', box=self.sj_groupBox_05, click=self.ButtonClicked_22)
    self.sj_load_pushButton_06 = setPushbutton('불러오기', box=self.sj_groupBox_06, click=self.ButtonClicked_23)

    self.sj_save_pushButton_01 = setPushbutton('저장하기', box=self.sj_groupBox_01, click=self.ButtonClicked_24)
    self.sj_save_pushButton_02 = setPushbutton('저장하기', box=self.sj_groupBox_02, click=self.ButtonClicked_25)
    self.sj_save_pushButton_03 = setPushbutton('저장하기', box=self.sj_groupBox_03, click=self.ButtonClicked_26)
    self.sj_save_pushButton_04 = setPushbutton('저장하기', box=self.sj_groupBox_04, click=self.ButtonClicked_27)
    self.sj_save_pushButton_05 = setPushbutton('저장하기', box=self.sj_groupBox_05, click=self.ButtonClicked_28)
    self.sj_save_pushButton_06 = setPushbutton('저장하기', box=self.sj_groupBox_06, click=self.ButtonClicked_29)

    self.st_textEdit = setTextEdit(self.lg_tab)
    self.ct_textEdit = setTextEdit(self.lg_tab)
    self.sc_textEdit = setTextEdit(self.lg_tab)
    self.cc_textEdit = setTextEdit(self.lg_tab)

    self.resize(1403, 763)
    self.geometry().center()
    self.main_tabWidget.setGeometry(5, 5, 1393, 753)
    self.tt_pushButton.setGeometry(5, 210, 35, 32)
    self.zo_pushButton.setGeometry(5, 246, 35, 32)
    self.progressBar.setGeometry(6, 285, 33, 360)
    self.bd_pushButton.setGeometry(5, 650, 35, 32)
    self.dd_pushButton.setGeometry(5, 687, 35, 32)
    self.sd_pushButton.setGeometry(5, 724, 35, 32)

    self.tt_tableWidget.setGeometry(5, 5, 668, 42)
    self.td_tableWidget.setGeometry(5, 52, 668, 320)
    self.tj_tableWidget.setGeometry(5, 377, 668, 42)
    self.jg_tableWidget.setGeometry(5, 424, 668, 320)
    self.gj_tableWidget.setGeometry(678, 5, 668, 367)
    self.cj_tableWidget.setGeometry(678, 377, 668, 367)

    self.calendarWidget.setGeometry(5, 5, 668, 245)
    self.dt_tableWidget.setGeometry(5, 255, 668, 42)
    self.ds_tableWidget.setGeometry(5, 302, 668, 442)

    self.nt_pushButton_01.setGeometry(678, 5, 219, 30)
    self.nt_pushButton_02.setGeometry(902, 5, 219, 30)
    self.nt_pushButton_03.setGeometry(1126, 5, 220, 30)
    self.nt_tableWidget.setGeometry(678, 40, 668, 42)
    self.ns_tableWidget.setGeometry(678, 87, 668, 657)

    self.sb_groupBox_01.setGeometry(5, 10, 668, 360)
    self.sb_groupBox_02.setGeometry(5, 382, 668, 360)
    self.cb_groupBox_01.setGeometry(678, 10, 668, 360)
    self.cb_groupBox_02.setGeometry(678, 382, 668, 360)

    self.sb_jcvc_labellll_01.setGeometry(10, 25, 650, 20)
    self.sb_jcvc_labellll_02.setGeometry(10, 53, 650, 20)
    self.sb_jcvc_labellll_03.setGeometry(10, 81, 650, 20)
    self.sb_jcvc_labellll_04.setGeometry(10, 109, 650, 20)
    self.sb_jcvc_labellll_05.setGeometry(10, 137, 650, 20)
    self.sb_jcvc_labellll_06.setGeometry(10, 165, 650, 20)
    self.sb_jcvc_labellll_07.setGeometry(10, 193, 650, 20)
    self.sb_jcvc_labellll_08.setGeometry(10, 221, 650, 20)
    self.sb_jcvc_labellll_09.setGeometry(10, 249, 650, 20)
    self.sb_jcvc_labellll_10.setGeometry(10, 277, 650, 20)
    self.sb_jcvc_labellll_11.setGeometry(10, 305, 650, 20)
    self.sb_jcvc_labellll_12.setGeometry(10, 333, 650, 20)

    self.sb_jcvc_lineEdit_01.setGeometry(92, 25, 45, 20)
    self.sb_jcvc_lineEdit_02.setGeometry(92, 53, 45, 20)
    self.sb_jcvc_lineEdit_03.setGeometry(92, 81, 105, 20)
    self.sb_jcvc_lineEdit_04.setGeometry(92, 109, 45, 20)
    self.sb_jcvc_lineEdit_05.setGeometry(153, 109, 45, 20)
    self.sb_jcvc_lineEdit_06.setGeometry(213, 109, 45, 20)
    self.sb_jcvc_lineEdit_07.setGeometry(274, 109, 45, 20)
    self.sb_jcvc_lineEdit_08.setGeometry(335, 109, 45, 20)
    self.sb_jcvc_lineEdit_09.setGeometry(396, 109, 45, 20)
    self.sb_jcvc_lineEdit_10.setGeometry(457, 109, 45, 20)
    self.sb_jcvc_lineEdit_11.setGeometry(520, 109, 45, 20)
    self.sb_jcvc_lineEdit_12.setGeometry(580, 109, 45, 20)
    self.sb_jcvc_lineEdit_13.setGeometry(92, 137, 45, 20)
    self.sb_jcvc_lineEdit_14.setGeometry(153, 137, 45, 20)
    self.sb_jcvc_lineEdit_15.setGeometry(213, 137, 45, 20)
    self.sb_jcvc_lineEdit_16.setGeometry(274, 137, 45, 20)
    self.sb_jcvc_lineEdit_17.setGeometry(335, 137, 45, 20)
    self.sb_jcvc_lineEdit_18.setGeometry(396, 137, 45, 20)
    self.sb_jcvc_lineEdit_19.setGeometry(457, 137, 45, 20)
    self.sb_jcvc_lineEdit_20.setGeometry(520, 137, 45, 20)
    self.sb_jcvc_lineEdit_21.setGeometry(92, 165, 105, 20)
    self.sb_jcvc_lineEdit_22.setGeometry(213, 165, 105, 20)
    self.sb_jcvc_lineEdit_23.setGeometry(335, 165, 105, 20)
    self.sb_jcvc_lineEdit_24.setGeometry(457, 165, 105, 20)
    self.sb_jcvc_lineEdit_25.setGeometry(92, 193, 45, 20)
    self.sb_jcvc_lineEdit_26.setGeometry(153, 193, 45, 20)
    self.sb_jcvc_lineEdit_27.setGeometry(213, 193, 45, 20)
    self.sb_jcvc_lineEdit_28.setGeometry(274, 193, 45, 20)
    self.sb_jcvc_lineEdit_29.setGeometry(92, 221, 105, 20)
    self.sb_jcvc_lineEdit_30.setGeometry(213, 221, 105, 20)
    self.sb_jcvc_lineEdit_31.setGeometry(335, 221, 105, 20)
    self.sb_jcvc_lineEdit_32.setGeometry(457, 221, 105, 20)
    self.sb_jcvc_lineEdit_33.setGeometry(92, 249, 45, 20)
    self.sb_jcvc_lineEdit_34.setGeometry(153, 249, 45, 20)
    self.sb_jcvc_lineEdit_35.setGeometry(213, 249, 45, 20)
    self.sb_jcvc_lineEdit_36.setGeometry(274, 249, 45, 20)
    self.sb_jcvc_lineEdit_37.setGeometry(92, 277, 45, 20)
    self.sb_jcvc_lineEdit_38.setGeometry(153, 277, 45, 20)
    self.sb_jcvc_lineEdit_39.setGeometry(213, 277, 45, 20)
    self.sb_jcvc_lineEdit_40.setGeometry(274, 277, 45, 20)
    self.sb_jcvc_lineEdit_41.setGeometry(92, 305, 45, 20)
    self.sb_jcvc_lineEdit_42.setGeometry(153, 305, 45, 20)
    self.sb_jcvc_lineEdit_43.setGeometry(213, 305, 45, 20)
    self.sb_jcvc_lineEdit_44.setGeometry(274, 305, 45, 20)
    self.sb_jcvc_lineEdit_45.setGeometry(92, 333, 45, 20)

    self.sb_jcvc_pushButton_01.setGeometry(450, 25, 100, 25)
    self.sb_jcvc_pushButton_02.setGeometry(560, 25, 100, 25)
    self.sb_jcvc_pushButton_03.setGeometry(560, 328, 100, 25)

    self.sb_jcvj_labellll_01.setGeometry(10, 25, 650, 20)
    self.sb_jcvj_labellll_02.setGeometry(10, 53, 650, 20)
    self.sb_jcvj_labellll_03.setGeometry(10, 81, 650, 20)
    self.sb_jcvj_labellll_04.setGeometry(10, 109, 650, 20)
    self.sb_jcvj_labellll_05.setGeometry(10, 137, 650, 20)
    self.sb_jcvj_labellll_06.setGeometry(10, 165, 650, 20)
    self.sb_jcvj_labellll_07.setGeometry(10, 193, 650, 20)
    self.sb_jcvj_labellll_08.setGeometry(10, 221, 650, 20)
    self.sb_jcvj_labellll_09.setGeometry(10, 249, 650, 20)
    self.sb_jcvj_labellll_10.setGeometry(10, 277, 650, 20)
    self.sb_jcvj_labellll_11.setGeometry(10, 305, 650, 20)
    self.sb_jcvj_labellll_12.setGeometry(10, 333, 650, 20)

    self.sb_jcvj_lineEdit_01.setGeometry(92, 25, 45, 20)
    self.sb_jcvj_lineEdit_02.setGeometry(92, 53, 45, 20)
    self.sb_jcvj_lineEdit_03.setGeometry(92, 81, 105, 20)
    self.sb_jcvj_lineEdit_04.setGeometry(92, 109, 45, 20)
    self.sb_jcvj_lineEdit_05.setGeometry(92, 137, 45, 20)
    self.sb_jcvj_lineEdit_06.setGeometry(92, 165, 105, 20)
    self.sb_jcvj_lineEdit_07.setGeometry(92, 193, 45, 20)
    self.sb_jcvj_lineEdit_08.setGeometry(92, 221, 105, 20)
    self.sb_jcvj_lineEdit_09.setGeometry(92, 249, 45, 20)
    self.sb_jcvj_lineEdit_10.setGeometry(92, 277, 45, 20)
    self.sb_jcvj_lineEdit_11.setGeometry(92, 305, 45, 20)
    self.sb_jcvj_lineEdit_12.setGeometry(92, 333, 45, 20)

    self.sb_jcvj_pushButton_01.setGeometry(450, 25, 100, 25)
    self.sb_jcvj_pushButton_02.setGeometry(560, 25, 100, 25)

    self.cb_jjvc_labellll_01.setGeometry(10, 25, 650, 20)
    self.cb_jjvc_labellll_02.setGeometry(10, 53, 650, 20)
    self.cb_jjvc_labellll_03.setGeometry(10, 81, 650, 20)
    self.cb_jjvc_labellll_04.setGeometry(10, 109, 650, 20)
    self.cb_jjvc_labellll_05.setGeometry(10, 137, 650, 20)
    self.cb_jjvc_labellll_06.setGeometry(10, 165, 650, 20)
    self.cb_jjvc_labellll_07.setGeometry(10, 193, 650, 20)
    self.cb_jjvc_labellll_08.setGeometry(10, 221, 650, 20)
    self.cb_jjvc_labellll_09.setGeometry(10, 249, 650, 20)
    self.cb_jjvc_labellll_10.setGeometry(10, 277, 650, 20)
    self.cb_jjvc_labellll_11.setGeometry(10, 305, 650, 20)
    self.cb_jjvc_labellll_12.setGeometry(10, 333, 650, 20)

    self.cb_jjvc_lineEdit_01.setGeometry(92, 25, 45, 20)
    self.cb_jjvc_lineEdit_02.setGeometry(92, 53, 45, 20)
    self.cb_jjvc_lineEdit_03.setGeometry(92, 81, 105, 20)
    self.cb_jjvc_lineEdit_04.setGeometry(92, 109, 45, 20)
    self.cb_jjvc_lineEdit_05.setGeometry(153, 109, 45, 20)
    self.cb_jjvc_lineEdit_06.setGeometry(213, 109, 45, 20)
    self.cb_jjvc_lineEdit_07.setGeometry(274, 109, 45, 20)
    self.cb_jjvc_lineEdit_08.setGeometry(335, 109, 45, 20)
    self.cb_jjvc_lineEdit_09.setGeometry(396, 109, 45, 20)
    self.cb_jjvc_lineEdit_10.setGeometry(457, 109, 45, 20)
    self.cb_jjvc_lineEdit_11.setGeometry(520, 109, 45, 20)
    self.cb_jjvc_lineEdit_12.setGeometry(580, 109, 45, 20)
    self.cb_jjvc_lineEdit_13.setGeometry(92, 137, 45, 20)
    self.cb_jjvc_lineEdit_14.setGeometry(153, 137, 45, 20)
    self.cb_jjvc_lineEdit_15.setGeometry(213, 137, 45, 20)
    self.cb_jjvc_lineEdit_16.setGeometry(274, 137, 45, 20)
    self.cb_jjvc_lineEdit_17.setGeometry(335, 137, 45, 20)
    self.cb_jjvc_lineEdit_18.setGeometry(396, 137, 45, 20)
    self.cb_jjvc_lineEdit_19.setGeometry(457, 137, 45, 20)
    self.cb_jjvc_lineEdit_20.setGeometry(520, 137, 45, 20)
    self.cb_jjvc_lineEdit_21.setGeometry(92, 165, 105, 20)
    self.cb_jjvc_lineEdit_22.setGeometry(213, 165, 105, 20)
    self.cb_jjvc_lineEdit_23.setGeometry(335, 165, 105, 20)
    self.cb_jjvc_lineEdit_24.setGeometry(457, 165, 105, 20)
    self.cb_jjvc_lineEdit_25.setGeometry(92, 193, 45, 20)
    self.cb_jjvc_lineEdit_26.setGeometry(153, 193, 45, 20)
    self.cb_jjvc_lineEdit_27.setGeometry(213, 193, 45, 20)
    self.cb_jjvc_lineEdit_28.setGeometry(274, 193, 45, 20)
    self.cb_jjvc_lineEdit_29.setGeometry(92, 221, 105, 20)
    self.cb_jjvc_lineEdit_30.setGeometry(213, 221, 105, 20)
    self.cb_jjvc_lineEdit_31.setGeometry(335, 221, 105, 20)
    self.cb_jjvc_lineEdit_32.setGeometry(457, 221, 105, 20)
    self.cb_jjvc_lineEdit_33.setGeometry(92, 249, 45, 20)
    self.cb_jjvc_lineEdit_34.setGeometry(153, 249, 45, 20)
    self.cb_jjvc_lineEdit_35.setGeometry(213, 249, 45, 20)
    self.cb_jjvc_lineEdit_36.setGeometry(274, 249, 45, 20)
    self.cb_jjvc_lineEdit_37.setGeometry(92, 277, 45, 20)
    self.cb_jjvc_lineEdit_38.setGeometry(153, 277, 45, 20)
    self.cb_jjvc_lineEdit_39.setGeometry(213, 277, 45, 20)
    self.cb_jjvc_lineEdit_40.setGeometry(274, 277, 45, 20)
    self.cb_jjvc_lineEdit_41.setGeometry(92, 305, 45, 20)
    self.cb_jjvc_lineEdit_42.setGeometry(153, 305, 45, 20)
    self.cb_jjvc_lineEdit_43.setGeometry(213, 305, 45, 20)
    self.cb_jjvc_lineEdit_44.setGeometry(274, 305, 45, 20)
    self.cb_jjvc_lineEdit_45.setGeometry(92, 333, 45, 20)

    self.cb_jjvc_pushButton_01.setGeometry(450, 25, 100, 25)
    self.cb_jjvc_pushButton_02.setGeometry(560, 25, 100, 25)
    self.cb_jjvc_pushButton_03.setGeometry(560, 328, 100, 25)

    self.cb_jjvj_labellll_01.setGeometry(10, 25, 650, 20)
    self.cb_jjvj_labellll_02.setGeometry(10, 53, 650, 20)
    self.cb_jjvj_labellll_03.setGeometry(10, 81, 650, 20)
    self.cb_jjvj_labellll_04.setGeometry(10, 109, 650, 20)
    self.cb_jjvj_labellll_05.setGeometry(10, 137, 650, 20)
    self.cb_jjvj_labellll_06.setGeometry(10, 165, 650, 20)
    self.cb_jjvj_labellll_07.setGeometry(10, 193, 650, 20)
    self.cb_jjvj_labellll_08.setGeometry(10, 221, 650, 20)
    self.cb_jjvj_labellll_09.setGeometry(10, 249, 650, 20)
    self.cb_jjvj_labellll_10.setGeometry(10, 277, 650, 20)
    self.cb_jjvj_labellll_11.setGeometry(10, 305, 650, 20)
    self.cb_jjvj_labellll_12.setGeometry(10, 333, 650, 20)

    self.cb_jjvj_lineEdit_01.setGeometry(92, 25, 45, 20)
    self.cb_jjvj_lineEdit_02.setGeometry(92, 53, 45, 20)
    self.cb_jjvj_lineEdit_03.setGeometry(92, 81, 105, 20)
    self.cb_jjvj_lineEdit_04.setGeometry(92, 109, 45, 20)
    self.cb_jjvj_lineEdit_05.setGeometry(92, 137, 45, 20)
    self.cb_jjvj_lineEdit_06.setGeometry(92, 165, 105, 20)
    self.cb_jjvj_lineEdit_07.setGeometry(92, 193, 45, 20)
    self.cb_jjvj_lineEdit_08.setGeometry(92, 221, 105, 20)
    self.cb_jjvj_lineEdit_09.setGeometry(92, 249, 45, 20)
    self.cb_jjvj_lineEdit_10.setGeometry(92, 277, 45, 20)
    self.cb_jjvj_lineEdit_11.setGeometry(92, 305, 45, 20)
    self.cb_jjvj_lineEdit_12.setGeometry(92, 333, 45, 20)

    self.cb_jjvj_pushButton_01.setGeometry(450, 25, 100, 25)
    self.cb_jjvj_pushButton_02.setGeometry(560, 25, 100, 25)

    self.sj_groupBox_01.setGeometry(5, 10, 1341, 65)
    self.sj_groupBox_02.setGeometry(5, 95, 1341, 90)
    self.sj_groupBox_03.setGeometry(5, 205, 1341, 65)
    self.sj_groupBox_04.setGeometry(5, 290, 1341, 65)
    self.sj_groupBox_05.setGeometry(5, 375, 1341, 90)
    self.sj_groupBox_06.setGeometry(5, 485, 1341, 90)
    self.sj_textEdit.setGeometry(5, 595, 1341, 148)

    self.sj_main_checkBox_01.setGeometry(10, 25, 100, 30)
    self.sj_main_checkBox_02.setGeometry(120, 25, 100, 30)
    self.sj_main_checkBox_03.setGeometry(230, 25, 100, 30)
    self.sj_main_checkBox_04.setGeometry(340, 25, 100, 30)

    self.sj_sacc_labellll_01.setGeometry(10, 30, 100, 20)
    self.sj_sacc_lineEdit_01.setGeometry(115, 30, 100, 20)
    self.sj_sacc_labellll_02.setGeometry(225, 30, 50, 20)
    self.sj_sacc_lineEdit_02.setGeometry(285, 30, 100, 20)
    self.sj_sacc_labellll_03.setGeometry(395, 30, 80, 20)
    self.sj_sacc_lineEdit_03.setGeometry(485, 30, 100, 20)
    self.sj_sacc_labellll_04.setGeometry(595, 30, 70, 20)
    self.sj_sacc_lineEdit_04.setGeometry(675, 30, 100, 20)
    self.sj_sacc_labellll_05.setGeometry(10, 60, 100, 20)
    self.sj_sacc_lineEdit_05.setGeometry(115, 60, 100, 20)
    self.sj_sacc_labellll_06.setGeometry(225, 60, 50, 20)
    self.sj_sacc_lineEdit_06.setGeometry(285, 60, 100, 20)
    self.sj_sacc_labellll_07.setGeometry(395, 60, 80, 20)
    self.sj_sacc_lineEdit_07.setGeometry(485, 60, 100, 20)
    self.sj_sacc_labellll_08.setGeometry(595, 60, 70, 20)
    self.sj_sacc_lineEdit_08.setGeometry(675, 60, 100, 20)

    self.sj_stock_checkBox_01.setGeometry(10, 25, 100, 30)
    self.sj_stock_checkBox_02.setGeometry(120, 25, 100, 30)
    self.sj_stock_labellll_01.setGeometry(10, 60, 115, 20)
    self.sj_stock_lineEdit_01.setGeometry(135, 60, 50, 20)
    self.sj_stock_labellll_02.setGeometry(195, 60, 50, 20)
    self.sj_stock_lineEdit_02.setGeometry(255, 60, 50, 20)
    self.sj_stock_labellll_03.setGeometry(315, 60, 70, 20)
    self.sj_stock_lineEdit_03.setGeometry(395, 60, 50, 20)
    self.sj_stock_labellll_04.setGeometry(455, 60, 70, 20)
    self.sj_stock_lineEdit_04.setGeometry(535, 60, 50, 20)
    self.sj_stock_labellll_05.setGeometry(595, 60, 90, 20)
    self.sj_stock_lineEdit_05.setGeometry(695, 60, 50, 20)
    self.sj_stock_labellll_06.setGeometry(755, 60, 60, 20)
    self.sj_stock_lineEdit_06.setGeometry(825, 60, 50, 20)
    self.sj_stock_labellll_07.setGeometry(885, 60, 60, 20)
    self.sj_stock_lineEdit_07.setGeometry(955, 60, 50, 20)
    self.sj_stock_labellll_08.setGeometry(1015, 60, 60, 20)
    self.sj_stock_lineEdit_08.setGeometry(1085, 60, 50, 20)

    self.sj_cacc_labellll_01.setGeometry(10, 30, 65, 20)
    self.sj_cacc_lineEdit_01.setGeometry(85, 30, 400, 20)
    self.sj_cacc_labellll_02.setGeometry(495, 30, 65, 20)
    self.sj_cacc_lineEdit_02.setGeometry(570, 30, 400, 20)

    self.sj_coin_checkBox_01.setGeometry(10, 25, 100, 30)
    self.sj_coin_checkBox_02.setGeometry(120, 25, 100, 30)
    self.sj_coin_labellll_01.setGeometry(10, 60, 115, 20)
    self.sj_coin_lineEdit_01.setGeometry(135, 60, 50, 20)
    self.sj_coin_labellll_02.setGeometry(195, 60, 50, 20)
    self.sj_coin_lineEdit_02.setGeometry(255, 60, 50, 20)
    self.sj_coin_labellll_03.setGeometry(315, 60, 70, 20)
    self.sj_coin_lineEdit_03.setGeometry(395, 60, 50, 20)
    self.sj_coin_labellll_04.setGeometry(455, 60, 70, 20)
    self.sj_coin_lineEdit_04.setGeometry(535, 60, 50, 20)
    self.sj_coin_labellll_05.setGeometry(595, 60, 90, 20)
    self.sj_coin_lineEdit_05.setGeometry(695, 60, 50, 20)
    self.sj_coin_labellll_06.setGeometry(755, 60, 60, 20)
    self.sj_coin_lineEdit_06.setGeometry(825, 60, 50, 20)
    self.sj_coin_labellll_07.setGeometry(885, 60, 60, 20)
    self.sj_coin_lineEdit_07.setGeometry(955, 60, 50, 20)
    self.sj_coin_labellll_08.setGeometry(1015, 60, 60, 20)
    self.sj_coin_lineEdit_08.setGeometry(1085, 60, 50, 20)

    self.sj_tele_labellll_01.setGeometry(10, 30, 65, 20)
    self.sj_tele_lineEdit_01.setGeometry(85, 30, 400, 20)
    self.sj_tele_labellll_02.setGeometry(495, 30, 65, 20)
    self.sj_tele_lineEdit_02.setGeometry(570, 30, 400, 20)

    self.sj_load_pushButton_01.setGeometry(1180, 30, 70, 22)
    self.sj_load_pushButton_02.setGeometry(1180, 30, 70, 22)
    self.sj_load_pushButton_03.setGeometry(1180, 30, 70, 22)
    self.sj_load_pushButton_04.setGeometry(1180, 30, 70, 22)
    self.sj_load_pushButton_05.setGeometry(1180, 30, 70, 22)
    self.sj_load_pushButton_06.setGeometry(1180, 30, 70, 22)

    self.sj_save_pushButton_01.setGeometry(1260, 30, 70, 22)
    self.sj_save_pushButton_02.setGeometry(1260, 30, 70, 22)
    self.sj_save_pushButton_03.setGeometry(1260, 30, 70, 22)
    self.sj_save_pushButton_04.setGeometry(1260, 30, 70, 22)
    self.sj_save_pushButton_05.setGeometry(1260, 30, 70, 22)
    self.sj_save_pushButton_06.setGeometry(1260, 30, 70, 22)

    self.st_textEdit.setGeometry(5, 5, 668, 367)
    self.ct_textEdit.setGeometry(678, 5, 668, 367)
    self.sc_textEdit.setGeometry(5, 377, 668, 367)
    self.cc_textEdit.setGeometry(678, 377, 668, 367)
