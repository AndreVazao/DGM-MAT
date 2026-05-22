from abc import ABC
from abc import abstractmethod


class ProviderBase(ABC):

    @abstractmethod
    def authenticate(self):
        pass

    @abstractmethod
    def list_conversations(self):
        pass
