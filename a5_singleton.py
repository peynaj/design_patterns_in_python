"""
Singleton

Structure:
1- Singleton class: private field + private constructor + get_instance static method
"""
import copy
import threading


class ConfigManager:

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)

            return cls._instance

    def __init__(self, config: dict):
        with self._lock:
            if getattr(self, "_initialized", False):
                return
            self._config = copy.deepcopy(config)
            self._initialized = True

    @classmethod
    def reset(cls):
        with cls._lock:
            cls._instance = None

    def get(self, key: str, default=None):
        with self._lock:
            return self._config.get(key, default)

    def set(self, key: str, value):
        with self._lock:
            self._config[key] = value

    def delete(self, key: str):
        with self._lock:
            self._config.pop(key)

    def get_all(self):
        with self._lock:
            return copy.deepcopy(self._config)


def run_tests():
    config1 = ConfigManager({
        "DEBUG": True,
        "DATABASE_HOST": "localhost"
    })

    config2 = ConfigManager({
        "DEBUG": False,
        "DATABASE_HOST": "production-db"
    })

    assert config1 is config2

    assert config1.get("DEBUG") is True
    assert config2.get("DATABASE_HOST") == "localhost"

    config2.set("DEBUG", False)
    assert config1.get("DEBUG") is False

    config1.reset()
    config3 = ConfigManager({
        "DEBUG": True,
        "DATABASE_HOST": "localhost"
    })
    assert config3 is not config1

    print("Tests Finished!")


if __name__ == "__main__":
    run_tests()
