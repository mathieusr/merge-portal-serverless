import datetime

class MergeLogs:

    def __init__(self, path: str):
        self.path = path

    def __enter__(self):

        self.file = open(self.path, "a")

        return self

    def __exit__(self, type, value, tb):

        self.file.close()

    def add_log(self, message: str):

        self.file.write(f"{self.get_date()} ---- {message} \n")


    def get_date(self):

        now = datetime.datetime.now()

        return now.strftime("%Y-%m-%d %H:%M:%S")

