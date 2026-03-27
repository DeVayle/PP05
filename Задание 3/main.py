import sys
from PyQt6.QtWidgets import (QWidget, QGridLayout, QLabel, QVBoxLayout, QHBoxLayout, QTableWidget, QHeaderView, QTableWidgetItem,
                             QMessageBox, QMainWindow, QLineEdit, QPushButton, QApplication, QComboBox, QFormLayout, QDialog)
from PyQt6.QtGui import QPixmap, QRegularExpressionValidator
from PyQt6.QtCore import Qt, pyqtSignal, QRegularExpression
from db import DBManager 

class ClickableLabel(QLabel):
    clicked = pyqtSignal(object)
    def __init__(self, part_id=None):
        super().__init__()
        self.part_id = part_id
        self.current_id = None
        self.setFixedSize(80, 80)
        self.setStyleSheet("border: 1px solid gray; background: #f9f9f9;")
        self.setScaledContents(True)
        self.is_used = False

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self)
        
class CaptchaWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.selected_source = None
        self.image_files = ["ui/1.png", "ui/2.png", "ui/3.png", "ui/4.png"] 
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)
        self.source_layout = QVBoxLayout()
        self.sources = []
        for i in range(4):
            lbl = ClickableLabel(part_id=i)
            lbl.setPixmap(QPixmap(self.image_files[i]))
            lbl.clicked.connect(self.on_source_click)
            self.sources.append(lbl)
            self.source_layout.addWidget(lbl)
            
        self.grid_layout = QGridLayout()
        self.slots = []
        for i in range(4):
            slot = ClickableLabel()
            slot.clicked.connect(self.on_slot_click)
            self.grid_layout.addWidget(slot, i // 2, i % 2)
            self.slots.append(slot)
            
        layout.addLayout(self.source_layout)
        layout.addLayout(self.grid_layout)

    def on_source_click(self, label):
        if label.is_used: return 
        for s in self.sources:
            if not s.is_used: s.setStyleSheet("border: 1px solid gray; background: white;")
        self.selected_source = label
        label.setStyleSheet("border: 3px solid blue; background: #e0e0ff;")

    def on_slot_click(self, slot):
        if self.selected_source and slot.current_id is None:
            slot.setPixmap(self.selected_source.pixmap())
            slot.current_id = self.selected_source.part_id
            self.selected_source.is_used = True
            self.selected_source = None

    def is_correct(self):
        return all(self.slots[i].current_id == i for i in range(4))
    
    def reset(self):
        self.selected_source = None
        for i in range(4):
            self.sources[i].is_used = False
            self.sources[i].setStyleSheet("border: 1px solid gray; background: white;")
            self.slots[i].setPixmap(QPixmap())
            self.slots[i].current_id = None

class UserEditDialog(QDialog):
    def __init__(self, db, user_data=None):
        super().__init__()
        self.db = db
        self.user_data = user_data
        self.init_ui()

    def init_ui(self):
        title = "Редактировать пользователя" if self.user_data else "Добавить нового пользователя"
        self.setWindowTitle(title)
        self.setMinimumWidth(400)
        layout = QFormLayout(self)

        name_re = QRegularExpression(r"^[a-zA-Zа-яА-ЯёЁ\-]+$")
        validator = QRegularExpressionValidator(name_re)

        self.username_edit = QLineEdit()
        self.password_edit = QLineEdit()
        self.f_edit = QLineEdit()
        self.i_edit = QLineEdit()
        self.o_edit = QLineEdit()

        for edit in [self.f_edit, self.i_edit, self.o_edit]:
            edit.setValidator(validator)
            edit.setMaxLength(50)

        self.role_combo = QComboBox()
        roles = self.db.get_roles()
        for r in roles:
            self.role_combo.addItem(r['name'], r['id'])

        layout.addRow("Логин*:", self.username_edit)
        layout.addRow("Пароль*:", self.password_edit)
        layout.addRow("Фамилия*:", self.f_edit)
        layout.addRow("Имя*:", self.i_edit)
        layout.addRow("Отчество:", self.o_edit)
        layout.addRow("Роль*:", self.role_combo)

        if self.user_data:
            self.username_edit.setText(self.user_data['username'])
            self.password_edit.setText(self.user_data['password'])
            self.f_edit.setText(self.user_data['f'])
            self.i_edit.setText(self.user_data['i'])
            self.o_edit.setText(self.user_data['o'] or "")
            index = self.role_combo.findText(self.user_data['role_name'])
            self.role_combo.setCurrentIndex(index)

        self.save_btn = QPushButton("Сохранить")
        self.save_btn.clicked.connect(self.save_user)
        layout.addRow(self.save_btn)

    def save_user(self):
        data = {
            "username": self.username_edit.text(),
            "password": self.password_edit.text(),
            "f": self.f_edit.text(),
            "i": self.i_edit.text(),
            "o": self.o_edit.text(),
            "role_id": self.role_combo.currentData()
        }
        
        if not all([data["username"], data["password"], data["f"], data["i"]]):
            QMessageBox.warning(self, "Ошибка", "Заполните все обязательные поля (*)")
            return

        if self.user_data:
            success, message = self.db.update_user(self.user_data['id'], **data)
        else:
            success, message = self.db.add_user(**data)

        if success:
            QMessageBox.information(self, "Успех", message)
            self.accept()
        else:
            QMessageBox.critical(self, "Ошибка", message)

class AdminWindow(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Управление - ООО 'Мебель'")
        self.setMinimumSize(900, 500)
        layout = QVBoxLayout(self)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID", "Логин", "ФИО", "Роль", "Статус", "Блокировка"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)

        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("Добавить")
        self.edit_btn = QPushButton("Изменить")
        self.unblock_btn = QPushButton("Разблокировать")
        
        self.add_btn.clicked.connect(self.open_add_dialog)
        self.edit_btn.clicked.connect(self.open_edit_dialog)
        self.unblock_btn.clicked.connect(self.handle_unblock)

        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.edit_btn)
        btn_layout.addWidget(self.unblock_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        self.load_data()

    def load_data(self):
        self.users_list = self.db.get_all_users()
        self.table.setRowCount(len(self.users_list))
        for i, u in enumerate(self.users_list):
            fio = f"{u['f']} {u['i']} {u['o'] or ''}"
            status = "ЗАБЛОКИРОВАН" if u['is_blocked'] else "Активен"
            self.table.setItem(i, 0, QTableWidgetItem(str(u['id'])))
            self.table.setItem(i, 1, QTableWidgetItem(u['username']))
            self.table.setItem(i, 2, QTableWidgetItem(fio))
            self.table.setItem(i, 3, QTableWidgetItem(u['role_name']))
            self.table.setItem(i, 4, QTableWidgetItem(status))

    def open_add_dialog(self):
        if UserEditDialog(self.db).exec():
            self.load_data()

    def open_edit_dialog(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Внимание", "Выберите пользователя!")
            return
        
        user_data = self.users_list[row]
        if UserEditDialog(self.db, user_data).exec():
            self.load_data()

    def handle_unblock(self):
        row = self.table.currentRow()
        if row < 0: return
        user_id = self.users_list[row]['id']
        if self.db.unblock_user(user_id):
            QMessageBox.information(self, "Успех", "Разблокировано")
            self.load_data()

class LoginWindow(QWidget):
    def __init__(self, main_app_window, db):    
        super().__init__()
        self.main_app_window = main_app_window
        self.db = db
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Авторизация - ООО 'Мебель'")
        self.setMinimumSize(350, 500)
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Логин:"))
        self.login_input = QLineEdit()
        layout.addWidget(self.login_input)

        layout.addWidget(QLabel("Пароль:"))
        self.pass_input = QLineEdit()
        self.pass_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.pass_input)

        layout.addWidget(QLabel("Соберите пазл:"))
        self.captcha = CaptchaWidget()
        layout.addWidget(self.captcha)

        self.login_btn = QPushButton("Войти")
        self.login_btn.setMinimumHeight(40)
        self.login_btn.clicked.connect(self.handle_login)
        layout.addWidget(self.login_btn)

        self.setTabOrder(self.login_input, self.pass_input)

    def handle_login(self):
        login = self.login_input.text()
        password = self.pass_input.text()

        if not login or not password:
            QMessageBox.warning(self, "Внимание", "Заполните поля!")
            return

        if not self.captcha.is_correct():
            self.db.increment_failed_attempts(login) 
            QMessageBox.critical(self, "Ошибка", "Капча неверна!")
            self.captcha.reset()
            return

        success, message, role, is_blocked = self.db.check_auth(login, password)
        if success:
            QMessageBox.information(self, "Успех", message)
            self.close()
            self.main_app_window.set_user_role(role)
            self.main_app_window.show()
        else:
            QMessageBox.critical(self, "Ошибка", message)
            self.captcha.reset()

class MainWindow(QMainWindow):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Каталог продукции - ООО 'Мебель'")
        self.setMinimumSize(800, 600)

        cw = QWidget()
        self.setCentralWidget(cw)
        self.main_layout = QVBoxLayout(cw)
        
        self.info_layout = QHBoxLayout()
        self.welcome_label = QLabel("Добро пожаловать!")
        self.welcome_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.role_label = QLabel("Роль: Гость")
        
        self.info_layout.addWidget(self.welcome_label)
        self.info_layout.addStretch()
        self.info_layout.addWidget(self.role_label)
        self.main_layout.addLayout(self.info_layout)

        self.table_label = QLabel("Каталог мебели в наличии:")
        self.main_layout.addWidget(self.table_label)
        
        self.product_table = QTableWidget()
        self.product_table.setColumnCount(5)
        self.product_table.setHorizontalHeaderLabels(["ID", "Наименование", "Тип", "Ед. изм.", "Код"])

        header = self.product_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        self.main_layout.addWidget(self.product_table)
        self.bottom_layout = QHBoxLayout()
        
        self.refresh_btn = QPushButton("Обновить каталог")
        self.refresh_btn.clicked.connect(self.load_products)
        
        self.admin_btn = QPushButton("Открыть панель управления")
        self.admin_btn.clicked.connect(self.open_admin)
        self.admin_btn.hide()
        
        self.bottom_layout.addWidget(self.refresh_btn)
        self.bottom_layout.addStretch()
        self.bottom_layout.addWidget(self.admin_btn)
        
        self.main_layout.addLayout(self.bottom_layout)

        self.load_products()

    def set_user_role(self, role):
        self.role_label.setText(f"Вы вошли как: {role}")
        
        if role == "Администратор":
            self.admin_btn.show()
            self.welcome_label.setText("Режим администратора")
        else:
            self.admin_btn.hide()
            self.welcome_label.setText("Режим просмотра")

    def load_products(self):
        products = self.db.get_products()
        self.product_table.setRowCount(len(products))
        
        for row, p in enumerate(products):
            self.product_table.setItem(row, 0, QTableWidgetItem(str(p['id'])))
            self.product_table.setItem(row, 1, QTableWidgetItem(str(p['name'])))
            self.product_table.setItem(row, 2, QTableWidgetItem(str(p['n_type'])))
            self.product_table.setItem(row, 3, QTableWidgetItem(str(p['unit'])))
            self.product_table.setItem(row, 4, QTableWidgetItem(str(p['code'])))

    def open_admin(self):
        self.aw = AdminWindow(self.db)
        self.aw.show()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    database = DBManager()
    main_win = MainWindow(database)
    login_win = LoginWindow(main_win, database)
    login_win.show()
    sys.exit(app.exec())