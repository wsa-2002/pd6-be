INT32_LOW, INT32_HIGH = -2_147_483_648, 2_147_483_647


def int32(number: int) -> int:
    if number < INT32_LOW:
        return INT32_LOW
    if number > INT32_HIGH:
        return INT32_HIGH
    return number
