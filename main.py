import sys
import os
import json
import vk_api
from PyQt5 import QtWidgets, QtGui
from widgets import CheckListWidget


class ApiHelper(object):
    LOGIN = None
    PASSWORD = None
    CODE = None

    def __init__(self):
        if os.path.isfile(".creds.json"):
            with open(".creds.json", "r") as f:
                data = json.load(f)
                self.LOGIN = data['login']
                self.PASSWORD = data['password']
        else:
            self.login()
        vk_session = vk_api.VkApi(
            self.LOGIN, self.PASSWORD,
            app_id=2685278, auth_handler=self.two_auth)
        vk_session.auth()
        self.vk = vk_session.get_api()
        self.save()

    def login(self):
        login = LoginWindow(helper=self)
        if not login.exec_():
            sys.exit()

    def save(self):
        with open(".creds.json", "w") as f:
            json.dump({
                "login": self.LOGIN,
                "password": self.PASSWORD
            }, f)
    
    def logout(self):
        os.remove(".creds.json")
        sys.exit()
    
    def two_auth(self):
        code = TwoFactorWindow(helper=self)
        if not code.exec_():
            sys.exit()
        return self.CODE, True
    
    def get_messages(self):
        messages = self.vk.messages.getConversations(count=200)['items']
        users = self.get_users(messages)
        data = []
        for i in messages:
            peer_id = i['conversation']['peer']['id']
            peer_type = i['conversation']['peer']['type']
            if peer_type == "user":
                name = users[peer_id]['first_name'] + ' ' + users[peer_id]['last_name']
            elif peer_type == "chat":
                name = i['conversation']['chat_settings']['title']
            else:
                continue
            data.append({
                "name": name,
                "id": peer_id,
                "type": peer_type
            })
        return data
    
    def get_users(self, messages):
        users = [
            i['conversation']['peer']['id'] for i in messages
            if i['conversation']['peer']['type'] == "user"
        ]
        return {
            user['id']: user for user in self.vk.users.get(user_ids=users)
        }

    def delete_history(self, peer_id):
        self.vk.messages.deleteConversation(peer_id=peer_id)


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        self.helper = kwargs.pop("helper")
        super().__init__(*args, **kwargs)
        self.setup()
        self.data = []
        self.refresh()
    
    def refresh(self):
        self.list.clean()
        self.data = self.helper.get_messages()
        self.list.addNewElements([i['name'] for i in self.data])
    
    def setup(self):
        self.setWindowTitle("VK Cleaner")
        self.setWindowIcon(QtGui.QIcon('icons/vk.png'))
        exit_action = QtWidgets.QAction('Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        logout_action = QtWidgets.QAction('Logout', self)
        logout_action.setShortcut('Ctrl+Shift+L')
        logout_action.triggered.connect(self.helper.logout)
        refresh_action = QtWidgets.QAction('Refresh', self)
        refresh_action.setShortcut('Ctrl+R')
        appmenu = QtWidgets.QMenu("App", self)
        appmenu.addActions([
            exit_action, refresh_action, logout_action
        ])
        menubar = self.menuBar()
        menubar.addMenu(appmenu)

        vlayout = QtWidgets.QVBoxLayout()
        self.list = CheckListWidget()
        hlayout = QtWidgets.QHBoxLayout()
        selectAllBtn = QtWidgets.QPushButton("Select all")
        deleteBtn = QtWidgets.QPushButton("Delete selected")
        selectAllBtn.clicked.connect(self.list.select)
        deleteBtn.clicked.connect(self.deleteMessages)
        hlayout.addWidget(selectAllBtn)
        hlayout.addWidget(deleteBtn)
        vlayout.addWidget(self.list)
        vlayout.addLayout(hlayout)
        widget = QtWidgets.QWidget()
        widget.setLayout(vlayout)
        self.setCentralWidget(widget)
    
    def deleteMessages(self):
        messages = [
            self.data[i] for i in self.list.get_selected_indexes()
        ]
        for i in messages:
            peer_id = i['id']
            self.helper.delete_history(peer_id)
        self.refresh()


class LoginWindow(QtWidgets.QDialog):
    def __init__(self, *args, **kwargs):
        self.helper = kwargs.pop("helper")
        super().__init__(*args, **kwargs)
        self.setup()
    
    def setup(self):
        self.setWindowIcon(QtGui.QIcon('icons/vk.png'))
        self.setWindowTitle("Login")
        form = QtWidgets.QFormLayout()
        self.loginEdit = QtWidgets.QLineEdit()
        self.passwordEdit = QtWidgets.QLineEdit()
        self.passwordEdit.setEchoMode(self.passwordEdit.PasswordEchoOnEdit)
        form.addRow("Login", self.loginEdit)
        form.addRow("Password", self.passwordEdit)
        hlayout = QtWidgets.QHBoxLayout()
        vlayout = QtWidgets.QVBoxLayout()
        cancelBtn = QtWidgets.QPushButton("Cancel")
        cancelBtn.clicked.connect(self.reject)
        submitBtn = QtWidgets.QPushButton("Proceed")
        submitBtn.clicked.connect(self.submit)
        hlayout.addWidget(cancelBtn)
        hlayout.addWidget(submitBtn)
        vlayout.addLayout(form)
        vlayout.addLayout(hlayout)
        self.setLayout(vlayout)
    
    def submit(self):
        login = self.loginEdit.text()
        password = self.passwordEdit.text()
        self.helper.LOGIN = login
        self.helper.PASSWORD = password
        self.accept()


class TwoFactorWindow(QtWidgets.QDialog):
    def __init__(self, *args, **kwargs):
        self.helper = kwargs.pop("helper")
        super().__init__(*args, **kwargs)
        self.setup()
    
    def setup(self):
        self.setWindowIcon(QtGui.QIcon('icons/vk.png'))
        self.setWindowTitle("Two Factor Authentication")
        form = QtWidgets.QFormLayout()
        self.codeEdit = QtWidgets.QLineEdit()
        form.addRow("Код", self.codeEdit)
        hlayout = QtWidgets.QHBoxLayout()
        vlayout = QtWidgets.QVBoxLayout()
        cancelBtn = QtWidgets.QPushButton("Cancel")
        cancelBtn.clicked.connect(self.reject)
        submitBtn = QtWidgets.QPushButton("Proceed")
        submitBtn.clicked.connect(self.submit)
        hlayout.addWidget(cancelBtn)
        hlayout.addWidget(submitBtn)
        vlayout.addLayout(form)
        vlayout.addLayout(hlayout)
        self.setLayout(vlayout)
    
    def submit(self):
        code = self.codeEdit.text()
        self.helper.CODE = code
        self.accept()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    api = ApiHelper()
    window = MainWindow(helper=api)
    window.show()
    sys.exit(app.exec_())
