# 实际“朗读短文”题：外层流程、合分公式与加分核查

目标：book2821FE6574D4930635501353FDD4A060 / lessonC65DB7D1A13D5A965301295DF2F21EEB / questionB69D97465D9EB7AAB8E2FEFB98512C6D。
本报告只读取本地发布文件及已有结果，不运行引擎、不录音、不上传。代码身份与native-findings.md一致。

## 实际题型，及模型名称的纠正

题目缓存answer.json记录：parta / ReadAloud，旧QuestionType=Repeat，QuestionTypeV3=ParagraphReadAloud，Area=beijing，LearnPeriod=SeniorHigh，ResponseMode=ReadAloud，DecoderType=FA，ContentType=Paragraph。
本次实际结果的score_type=ParagraphReadAloud，native运行日志进入PaParagraphReadaloudScorer。

重要：PaScoreIntegration.this+0x8b0 是 QuestionType 枚举，不是地区枚举。GetQuestionTypeStr（VA1007e810）确认枚举1→Repeat、2→ParagraphReadAloud、7→ParagraphRecite、3→Paragraph、13→ParagraphTextbook、14→ParagraphDubbing。模型系数虽名为gd/bj/gz，但ComputeParagraphScore本处的选择直接依据题型枚举。

该题ParagraphReadAloud=2，代码VA1017da9a..1017dab6选取this+0x854系数向量和+0x860偏置。更正：目前尚未完整证明配置对象中bj_paragraph_score_model的向量如何搬运到这两个integration成员，不能把该对应关系写成已完全确认。题型选择、配置解析和数值复算分别是证据，但缺失的成员复制桥不能由数值近似代替。

## 已确认的合分结构与候选BJ参数

设：

- A：句子pronounce按句子权重加权后的篇章发音分。
- C：句子completion按相同权重加权后的篇章完整度。
- F：句子fluency按相同权重加权后的篇章流利度。
- P50：排除specific_words_score等条件后的有效词中，词分<=50的比例。
- P50_70：同一有效词集合中50<词分<=70的比例。

DLL确认的结构是对下列五项做系数点积、加偏置并限制0..100。若使用配置中的BJ参数，展开为：

```text
base = clamp(
    0.77266539*A
  + 0.05508793*C
  + 0.18843264*F
  - 23.51403671*P50
  - 15.79654803*P50_70
  + 0.1992771,
  0, 100)
```

证据：paragraph-coeff-select.asm.txt，VA1017da9f选择向量，VA1017dba6..1017dbbf点积加偏置，VA1017dbc9..1017dbe8夹到0..100。以上数字直接来自解码后的model/score/readaloud/score-basic-feature.json中bj_paragraph_score_model，并非拟合得到；但这些数字进入本题所选成员的复制链尚缺一步静态证明。

有效词过滤器VA101bc1c0会先将词转小写，再检查specific_words_score集合；其调用点还检查词flag。当前样本完整度100，public数值结果与同序题目词表可以验证本次集合统计。没有将题目词文本保存到复算文件。

## 本次可复现的数值证据

- 共9句，句词数[7,16,8,19,16,8,18,16,26]，总计134词。本题每句均超过3词，因此这一样本的句子权重为各句词数/134。
- 用已经公开到两位小数的句子分重算：A=68.10014925373136，C=100，F=92.025。
- 排除specific_words_score后99词；其中<=50有0词、50至70有18词，因此P50=0，P50_70=18/99。
- 代入上式得72.79511253637436；原应用返回score=72.79、original_score=72.79、pronounce=68.1、completion=100、fluency=92.02。
- 对照default_paragraph_score_model得到72.80815625024424。输入已经只剩两位小数，尚无内部精度误差边界，因此约0.013的差值不能单独排除default，也不能据此证明本题选用BJ参数。

完整数字保存在actual-aggregate-replay.json。输入为已有JSON中已截断的句子/词分，所以这里只是数值核验，不能声称已恢复原引擎全部float内部状态。JSON数值截断到两位的具体writer路径尚未完成静态证明；不要把推断的格式化公式当成已确认指令。

## paragraph_addscore对本次成绩无影响

实际ParagraphReadaloudScorer::Scoring（入口VA10179b30）确实包含可选AddScore分支，不是从Textbook类推。

1. 选出本次pass的基础输出后，VA1017a0df..1017a0e6先把score复制到original_score对应槽位。
2. VA1017a178检查this+0xd1c的paragraph_addscore开关；题目特殊参数可覆盖配置。
3. 为true时VA1017a1d0调用AddScore（入口VA101963a0）；成功后仅覆盖score（this+0xe20），不修改A/C/F。
4. AddScore在VA101964be..101964cf先检查base_score > hparams[1]；本配置hparams[1]=60，满足则立即原分返回，且尚未进入任何AddscoreGetFeature/UseModelPredict日志。

本次基分约72.795>60，所以无论开关最终是否触发调用，这个调整分支都不会改变本次成绩。运行记录score=original_score=72.79也支持这一点。不能仅根据没有AddScore日志判断没有调用，因为高分早退发生在内部日志之前。

该题实际isReject=0、abnormal=false，只有一次朗读pass（repeated_num=1，choose_id=0），所以本次没有多pass择优或拒评改变最终分。拒评的全部条件不在本报告中恢复。

## score_factor

当前实际score_factor=1、score_level_type=3；运行日志显示加载svm_accuracy_normal。它改变前面的词/句发音模型与阈值档位，不是把最后的百分制分再乘1或简单增减分。本报告没有把Retell的LightGBM选档代码混入该朗读分支。

## 证据文件

- paragraph-readaloud-scoring.asm.txt：实际外层Scoring，以及AddScore开关/调用/只覆盖score。
- paragraph-coeff-select.asm.txt：系数选择、点积、clamp。
- question-type-enum.asm.txt：QuestionType枚举到字符串的绑定。
- set-output-aggregates.asm.txt：A/C/F及基础score进入输出结构。
- special-word-filter.asm.txt：小写与specific_words_score过滤。
- addscore.asm.txt：60分高分早退等调整入口。
- actual-reading-numeric-result.json：parent提取的脱敏数字结果。
- actual-aggregate-replay.json：本次候选模型的数字核验。
