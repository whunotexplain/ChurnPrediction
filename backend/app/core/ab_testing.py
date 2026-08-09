"""
Распределение запросов по A/B-группам.

Если передан customer_id — берём хэш от него, чтобы один и тот же клиент
всегда попадал в одну и ту же группу между визитами (иначе за разные
запросы он то видит модель A, то B — эксперимент перестаёт быть чистым,
это называется "cross-contamination" между группами).

Если customer_id не передан — обычный случайный сплит на уровне запроса.
"""

import hashlib
import random

from app.core.config import settings


def assign_variant(customer_id: str | None = None) -> str:
    if not settings.AB_TEST_ENABLED:
        return "A"

    if customer_id:
        digest = hashlib.sha256(customer_id.encode()).hexdigest()
        bucket = int(digest, 16) % 10_000 / 10_000
    else:
        bucket = random.random()

    return "B" if bucket < settings.AB_TRAFFIC_SPLIT else "A"
