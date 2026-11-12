# -*- coding: utf-8 -*-
"""题库难度自动打分算法。

输入四个维度的整数分（Rubric 锚点分）：
    C  概念与思维深度   [1, 4]
    S  推理链路长度     [1, 3]
    T  信息隐蔽度与陷阱 [1, 3]
    L  运算与审题负荷   [1, 3]

输出：
    连续总分（Elo 式，800 ~ 2800，可超过 2800 若未来扩展维度上限）
    + 离散等级（L1 ~ L5-3，非等距分档，左粗右细）。

设计要点
--------
1. 非线性合成：raw = 2**C + ALPHA * (S + T + L)
   - 思维深度 C 指数加权，C=4 的贡献（16）是 C=1（2）的 8 倍；
   - C=4 的最小合成值 > C=1 的最大合成值，"一票升档"由结构保证。
2. 硬性封顶：C=3 / C<=2 的题封顶在 L4（< 1950），纯繁琐或常规综合
   题无法进入压轴区间；C=4 保底 1950（L5-1）。
3. 非等距分档：低分段带宽宽（吸收打分噪音），高分段带宽窄
   （提高区分度），顶部开放（L5-3 不封顶）。
4. L4 横向拆分：T > L（陷阱 > 负荷）记 L4-B（巧），否则 L4-A（繁）。
"""

from dataclasses import dataclass
import math

# ----------------------------------------------------------------------
# 可调参数（教研可按题库分布微调，无需改动主流程）
# ----------------------------------------------------------------------
ALPHA = 1.5            # 辅助维度 (S+T+L) 的缩放系数
SCORE_MIN = 800.0      # 最易题分数（C=1, S=T=L=1）
SCORE_MAX = 2800.0     # 最难题分数（C=4, S=T=L=3）

RAW_MIN = 2 ** 1 + ALPHA * 3     # 6.5
RAW_MAX = 2 ** 4 + ALPHA * 9     # 29.5
GAIN = (SCORE_MAX - SCORE_MIN) / (RAW_MAX - RAW_MIN)

# 硬性规则阈值
L5_FLOOR = 1950.0      # C=4 一票升档的保底分（进入 L5-1）
L4_CEILING = 1949.5    # C<=3 的封顶分（无法进入 L5）

# 维度取值范围（闭区间）
RANGES = {"c": (1, 4), "s": (1, 3), "t": (1, 3), "l": (1, 3)}

# 非等距分档表：(下界, 上界, 等级, 星级, 标签)
LEVELS = [
    (800.0, 1200.0, "L1",    "★☆☆☆☆",  "基础直达"),
    (1200.0, 1500.0, "L2",   "★★☆☆☆",  "常规巩固"),
    (1500.0, 1750.0, "L3",   "★★★☆☆",  "综合中档"),
    (1750.0, 1950.0, "L4",   "★★★★☆",  "进阶拔高"),
    (1950.0, 2100.0, "L5-1", "★★★★★",  "压轴挑战"),
    (2100.0, 2400.0, "L5-2", "👑 S",    "竞赛/超难"),
    (2400.0, math.inf, "L5-3", "🏛 殿堂", "殿堂/极限"),
]

L4_A_LABEL = "进阶拔高（繁）"   # 过程繁琐：运算/阅读/分类讨论负荷大
L4_B_LABEL = "进阶拔高（巧）"   # 思维卡点：陷阱隐蔽、需特定技巧


@dataclass(frozen=True)
class DifficultyRating:
    """打分结果。"""
    score: float        # 连续总分（800 ~ 2800+）
    level: str          # 离散等级编码，如 "L3"、"L4-B"、"L5-2"
    stars: str          # 前端星级展示
    label: str          # 中文标签
    raw: float          # 合成前的原始非线性分（调试/审计用）


def _validate(name: str, value) -> int:
    """校验维度分：必须是取值范围内的整数。"""
    lo, hi = RANGES[name]
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"维度 {name} 需为数字，收到 {value!r}")
    if value != int(value):
        raise ValueError(f"维度 {name} 需为整数锚点分（{lo}~{hi}），收到 {value}")
    value = int(value)
    if not lo <= value <= hi:
        raise ValueError(f"维度 {name} 超出范围 [{lo}, {hi}]，收到 {value}")
    return value


def score_difficulty(c: int, s: int, t: int, l: int) -> DifficultyRating:
    """根据四个维度分计算最终难度评分。

    参数
    ----
    c : 概念与思维深度，1~4
    s : 推理链路长度，1~3
    t : 信息隐蔽度与陷阱，1~3
    l : 运算与审题负荷，1~3
    """
    c = _validate("c", c)
    s = _validate("s", s)
    t = _validate("t", t)
    l = _validate("l", l)

    # 1) 非线性合成：思维深度指数加权，辅助维度线性叠加
    raw = 2 ** c + ALPHA * (s + t + l)

    # 2) 线性映射到 Elo 式连续分
    score = SCORE_MIN + GAIN * (raw - RAW_MIN)

    # 3) 硬性规则（保险丝）
    if c >= 4:
        # 一票升档：非标构造保底进入压轴区间
        score = max(score, L5_FLOOR)
    else:
        # 封顶：思维深度不足，无论多繁琐都不进 L5
        score = min(score, L4_CEILING)

    score = round(score, 1)

    # 4) 非等距分档映射
    for lo, hi, level, stars, label in LEVELS:
        if lo <= score < hi:
            if level == "L4":
                # L4 横向拆分：陷阱高于负荷 → 巧；否则 → 繁
                if t > l:
                    level, label = "L4-B", L4_B_LABEL
                else:
                    level, label = "L4-A", L4_A_LABEL
            return DifficultyRating(score, level, stars, label, round(raw, 2))

    # score >= 2400 已被 math.inf 上界覆盖，理论不可达
    raise RuntimeError(f"分档映射失败：score={score}")


# ----------------------------------------------------------------------
# 自测与演示
# ----------------------------------------------------------------------
if __name__ == "__main__":
    cases = [
        # (C, S, T, L, 说明)
        (1, 1, 1, 1, "最简单：单知识点直接套用"),
        (1, 2, 2, 3, "思维简单但繁琐的题（原文反例 1）"),
        (4, 2, 1, 1, "思维极深但题干短计算少（原文反例 2）"),
        (2, 1, 1, 1, "常规巩固"),
        (2, 3, 3, 3, "纯繁琐题：分类多、运算大（封顶 L4-A）"),
        (3, 2, 2, 2, "标准综合中档"),
        (3, 3, 3, 2, "综合+强陷阱（L4-B 巧）"),
        (3, 3, 3, 3, "C=3 全满（封顶 L4，不进 L5）"),
        (4, 1, 1, 1, "非标构造但其余极简（保底 L5-1）"),
        (4, 3, 2, 2, "跨模块综合+强构造（竞赛级）"),
        (4, 3, 3, 3, "最难题（顶格 L5-3）"),
    ]
    print(f"{'C S T L':<8} {'总分':>7}  {'等级':<6} {'星级':<9} 说明")
    print("-" * 72)
    for c, s, t, l, desc in cases:
        r = score_difficulty(c, s, t, l)
        print(f"{c} {s} {t} {l:<4} {r.score:>7.1f}  {r.level:<6} {r.stars:<9} {desc}")

    # 断言自检
    assert score_difficulty(1, 2, 2, 3).score < 1500      # 繁琐简单题 < L3
    assert score_difficulty(4, 2, 1, 1).score > 2100      # 深思维题 > 繁琐题 且进 S 级
    assert score_difficulty(1, 2, 2, 3).score < score_difficulty(4, 2, 1, 1).score
    assert score_difficulty(2, 3, 3, 3).level.startswith("L4-A")  # 纯繁琐封顶 L4-A
    assert score_difficulty(3, 3, 3, 3).level.startswith("L4")    # C=3 封顶 L4
    assert score_difficulty(4, 1, 1, 1).level == "L5-1"           # C=4 保底
    assert score_difficulty(4, 3, 3, 3).level == "L5-3"           # 顶格
    assert score_difficulty(3, 3, 3, 2).level == "L4-B"           # 陷阱>负荷 → 巧
    print("\n[自检] 全部断言通过 ✓")
