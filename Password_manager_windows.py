import sys
import json
import os
import hashlib
import secrets
import string
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QClipboard


class PasswordManager(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Парольный менеджер")
        self.setGeometry(300, 300, 700, 500)

        self.master_password = "admin123"

        if not self.check_master_password():
            sys.exit()

        layout = QVBoxLayout()

        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Поиск по сайтам...")
        self.search_input.textChanged.connect(self.search_passwords)
        search_layout.addWidget(QLabel("🔍 Поиск:"))
        search_layout.addWidget(self.search_input)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Сайт", "Логин", "Пароль"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)

        form_group = QGroupBox("Добавить новый пароль")
        form_layout = QGridLayout()

        self.site_input = QLineEdit()
        self.site_input.setPlaceholderText("example.com")
        self.login_input = QLineEdit()
        self.login_input.setPlaceholderText("username@email.com")
        self.pass_input = QLineEdit()
        self.pass_input.setEchoMode(QLineEdit.Password)

        self.gen_btn = QPushButton("🎲 Сгенерировать")
        self.gen_btn.clicked.connect(self.generate_password)

        form_layout.addWidget(QLabel("Сайт:"), 0, 0)
        form_layout.addWidget(self.site_input, 0, 1)
        form_layout.addWidget(QLabel("Логин:"), 1, 0)
        form_layout.addWidget(self.login_input, 1, 1)
        form_layout.addWidget(QLabel("Пароль:"), 2, 0)
        form_layout.addWidget(self.pass_input, 2, 1)
        form_layout.addWidget(self.gen_btn, 2, 2)

        form_group.setLayout(form_layout)

        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("➕ Добавить")
        self.delete_btn = QPushButton("🗑 Удалить")
        self.copy_btn = QPushButton("📋 Копировать пароль")
        self.edit_btn = QPushButton("✏ Редактировать")
        self.export_btn = QPushButton("💾 Экспорт")

        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.edit_btn)
        btn_layout.addWidget(self.delete_btn)
        btn_layout.addWidget(self.copy_btn)
        btn_layout.addWidget(self.export_btn)

        self.status_label = QLabel("Готов")
        self.status_label.setStyleSheet("color: green; padding: 5px;")

        layout.addLayout(search_layout)
        layout.addWidget(self.table)
        layout.addWidget(form_group)
        layout.addLayout(btn_layout)
        layout.addWidget(self.status_label)

        self.add_btn.clicked.connect(self.add_password)
        self.delete_btn.clicked.connect(self.delete_password)
        self.copy_btn.clicked.connect(self.copy_password)
        self.edit_btn.clicked.connect(self.edit_password)
        self.export_btn.clicked.connect(self.export_passwords)

        self.setLayout(layout)
        self.passwords = []
        self.filtered_passwords = []
        self.load_passwords()

        self.timer = QTimer()
        self.timer.timeout.connect(self.clear_status)
        self.timer.setSingleShot(True)

    def check_master_password(self):
        password, ok = QInputDialog.getText(
            self, "Авторизация",
            "Введите мастер-пароль:",
            QLineEdit.Password
        )
        if ok and password == self.master_password:
            return True
        else:
            QMessageBox.critical(self, "Ошибка", "Неверный пароль!")
            return False

    def generate_password(self):
        length = 12
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        password = ''.join(secrets.choice(alphabet) for _ in range(length))
        self.pass_input.setText(password)
        self.show_status("✅ Сгенерирован надежный пароль!", "green")

    def add_password(self):
        site = self.site_input.text().strip()
        login = self.login_input.text().strip()
        password = self.pass_input.text()

        if not site:
            QMessageBox.warning(self, "Ошибка", "Введите название сайта!")
            return

        if not login:
            QMessageBox.warning(self, "Ошибка", "Введите логин!")
            return

        if not password:
            QMessageBox.warning(self, "Ошибка", "Введите пароль!")
            return

        for item in self.passwords:
            if item['site'].lower() == site.lower() and item['login'].lower() == login.lower():
                reply = QMessageBox.question(self, "Дубликат",
                                             f"Пароль для {site} уже существует. Перезаписать?",
                                             QMessageBox.Yes | QMessageBox.No)
                if reply == QMessageBox.No:
                    return
                self.passwords.remove(item)
                break

        self.passwords.append({
            'site': site,
            'login': login,
            'password': password
        })

        self.save_passwords()
        self.search_passwords()
        self.clear_form()
        self.show_status(f"✅ Пароль для {site} сохранен!", "green")

    def edit_password(self):

        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите запись для редактирования!")
            return


        if self.filtered_passwords:
            selected = self.filtered_passwords[current_row]
        else:
            selected = self.passwords[current_row]


        self.site_input.setText(selected['site'])
        self.login_input.setText(selected['login'])
        self.pass_input.setText(selected['password'])


        self.passwords.remove(selected)
        self.save_passwords()
        self.search_passwords()
        self.show_status("✏ Редактируйте и нажмите Добавить", "orange")

    def delete_password(self):
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите запись для удаления!")
            return

        if self.filtered_passwords:
            selected = self.filtered_passwords[current_row]
        else:
            selected = self.passwords[current_row]

        reply = QMessageBox.question(self, "Подтверждение",
                                     f"Удалить пароль для {selected['site']}?",
                                     QMessageBox.Yes | QMessageBox.No)

        if reply == QMessageBox.Yes:
            self.passwords.remove(selected)
            self.save_passwords()
            self.search_passwords()
            self.show_status(f"🗑 Пароль для {selected['site']} удален!", "red")

    def copy_password(self):
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите запись!")
            return

        if self.filtered_passwords:
            selected = self.filtered_passwords[current_row]
        else:
            selected = self.passwords[current_row]

        clipboard = QApplication.clipboard()
        clipboard.setText(selected['password'])

        self.show_status(f"📋 Пароль для {selected['site']} скопирован в буфер!", "green")

        QTimer.singleShot(30000, lambda: clipboard.setText("") if clipboard.text() == selected['password'] else None)

    def search_passwords(self):
        search_text = self.search_input.text().lower()

        if not search_text:
            self.filtered_passwords = self.passwords.copy()
        else:
            self.filtered_passwords = [
                p for p in self.passwords
                if search_text in p['site'].lower() or search_text in p['login'].lower()
            ]

        self.update_table()

    def update_table(self):
        self.table.setRowCount(len(self.filtered_passwords))

        for row, item in enumerate(self.filtered_passwords):
            self.table.setItem(row, 0, QTableWidgetItem(item['site']))
            self.table.setItem(row, 1, QTableWidgetItem(item['login']))

            password_item = QTableWidgetItem("••••••••")
            password_item.setData(Qt.UserRole, item['password'])
            self.table.setItem(row, 2, password_item)

        self.table.resizeColumnsToContents()

        self.show_status(f"📊 Найдено: {len(self.filtered_passwords)} записей", "blue", temporary=False)

    def export_passwords(self):

        if not self.passwords:
            QMessageBox.warning(self, "Ошибка", "Нет паролей для экспорта!")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить пароли",
            "passwords_backup.json",
            "JSON files (*.json)"
        )

        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(self.passwords, f, ensure_ascii=False, indent=2)
                self.show_status(f"💾 Экспорт выполнен в {file_path}", "green")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось экспортировать: {str(e)}")

    def save_passwords(self):
        try:
            with open("passwords.json", "w", encoding='utf-8') as f:
                json.dump(self.passwords, f, ensure_ascii=False, indent=2)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить: {str(e)}")

    def load_passwords(self):
        if os.path.exists("passwords.json"):
            try:
                with open("passwords.json", "r", encoding='utf-8') as f:
                    self.passwords = json.load(f)
                self.search_passwords()
                self.show_status(f"✅ Загружено {len(self.passwords)} паролей", "green")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить: {str(e)}")
                self.passwords = []

    def clear_form(self):
        self.site_input.clear()
        self.login_input.clear()
        self.pass_input.clear()

    def clear_status(self):
        self.status_label.setText("Готов")
        self.status_label.setStyleSheet("color: gray; padding: 5px;")

    def show_status(self, message, color="green", temporary=True):
        self.status_label.setText(message)
        self.status_label.setStyleSheet(f"color: {color}; padding: 5px;")

        if temporary:
            self.timer.start(3000)


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = PasswordManager()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()