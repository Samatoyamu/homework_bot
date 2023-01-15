class JSONError(Exception):
    """Ошибка полученние JSONа."""

    pass


class RequestError(Exception):
    """Ошибка при запросе к основному API."""

    pass


class CurrentDateKeyError(Exception):
    """В ответе API отсутствует дата ответа."""

    pass


class CurrentDateNotint(Exception):
    """Дата ответа имеет неправильный тип."""

    pass
