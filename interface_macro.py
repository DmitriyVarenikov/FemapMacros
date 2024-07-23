from abc import ABC, abstractmethod


class IMacro(ABC):
    @abstractmethod
    def run_macro(self):
        pass
