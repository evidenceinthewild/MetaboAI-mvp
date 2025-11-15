"""Lightweight Pydantic stub implementing the subset of features required for tests."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable, Optional, Union, get_args, get_origin


@dataclass
class FieldInfo:
    default: Any = ...
    metadata: Dict[str, Any] | None = None


def Field(default: Any = ..., **metadata: Any) -> FieldInfo:
    return FieldInfo(default=default, metadata=metadata or None)


class ConstrainedNumber:
    def __init__(self, base: type, *, gt: float | None = None, ge: float | None = None) -> None:
        self.base = base
        self.gt = gt
        self.ge = ge

    def __call__(self, value: Any) -> Any:
        coerced = self.base(value)
        if self.gt is not None and not coerced > self.gt:
            raise ValueError(f"Value {coerced} must be greater than {self.gt}")
        if self.ge is not None and not coerced >= self.ge:
            raise ValueError(f"Value {coerced} must be greater than or equal to {self.ge}")
        return coerced


def confloat(**constraints: Any) -> ConstrainedNumber:
    return ConstrainedNumber(float, **constraints)


def conint(**constraints: Any) -> ConstrainedNumber:
    return ConstrainedNumber(int, **constraints)


class BaseModel:
    __fields__: Dict[str, FieldInfo]
    __validators__: Dict[str, Iterable[Callable[[type, Any, Dict[str, Any]], Any]]]

    def __init_subclass__(cls) -> None:
        fields: Dict[str, FieldInfo] = {}
        validators: Dict[str, list[Callable[[type, Any, Dict[str, Any]], Any]]] = {}
        for name, attr in cls.__dict__.items():
            if isinstance(attr, FieldInfo):
                fields[name] = attr
        for attr in cls.__dict__.values():
            if getattr(attr, "__pydantic_validator__", False):
                field = attr.__pydantic_field__
                validators.setdefault(field, []).append(attr)
        cls.__fields__ = fields
        cls.__validators__ = validators

    def __init__(self, **data: Any) -> None:
        values: Dict[str, Any] = {}
        annotations = getattr(self.__class__, "__annotations__", {})
        for name, annotation in annotations.items():
            field_info = self.__class__.__fields__.get(name)
            has_default = field_info is not None and field_info.default is not ...
            if name in data:
                raw_value = data[name]
            elif has_default:
                raw_value = field_info.default
            elif hasattr(self.__class__, name):
                raw_value = getattr(self.__class__, name)
            else:
                raise ValueError(f"Missing field: {name}")

            value = _coerce(annotation, raw_value)
            for validator in self.__class__.__validators__.get(name, []):
                value = validator(self.__class__, value, values.copy())
            values[name] = value

        for name, value in values.items():
            setattr(self, name, value)

    def dict(self) -> Dict[str, Any]:
        return {name: getattr(self, name) for name in getattr(self.__class__, "__annotations__", {})}


def _coerce(annotation: Any, value: Any) -> Any:
    origin = get_origin(annotation)
    if isinstance(annotation, ConstrainedNumber):
        return annotation(value)
    if origin is Union:
        args = [arg for arg in get_args(annotation) if arg is not type(None)]  # noqa: E721
        if value is None and len(args) < len(get_args(annotation)):
            return None
        if args:
            return _coerce(args[0], value)
        return value
    if value is None:
        return None
    if origin is tuple and get_args(annotation):
        return tuple(_coerce(get_args(annotation)[0], item) for item in value)
    if isinstance(annotation, type):
        if issubclass(annotation, BaseModel):
            if isinstance(value, annotation):
                return value
            if isinstance(value, dict):
                return annotation(**value)
        if issubclass(annotation, _Enum):
            return annotation(value)
        if annotation in (int, float, bool, str):
            return annotation(value)
    return value


def validator(field_name: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        func.__pydantic_validator__ = True  # type: ignore[attr-defined]
        func.__pydantic_field__ = field_name  # type: ignore[attr-defined]
        return func

    return decorator


try:  # pragma: no cover
    from enum import Enum as _Enum
except Exception:  # pragma: no cover
    class _Enum:  # type: ignore[too-many-ancestors]
        pass
