import sys, os, sqlite3, csv, socket, shutil

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTableView, QPushButton, QLineEdit, QLabel, QStatusBar,
    QFileDialog, QMessageBox, QFormLayout, QSpinBox, QProgressBar,
    QSplashScreen, QGraphicsOpacityEffect
)
from PyQt6.QtGui import QAction, QMovie
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QPropertyAnimation
from PyQt6.QtSql import QSqlDatabase, QSqlTableModel, QSqlQuery

class PortScanner(QThread):
    progress = pyqtSignal(int, bool)
    finished = pyqtSignal()

    def __init__(self, host, ports):
        super().__init__()
        self.host, self.ports = host, ports

    def run(self):
        for p in self.ports:
            s = socket.socket()
            s.settimeout(0.3)
            ok = (s.connect_ex((self.host, p)) == 0)
            s.close()
            self.progress.emit(p, ok)
        self.finished.emit()

class DatabaseManager:
    def __init__(self, path="people.db"):
        self.path = path

    def init_db(self):
        if not os.path.exists(self.path):
            conn = sqlite3.connect(self.path)
            conn.execute("""
                CREATE TABLE users (
                    id   INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT    NOT NULL,
                    age  INTEGER NOT NULL
                )
            """)
            conn.commit()
            conn.close()

        self.db = QSqlDatabase.addDatabase("QSQLITE")
        self.db.setDatabaseName(self.path)
        if not self.db.open():
            raise RuntimeError(self.db.lastError().text())

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CRUD + Сетевые инструменты 🌀")
        self.resize(900, 600)

        self.dbm = DatabaseManager()
        self.dbm.init_db()

        self.model = QSqlTableModel(self, self.dbm.db)
        self.model.setTable("users")
        self.model.setEditStrategy(QSqlTableModel.EditStrategy.OnManualSubmit)
        self.model.select()
        for i, hdr in enumerate(("ID", "Имя", "Возраст")):
            self.model.setHeaderData(i, Qt.Orientation.Horizontal, hdr)

        self._build_ui()
        self.animate_table()

    def _build_ui(self):
        m = self.menuBar().addMenu("Файл")
        for text, method in [
            ("Экспорт CSV", self.export_csv),
            ("Импорт CSV", self.import_csv),
            ("Резервная копия БД", self.backup_db)
        ]:
            act = QAction(text, self, triggered=method)
            m.addAction(act)
            self.addToolBar("T").addAction(act)

        w = QWidget()
        self.setCentralWidget(w)
        lay = QVBoxLayout(w)

        h = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Поиск по имени…")
        h.addWidget(self.search)
        for txt, fn in [("🔍", self.apply_filter), ("✖", self.clear_filter)]:
            btn = QPushButton(txt)
            btn.clicked.connect(fn)
            h.addWidget(btn)
        lay.addLayout(h)

        self.tv = QTableView()
        self.tv.setModel(self.model)
        self.tv.setSortingEnabled(True)
        self.tv.doubleClicked.connect(self.on_row_double)
        self.tv.horizontalHeader().setStretchLastSection(True)
        self.tv.resizeColumnsToContents()
        lay.addWidget(self.tv)

        frm = QFormLayout()
        self.name = QLineEdit()
        self.age = QSpinBox()
        self.age.setRange(0, 200)
        frm.addRow("Имя:", self.name)
        frm.addRow("Возраст:", self.age)
        lay.addLayout(frm)

        h2 = QHBoxLayout()
        for txt, fn in [
            ("➕ Добавить", self.add_rec),
            ("📝 Обновить", self.update_rec),
            ("🗑️ Удалить", self.delete_rec)
        ]:
            btn = QPushButton(txt)
            btn.clicked.connect(fn)
            h2.addWidget(btn)
        lay.addLayout(h2)

        lay.addWidget(QLabel("Сканер портов:"))
        nf = QFormLayout()
        self.host = QLineEdit(socket.gethostname())
        self.ports = QLineEdit("22,80-85,443")
        scan_btn = QPushButton("Сканировать порты")
        scan_btn.clicked.connect(self.scan_ports)
        nf.addRow("Хост:", self.host)
        nf.addRow("Порты:", self.ports)
        nf.addRow(scan_btn)
        lay.addLayout(nf)

        self.spinner_lbl = QLabel()
        self.spinner = QMovie("spinner.gif")
        self.spinner_lbl.setMovie(self.spinner)
        self.spinner_lbl.setVisible(False)
        lay.addWidget(self.spinner_lbl)

        self.pb = QProgressBar()
        self.pb.setVisible(False)
        lay.addWidget(self.pb)

        self.status = QStatusBar()
        self.setStatusBar(self.status)

    def animate_table(self):
        eff = QGraphicsOpacityEffect(self.tv)
        self.tv.setGraphicsEffect(eff)
        anim = QPropertyAnimation(eff, b"opacity", self)
        anim.setStartValue(0.2)
        anim.setEndValue(1.0)
        anim.setDuration(600)
        anim.start()

    def apply_filter(self):
        t = self.search.text().strip()
        self.model.setFilter(f"name LIKE '%{t}%'" if t else "")
        self.model.select()
        self.animate_table()

    def clear_filter(self):
        self.search.clear()
        self.apply_filter()

    def add_rec(self):
        n, a = self.name.text().strip(), self.age.value()
        if not n:
            QMessageBox.warning(self, "Ошибка", "Введите имя")
            return
        q = QSqlQuery()
        q.prepare("INSERT INTO users(name, age) VALUES (?, ?)")
        q.addBindValue(n)
        q.addBindValue(a)
        if not q.exec():
            QMessageBox.critical(self, "Ошибка БД", q.lastError().text())
        else:
            self.model.select()
            self.animate_table()
            self._status_anim("Добавлено ✔", success=True)
            self.name.clear()
            self.age.setValue(0)

    def on_row_double(self, idx):
        r = self.model.record(idx.row())
        self.cur_id = r.value("id")
        self.name.setText(r.value("name"))
        self.age.setValue(r.value("age"))

    def update_rec(self):
        if not hasattr(self, "cur_id"):
            QMessageBox.warning(self, "Ошибка", "Выберите запись")
            return
        n, a = self.name.text().strip(), self.age.value()
        if not n:
            QMessageBox.warning(self, "Ошибка", "Введите имя")
            return
        q = QSqlQuery()
        q.prepare("UPDATE users SET name=?, age=? WHERE id=?")
        q.addBindValue(n)
        q.addBindValue(a)
        q.addBindValue(self.cur_id)
        if not q.exec():
            QMessageBox.critical(self, "Ошибка БД", q.lastError().text())
        else:
            self.model.select()
            self.animate_table()
            self._status_anim("Обновлено ✔", success=True)
            self.name.clear()
            self.age.setValue(0)
            del self.cur_id