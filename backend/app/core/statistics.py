"""
Статистика для A/B-теста двух моделей (accuracy как метрика успеха).

Что именно тестируем: гипотезу H0 "доля верных предсказаний у модели A
равна доле верных предсказаний у модели B" против H1 "доли различаются".
Это двухвыборочный z-тест для пропорций — тот же математический
аппарат, что используют для сравнения конверсии в классическом
продуктовом A/B-тесте (клик/не клик), просто здесь "конверсия" —
это "предсказание совпало с реальным исходом".
"""

import math
from dataclasses import dataclass

from scipy.stats import norm


@dataclass
class ProportionStats:
    n: int              # сколько исходов собрано в группе
    successes: int       # сколько предсказаний оказались верными
    p: float              # доля верных = successes / n


@dataclass
class ABTestResult:
    variant_a: ProportionStats
    variant_b: ProportionStats
    diff: float                 # p_b - p_a
    z_stat: float
    p_value: float
    significant: bool           # p_value < alpha
    ci_low: float                # доверительный интервал для diff
    ci_high: float
    alpha: float


def compute_proportion_stats(n: int, successes: int) -> ProportionStats:
    if n == 0:
        return ProportionStats(n=0, successes=0, p=0.0)
    return ProportionStats(n=n, successes=successes, p=successes / n)


def two_proportion_z_test(a: ProportionStats, b: ProportionStats, alpha: float = 0.05) -> ABTestResult:
    """
    Двухвыборочный z-тест для пропорций.

    Шаг 1 — z-статистика считается через ОБЪЕДИНЁННУЮ (pooled) пропорцию,
    потому что при H0 (доли равны) она и есть лучшая общая оценка истинной
    доли — так тест честнее к ложным срабатываниям (false positive rate
    действительно держится на уровне alpha).

    Шаг 2 — доверительный интервал для разницы (p_b - p_a) считается уже
    БЕЗ пулинга (unpooled SE), потому что здесь мы не предполагаем H0 —
    наоборот, хотим оценить, какова разница на самом деле, не навязывая
    ей никакого значения заранее.

    Это стандартная практика: pooled SE — для теста значимости,
    unpooled SE — для доверительного интервала. Смешивать их — частая
    ошибка, которая портит либо мощность теста, либо точность интервала.
    """
    if a.n == 0 or b.n == 0:
        raise ValueError("Недостаточно данных: в одной из групп нет ни одного исхода")

    pooled_p = (a.successes + b.successes) / (a.n + b.n)
    se_pooled = math.sqrt(pooled_p * (1 - pooled_p) * (1 / a.n + 1 / b.n))

    diff = b.p - a.p
    z_stat = diff / se_pooled if se_pooled > 0 else 0.0

    # Двусторонний p-value: интересует и "B хуже", и "B лучше"
    p_value = 2 * (1 - norm.cdf(abs(z_stat)))

    se_unpooled = math.sqrt(a.p * (1 - a.p) / a.n + b.p * (1 - b.p) / b.n)
    z_crit = norm.ppf(1 - alpha / 2)
    ci_low = diff - z_crit * se_unpooled
    ci_high = diff + z_crit * se_unpooled

    return ABTestResult(
        variant_a=a, variant_b=b, diff=diff, z_stat=z_stat, p_value=p_value,
        significant=p_value < alpha, ci_low=ci_low, ci_high=ci_high, alpha=alpha,
    )


def required_sample_size(baseline_p: float, min_detectable_effect: float,
                          alpha: float = 0.05, power: float = 0.8) -> int:
    """
    Сколько исходов нужно НА КАЖДУЮ группу, чтобы с вероятностью `power`
    (обычно 80%) обнаружить разницу размером `min_detectable_effect`
    (например 0.05 = 5 процентных пунктов accuracy), если она реально
    существует — при уровне значимости alpha (обычно 5%).

    Смысл: если ты не посчитал это ЗАРАНЕЕ, легко провести тест на
    30 наблюдениях, получить p_value=0.4 и сделать неверный вывод
    "модели не отличаются" — хотя на самом деле выборка просто
    слишком мала, чтобы что-либо обнаружить (тест недостаточно мощный).
    """
    z_alpha = norm.ppf(1 - alpha / 2)
    z_beta = norm.ppf(power)

    p1 = baseline_p
    p2 = baseline_p + min_detectable_effect
    p2 = min(max(p2, 0.0), 1.0)

    numerator = (z_alpha + z_beta) ** 2 * (p1 * (1 - p1) + p2 * (1 - p2))
    n = numerator / (min_detectable_effect ** 2)
    return math.ceil(n)
