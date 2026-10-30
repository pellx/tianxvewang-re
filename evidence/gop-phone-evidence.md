# 音素 GOP：静态证据和限制

目标：本机 lsx-ases.dll，SHA-256 f290ad5c396cf95353edcf7444385b7fa8bebebe04a42997a13a0207d34007b5。逐帧 GOP 上游具体生成式和现有题目的标准化参数值尚未证明，下面不以通常的教科书公式或配置文件名称代替证据。

1. __PhoneScoreInfo（反汇编 phone-score.asm.txt）：VA 0x101829eb..0x10182a69，对该音素对应的 frame_gop 数值累计，再除以该音素的帧计数 N。即 G=sum(frame_gop)/N；空帧及特殊浮点值不在普通公式范围。VA 0x10182a76..0x10182a7f 对数组中的 ID<=10 有置0特殊分支，ID含义尚未全部确认。
2. __PhoneHundredScore：VA 0x10182e30 读上述初始音素分，根据两个内部选择字段走不同分支。普通标准化分支执行 z=(G-m)/s，其中 m,s 分别取对象字段；例如 VA 0x10182e84..0x10182e8c 从 +0x61c、+0x620 读值。不同分支选不同字段；不声称已经确定本题字段对应的具体配置项和数值。
3. VA 0x10182ff4..0x10183020 所有路径汇合，执行 score=max(0,100-10*min(0,z)^2)。100和10在注释反汇编中已读为float常量。仅当 z 为有效有限数值时可以按此常规数学解释。
4. 安装配置 recognition/parta/Configfile 指定 acoustic-model=final.mdl、tree、phones、lexicon 和 mfcc.conf。此配置与本地历史日志支持使用本地资源；不因此声称已经追出 frame_gop 的逐帧后验/似然公式。

实际日志仅含音素百分制结果，未记录每帧GOP及本题参数。无法用已显示的59.36反推唯一的原始音素GOP。
