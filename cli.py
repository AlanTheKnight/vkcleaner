from main import ApiHelper
from getpass import getpass


class CliApiHelper(ApiHelper):
    def login(self):
        self.LOGIN = input("Login: ")
        self.PASSWORD = getpass("Password: ")

    def two_auth(self):
        self.CODE = input("Code: ")
        return self.CODE, True


if __name__ == "__main__":
    helper = CliApiHelper()
    messages = helper.get_messages()
    for i, m in enumerate(messages, start=1):
        print(i, m['name'])
    print("Enter numbers of messages you want to delete:")
    print("\"ALL\" for all messages")
    print("Blank to skip")
    to_delete = input(">>> ")
    if to_delete:
        if to_delete == "ALL":
            to_delete = range(0, len(messages))
        else:
            to_delete = list(map(lambda i: int(i) - 1, to_delete.split(" ")))
        for i in to_delete:
            helper.delete_history(messages[i]['id'])
