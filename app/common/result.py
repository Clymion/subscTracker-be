"""
A simple Result type for Python, inspired by Rust's Result enum.
"""

from typing import Generic, TypeVar

T = TypeVar("T")  # Success value type
E = TypeVar("E")  # Error value type


class Result(Generic[T, E]):
    """
    The Result class represents either a success (Ok) or a failure (Err).
    """

    def __init__(self, is_ok: bool, value: T | E):
        self._is_ok = is_ok
        self._value = value

    def is_ok(self) -> bool:
        """Returns True if the result is Ok."""
        return self._is_ok

    def is_err(self) -> bool:
        """Returns True if the result is Err."""
        return not self._is_ok

    def unwrap(self) -> T:
        """
        Returns the contained Ok value.

        Raises:
            Exception: If the result is an Err.
        """
        if self.is_ok():
            return self._value
        raise Exception(f"Called `unwrap()` on an `Err` value: {self._value}")

    def unwrap_err(self) -> E:
        """
        Returns the contained Err value.

        Raises:
            Exception: If the result is an Ok.
        """
        if self.is_err():
            return self._value
        raise Exception(f"Called `unwrap_err()` on an `Ok` value: {self._value}")

    @staticmethod
    def Ok(value: T) -> "Result[T, E]":
        """Create an Ok result."""
        return Result(is_ok=True, value=value)

    @staticmethod
    def Err(error: E) -> "Result[T, E]":
        """Create an Err result."""
        return Result(is_ok=False, value=error)
