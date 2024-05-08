import os


class AppConfig:
    def __init__(self):
        self.SECRET_KEY = None
        self.PORT = None
        self.HOST = None
        env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                '../../.env')
        with open(env_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):  # Ignore empty lines and comments
                    key, value = line.split("=")
                    setattr(self, key, value)
