#!/usr/bin/env python3
# coding: utf-8

from sys import argv, exit
from subprocess import Popen, PIPE
from os import path, listdir, sep, name
from datetime import date, datetime, time, timedelta
from PyQt5 import QtWidgets, QtGui, QtCore, QtSql

class MyWindows(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.zandronum_path_string = QtWidgets.QLineEdit()
        if (name == 'posix'):
            self.zandronum_path_string.setText(Popen(['which zandronum'], stdout=PIPE, shell=True).communicate()[0].decode())
        #
        self.cbx_select_iwad = QtWidgets.QComboBox(self)
        self.cbx_pk3s_menu = QtWidgets.QMenu(self)
        #
        self.chbx_networking_game = QtWidgets.QCheckBox()
        self.edit_server = QtWidgets.QLineEdit('ice2heart.com')
        self.edit_server_port = QtWidgets.QLineEdit('10666')
        #
        self.info = QtWidgets.QTextEdit()
        # Список pk3-файлов
        self.pk3s = []
        #
        self.db = self.dbInit()
        self.serverModel = QtSql.QSqlTableModel(self, self.db)
        #       
        self.initUI()
        self.cbx_populate()
        # self.saveOptionsload()
        self.makeInfo()
    
    def initUI(self):
        central_widget = QtWidgets.QWidget(self)
        self.setCentralWidget(central_widget)
        central_widget_grid_layout = QtWidgets.QGridLayout()
        central_widget.setLayout(central_widget_grid_layout)
        #
        file_group = QtWidgets.QGroupBox()
        file_group.setFixedSize(380, 150)
        file_group_layout = QtWidgets.QGridLayout()
        #
        self.zandronum_path_string.setFixedHeight(25)
        btn_select_zandronum_path = QtWidgets.QPushButton("..")
        btn_select_zandronum_path.setFixedSize(25, 25)
        btn_select_zandronum_path.setToolTip("Указать путь к бинарнику Zandronum")
        btn_select_zandronum_path.pressed.connect(lambda: self.openZandronumBinPath())
        # Выбор wad'ов
        self.cbx_select_iwad.currentTextChanged.connect(lambda: self.fileSelection("wad"))
        self.cbx_select_iwad.setFixedSize(225, 25)
        # Выбор pk3-файлов
        cbx_select_pk3 = QtWidgets.QToolButton(self)
        cbx_select_pk3.setMenu(self.cbx_pk3s_menu)
        cbx_select_pk3.setPopupMode(QtWidgets.QToolButton.InstantPopup)
        cbx_select_pk3.triggered.connect(lambda cbx_select_pk3: self.fileSelection("pk3", cbx_select_pk3))
        cbx_select_pk3.setFixedSize(225, 25)
        #
        file_group_layout.addWidget(QtWidgets.QLabel("Путь к zandronum:"), 0, 0)
        file_group_layout.addWidget(self.zandronum_path_string, 1, 0, 1, 2)
        file_group_layout.addWidget(btn_select_zandronum_path, 1, 2)
        file_group_layout.addWidget(QtWidgets.QLabel("iwad-файл:"), 2, 0)
        file_group_layout.addWidget(self.cbx_select_iwad, 2, 1)
        file_group_layout.addWidget(QtWidgets.QLabel("pk3-файл(ы):"), 3, 0)
        file_group_layout.addWidget(cbx_select_pk3, 3, 1)
        # Сеть
        network_group = QtWidgets.QGroupBox()
        network_group_layout = QtWidgets.QGridLayout()
        #
        self.chbx_networking_game.setText("Сетевая игра")
        self.chbx_networking_game.setChecked(True)
        self.chbx_networking_game.stateChanged.connect(lambda: self.networkingGame())
        #
        self.edit_server.setFixedSize(220, 25)
        btn_add_server = QtWidgets.QPushButton()
        btn_add_server.setText("+")
        btn_add_server.setToolTip("Сохранить сервер")
        btn_add_server.setFixedSize(25, 25)
        btn_add_server.pressed.connect(lambda: self.db_queryServer())
        # Таблица с сохранёнными серверами
        self.serverModel.setEditStrategy(QtSql.QSqlTableModel.OnFieldChange)
        self.serverModel.setTable('servers')
        self.serverModel.select()
        # self.serverModel.removeColumn(0)
        # self.serverModel.setHeaderData(0, QtCore.Qt.Horizontal, "ID")
        self.serverModel.setHeaderData(1, QtCore.Qt.Horizontal, "Сервер")
        self.serverModel.setHeaderData(2, QtCore.Qt.Horizontal, "Порт")
        tbl_servers = QtWidgets.QTableView()
        tbl_servers.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        tbl_servers.verticalHeader().hide()
        tbl_servers.setSelectionMode(QtWidgets.QTableView.SingleSelection)
        tbl_servers.setSelectionBehavior(QtWidgets.QTableView.SelectRows)
        tbl_servers.setEditTriggers(QtWidgets.QTableView.NoEditTriggers)
        tbl_servers.setAlternatingRowColors(True)
        tbl_servers.setModel(self.serverModel)
        tbl_servers.setColumnHidden(0, True)
        tbl_servers.doubleClicked.connect(lambda: self.db_getSaveServer(tbl_servers.currentIndex())) # Двойной клик по таблице (выбор сохраненного сервера)
        QtWidgets.QShortcut(QtCore.Qt.Key_Delete, tbl_servers, activated=lambda: self.db_queryServer(1, tbl_servers.currentIndex())) # Удаление записи из БД по Delete
        #
        network_group_layout.addWidget(self.chbx_networking_game, 0, 0)
        network_group_layout.addWidget(QtWidgets.QLabel("Сервер"), 1, 0)
        network_group_layout.addWidget(self.edit_server, 2, 0)
        network_group_layout.addWidget(QtWidgets.QLabel("Порт"), 1, 1)
        network_group_layout.addWidget(self.edit_server_port, 2, 1)
        network_group_layout.addWidget(btn_add_server, 2, 2)
        #
        network_group_layout.addWidget(QtWidgets.QLabel("Сохраненные сервера"), 3, 0)
        network_group_layout.addWidget(tbl_servers, 4, 0, 1, 3)
        #
        rungame_group = QtWidgets.QGroupBox()
        rungame_group_layout = QtWidgets.QGridLayout()
        # Информация
        info_group = QtWidgets.QGroupBox()
        info_group_layout = QtWidgets.QGridLayout()
        #
        info_group_layout.addWidget(self.info)
        info_group.setLayout(info_group_layout)
        # Кнопка запуска
        btn_rungame = QtWidgets.QPushButton()
        btn_rungame.setText("Запустить игру!")
        btn_rungame.pressed.connect(lambda: self.runGame())
        rungame_group_layout.addWidget(btn_rungame)
        #
        file_group.setLayout(file_group_layout)
        network_group.setLayout(network_group_layout)
        rungame_group.setLayout(rungame_group_layout)
        #
        central_widget_grid_layout.addWidget(file_group, 0, 0)
        central_widget_grid_layout.addWidget(network_group, 1, 0)
        central_widget_grid_layout.addWidget(info_group, 2, 0)
        central_widget_grid_layout.addWidget(rungame_group, 3, 0)
        #
        self.setWindowTitle("ZLauncher - Zandronum launcher ver. 0.1")
        self.setFixedSize(400, 600)
        self.setCenter()
        self.show()

    # Ручками указать путь к Zandronum
    def openZandronumBinPath(self):
        filename = QtWidgets.QFileDialog().getOpenFileName(self, 'Найти бинарь Zandronum\'а', path.dirname(path.realpath(__file__)))[0]
        if ("zandronum" in filename.lower()):
            self.zandronum_path_string.setText(filename)
        elif (len(filename) < 1):
            pass
        else:
            self.message("Не верное имя файла!\n Укажите путь к \"zandorum\".")
    
    # Центрирование окна
    def setCenter(self):
        qr = self.frameGeometry()
        cp = QtWidgets.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
    
    # Заполнение ComboBox'ов файлами
    def cbx_populate(self):
        try:
            for i in map(path.splitext, listdir(path.dirname(path.realpath(__file__))+sep+"wads")):
                if (i[1].upper() == ".WAD"):
                    self.cbx_select_iwad.addItem(i[0]+i[1])
                elif (i[1].upper() == ".PK3"):
                    action = self.cbx_pk3s_menu.addAction(i[0]+i[1])
                    action.setCheckable(True)
            self.cbx_select_iwad.setCurrentIndex(0)
        except:
            self.message("Отсутствует каталог с wad-файлами!")
    
    # Формирование списка файлов
    def fileSelection(self, file, selected = ""):
        if file != "wad" and selected != "":
            if (selected.isChecked()):
                self.pk3s.append(selected.text())
            else:
                self.pk3s.remove(selected.text())
        self.makeInfo()
    
    # Контроль сетевой игры
    def networkingGame(self):
        if self.chbx_networking_game.isChecked():
            self.edit_server.setEnabled(True)
            self.edit_server_port.setEnabled(True)
        else:
            self.edit_server.setDisabled(True)
            self.edit_server_port.setDisabled(True)
        self.makeInfo()
    
    # Выбор сохраненного сервера
    def db_getSaveServer(self, currentIndex):
        self.edit_server.setText(str(self.serverModel.record(currentIndex.row()).value(1)))
        self.edit_server_port.setText(str(self.serverModel.record(currentIndex.row()).value(2)))
    
    # Сохранить сервер в БД или удалить из БД
    def db_queryServer(self, delete = 0, currentIndex = 0):
        query = QtSql.QSqlDatabase(self.db)
        if delete == 1:
            query.exec_("DELETE FROM `servers` WHERE `id` = "+str(self.serverModel.record(currentIndex.row()).value(0)))
            self.message("Сервер удалён.")
        else:
            query.exec_("INSERT INTO `servers`(`host`, `port`) VALUES('"+self.edit_server.text()+"', '"+self.edit_server_port.text()+"')")
            self.message("Сервер добавлен.")
        self.serverModel.select()
    
    # Инициализация БД
    def dbInit(self):
        dbfile = path.dirname(path.realpath(__file__))+sep+"zlauncher.db"
        db = QtSql.QSqlDatabase.addDatabase('QSQLITE')
        db.setDatabaseName(dbfile)
        if not db.open():
                self.message("Ошибка инициализации БД!")
                return(False)
        if (path.getsize(dbfile) <= 0):
            query = QtSql.QSqlQuery(db)
            query.exec_("CREATE TABLE `servers`(`id` INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, `host` VARCHAR(50) NOT NULL, `port` INTEGER(5) NOT NULL)")
            query.exec_("INSERT INTO `servers`(`host`, `port`) VALUES('ice2heart.com', '10666')")
            query.exec_("CREATE TABLE `options`(`id` INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, `path` VARCHAR(255), `iwad` VARCHAR(50), `pk3` VARCHAR(50), `network` BOOLEAN, `host` VARCHAR(50), `port` INTEGER(5))")
        return(db)
    
    # Информация о выбранных компонентах
    def makeInfo(self):
        if self.chbx_networking_game.isChecked():
            server = "<b>Сервер: </b>"+self.edit_server.text()+" <b> : </b>"+self.edit_server_port.text()
        else:
            server = ""
        self.info.setText("<b>iwad: </b>"+self.cbx_select_iwad.currentText()+
            "<br><b>pk3: </b>"+"<b>,</b> ".join(self.pk3s)+"<br>"+server)
    
    # Формирование параметров запуска
    def makeRunstring(self):
        if len(self.zandronum_path_string.text()) <= 0:
            self.message("На компьютере не обнаружен Zandronum!\n Укажите путь к исполняемому файлу Zandronum.")
            runstring = 0
            return(runstring)
        path_to_wads=path.dirname(path.realpath(__file__))+sep+"wads"+sep
        runstring = str(self.zandronum_path_string.text()).strip() + " "
        if (len(self.cbx_select_iwad.currentText()) > 0):
            runstring += "-iwad " + path_to_wads + self.cbx_select_iwad.currentText() + " "
        else:
            self.message("Отсутствует iwad-фалй!")
            runstring = 0
        if (len(self.pk3s) > 0):
            runstring = runstring + "-file "
            for i in self.pk3s:
                runstring += path_to_wads+i+" "
        if self.chbx_networking_game.isChecked():
            if len(self.edit_server.text()) > 1 and len(self.edit_server_port.text()) > 1:
                runstring += "+connect " + self.edit_server.text().strip() + " -port " + self.edit_server_port.text().strip()
            else:
                self.message("Укажите сервер и порт.")
                runstring = 0
        #
        if (runstring != 0):
            return(runstring)

    # Сохранение и восстановление параметров
    def saveOptionsload(self, runstring = "", save = 1):
        if (save == 1):
            import re
            print(re.split("(-iwad|-file|\+connect)", runstring))
            # rs = runstring.split(' ')
            # zp = rs.pop(0)
            # rs.pop(0)
            # iwad = rs.pop(0).split(sep)[-1]
            # rs.pop(0)
            # pk3 = []
            # server = ""
            # port = ""
            
            # # for i in (x for x in rs if x != "+connect"):
            # for i in rs:
            #     if i != "+connect":
            #         print(i)
            #     else:
            #         break

    # Запуск игры
    def runGame(self):
        runstring = self.makeRunstring()
        if (runstring != 0):
            print(runstring)
            # self.saveOptionsload(runstring)
            Popen(runstring, shell=True)
            
    # Сообщения
    def message(self, msg):
        mb = QtWidgets.QMessageBox()
        mb.question(self, "Сообщение", msg, QtWidgets.QMessageBox.Ok)
    
if __name__ == '__main__':
    app = QtWidgets.QApplication(argv)
    w = MyWindows()
    exit(app.exec_())
