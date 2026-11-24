"""Collected validation messages for forms. Callers still receive a plain list."""


class ErrorList:
    def __init__(self) -> None:
        self._messages: list[str] = []

    def add(self, message: str) -> None:
        self._messages.append(message)

    def extend(self, messages: list[str]) -> None:
        self._messages.extend(messages)

    def messages(self) -> list[str]:
        return list(self._messages)

    def __bool__(self) -> bool:
        return bool(self._messages)
