import re

from django.core.exceptions import ValidationError


def only_digits(value):
    return re.sub(r"\D", "", value or "")


def validate_cnpj(value):
    digits = only_digits(value)
    if len(digits) != 14:
        raise ValidationError("CNPJ deve conter 14 dígitos.")
    if len(set(digits)) == 1:
        raise ValidationError("CNPJ inválido.")

    def check_digit(base, weights):
        total = sum(int(digit) * weight for digit, weight in zip(base, weights, strict=True))
        remainder = total % 11
        return "0" if remainder < 2 else str(11 - remainder)

    weights_first = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    weights_second = [6] + weights_first
    first = check_digit(digits[:12], weights_first)
    second = check_digit(digits[:12] + first, weights_second)
    if digits[12:] != first + second:
        raise ValidationError("CNPJ inválido.")


def normalize_cnpj(value):
    return only_digits(value)


def validate_cpf(value):
    digits = only_digits(value)
    if len(digits) != 11:
        raise ValidationError("CPF deve conter 11 dígitos.")
    if len(set(digits)) == 1:
        raise ValidationError("CPF inválido.")
    for position in (9, 10):
        total = sum(int(digit) * weight for digit, weight in zip(digits[:position], range(position + 1, 1, -1), strict=True))
        remainder = (total * 10) % 11
        expected = "0" if remainder == 10 else str(remainder)
        if digits[position] != expected:
            raise ValidationError("CPF inválido.")


def normalize_cpf(value):
    return only_digits(value)
