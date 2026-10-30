# 原始解码结果到 frame_gop 的静态数据链

目标文件：lsx-ases.dll，SHA-256 f290ad5c396cf95353edcf7444385b7fa8bebebe04a42997a13a0207d34007b5。以下地址为 VA，分析未执行引擎。

1. 朗读评分 Scoring 调用 0x10179780，函数在 0x101797b0–0x101797c1 将输入 DecoderData 复制到 scorer+0x0c，并以原 DecoderData 为输入调用 ProcessedDecoderData，输出保存于 scorer+0xac（即前述对象+0xa0）。
2. ProcessedDecoderData 在 0x102dddc4–0x102dde57 遍历输入对象+0x58的8字节项，读每项第二个float；0x102dddef调用全局对象获取函数，0x102dddfc除以对象+0x290，0x102dde04通过符号位异或取反。结果顺序存入临时float数组。0x102dde5c–0x102ddefa 把数组复制为临时 processed 对象首个 vector，0x102dee74–81 经 0x100e8fa0 把该对象复制到 scorer+0xac。
3. 0x10179d0d–1d 将 scorer+0x0c 传给 PaScoreIntegration 准备函数 0x1017be70。0x1017c103–11e 通过 0x1009cd40 创建完整解码对象副本，0x1009ce2f–45 单独复制其+0xa0 processed 子对象的首个 vector。0x1017c13a调用 0x102df0b0 按 pass 裁切其他对象成员；逐指令审计到返回 0x102df508：改变的成员偏移为+0x4c、+0x94、+0xd0、+0xdc、+0x64、+0xe8、+0xf4、+0x104、+0x11c，未写 +0xa0 首个vector。注意此结论针对静态可见调用及成员偏移。
4. 0x1017c145–16b 将副本保存于 Integration+0x3a4 所指vector；0x1017c5ba–c6 复制首个解码对象到 Integration+0x270。其复制函数 0x100e8f84–91 将 +0xa0 processed 子对象复制至 Integration+0x310。0x10182a10–65 读取 Integration+0x310 的数据（错误信息称 frame_gop），按各音素对应帧数取均值。
5. 缩放参数：0x100d71d5–db 用配置对象+0x284调用 0x100d49a0；该函数 0x100d4b44–83 将 `acoustic-scale` 参数绑定到其this+0xc，即外层对象+0x290。Model::Initialize 0x100d945d–62 调初始化对象，0x100d948f 使用同对象+0xa8作为键，0x100d9579–7c 将此对象指针保存至map节点+0x28，0x100d95b7–d2 将该键复制至全局当前键0x10463cc4。0x100d7490以同一全局键调用0x100d9810查询map，在0x100d7515返回节点+0x28对象。因而 0x102dddef 读取的是当前模型的 acoustic-scale 字段。
6. 模型初始化在0x100d7143–86读取主配置的 `online-conf` 键到模型+0x90，注册参数后在0x100d72aa–b7以+0x90为路径调用 0x102d4e80；该函数保留 `kaldi::ParseOptions::ReadConfigFile` 标识（见online-parse.asm.txt）。本机 recognition/parta/Configfile 指向 online.conf；该文件按 encr 包装解码后明确有 `--acoustic-scale=1.0`。这为默认本地配置提供直接依据；已有运行日志未打印该次计算时内存值，故对运行期其他配置覆盖保留限制。

已确认从 `DecoderData+0x58` 每项第二float，经取反除 acoustic-scale，再到最终音素函数的 frame_gop 的数据桥。本地默认配置为1.0，尚无本次会话最终内存值。第二float是哪个声学/图权重及其如何产生须另追；不应把通用GOP后验公式当成安装程序的实现。
