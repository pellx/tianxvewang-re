"""仅实现已确定的计算结构；普通 Python 浮点数不保证与原程序逐位相同。"""

from math import exp, fsum, isfinite


def clamp(value, low=0.0, high=100.0):
    return min(high, max(low, value))


def frame_gop(acoustic_weight, acoustic_scale):
    if acoustic_scale == 0:
        raise ValueError("acoustic_scale 不能为零")
    return -acoustic_weight / acoustic_scale


def phone_gop(frame_values):
    values = list(frame_values)
    if not values:
        raise ValueError("音素帧不能为空")
    return fsum(values) / len(values)


def phone_score(gop, mean, scale):
    if scale == 0:
        raise ValueError("音素评分 scale 不能为零")
    z = (gop - mean) / scale
    return max(0.0, 100.0 - 10.0 * min(0.0, z) ** 2)


def ordinary_word_score(phone_scores):
    """普通路径；特殊标记和特殊词路径尚未完整重建。"""
    scores = list(phone_scores)
    if not scores:
        raise ValueError("没有音素分，无法套用普通路径")
    return fsum(scores) / len(scores)


def completion_score(word_count, marker_count, zero_count):
    """有词位的普通路径。空句、无效数据等特殊路径未重建。"""
    if word_count <= 0 or not 0 <= zero_count <= word_count or marker_count < 0:
        raise ValueError("需要正词位数与有效计数")
    invalid = zero_count if zero_count > word_count / 2 else marker_count
    return 100.0 * (word_count - invalid) / word_count


def normalize(features, mean, scale):
    if not (len(features) == len(mean) == len(scale)):
        raise ValueError("特征、均值和尺度维度不一致")
    if any(s == 0 or not isfinite(s) for s in scale):
        raise ValueError("尺度必须为非零有限数")
    return [(x - m) / s for x, m, s in zip(features, mean, scale)]


def rbf_svr_predict(features, gamma, rho, support_vectors):
    """LIBSVM epsilon-SVR：support_vectors 为 (系数, {一基索引: 值})。"""
    total = 0.0
    for coef, sparse in support_vectors:
        if any(i < 1 or i > len(features) for i in sparse):
            raise ValueError("支持向量索引超过输入维度")
        distance = fsum((value - sparse.get(i, 0.0)) ** 2
                        for i, value in enumerate(features, 1))
        total += coef * exp(-gamma * distance)
    return total - rho


def fluency_postprocess(prediction, internal_scale, sentence_multiplier):
    """比例字段和乘数字段须由调用者提供；其来源尚未完全绑定。"""
    if internal_scale <= 0:
        raise ValueError("内部比例应为正数")
    t = clamp(prediction, 0.0, internal_scale) * internal_scale
    if t > 75.0:
        t = min(100.0, 2.0 * t - 75.0)
    return t * sentence_multiplier


def long_sentence_score(pronunciation, fluency, completion):
    """普通长句（超过 3 词）分支。"""
    value = 0.8 * pronunciation + 0.2 * fluency
    if completion <= 50:
        value *= completion / 75
    return clamp(value)


def aggregate_long_sentences(sentences):
    """每项为 (词数, 发音分, 完整度, 流利度)；仅支持全部超过3词。"""
    rows = list(sentences)
    if not rows or any(count <= 3 for count, *_ in rows):
        raise ValueError("仅实现全部句子超过3词的样本路径")
    total = sum(row[0] for row in rows)
    return tuple(fsum(row[0] * row[i] for row in rows) / total for i in (1, 2, 3))


def paragraph_score(features, coefficients, bias):
    """5项点积结构。调用方负责选择已验证的系数；不存在默认选档。"""
    if len(features) != 5 or len(coefficients) != 5:
        raise ValueError("需要5个篇章特征和5个系数")
    return clamp(fsum(x * c for x, c in zip(features, coefficients)) + bias)


def scale_to_question_points(percent, maximum):
    """返回未格式化数值；显示舍入由前端决定。"""
    return percent * maximum / 100.0
