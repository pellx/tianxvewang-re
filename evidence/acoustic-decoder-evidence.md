# 声学缓存与标准在线解码器的静态追踪

## 资产

见 `acoustic-asset-audit.json` 和复算脚本。模型主 output 节点是 output.affine，output-xent 的 LogSoftmax 是辅助分支，priors 向量为空。安装包 online.conf 中 acoustic-scale=1.0，但是否被运行时覆盖未验证。

## 输出缓存

`cache-advance.asm.txt` VA 0x100c8c23..0x100c8c95，从网络取得名为 output 的矩阵；若对象包含非空向量则用 -1 做加向量运算，再调用 VA 0x1004bc80（见 matrix-scale.asm.txt）对矩阵按某标量缩放。此模式与 Kaldi 的 prior 校正及 acoustic-scale 缩放吻合；空 priors 模型会使原始默认路径略过 prior 扣除，但未动态验证运行对象。

MSVC RTTI `.?AVDecodableAmNnetLoopedOnlineCache@nnet3@kaldi@@`：类型描述符 VA 0x1046866c，完整对象定位器 VA 0x104204b0，虚表 VA 0x103f2994，首槽值 0x100c8dc0。安装 DLL 中 VA 0x1009a21e 调用缓存基类构造，0x1009a223 把虚表 0x103f2994 写入对象，0x1009a229 写入对象+0xa4 的另一对象指针。

`cache-likelihood.asm.txt`：首虚函数 0x100c8dc0 读取第一个参数作为帧索引，若缓存不足调用 0x100c8950；0x100c8de9..0x100c8e01 从 object+0xa4 所指对象+0x48 找到第二参数索引对应的整数映射，再据帧行和映射列索引 object+0x04 指向的浮点矩阵，x87 fld 返回该值。此处可确认缓存和映射，但缺乏对表中索引语义的独立运行时验证。按类名和 Kaldi 数据布局，second argument 是 transition ID、映射列是 pdf ID 的解释可信，但应与数据对象赋值链一起验证。

## 标准在线 decoder 的处理

历史日志 `[应用数据目录]/logs/ases-20261029.log:373590` 在当前题记录了 `kaldi::LatticeFasterOnlineDecoder::ProcessNonemitting`，证明评测期间该类被调用，并不足以单独绑定下面的缓存对象到同一调用实例。

`standard-emitting.asm.txt`：调度函数 0x1021e370 根据 FST 类型调用 const、vector 和其他模板实现。const FST 路径 0x1021f009..f01a 计算并保存一个负基准偏移，0x1021f12b..f13b 以帧和弧标签调用传入解码对象首虚函数，用 x87 fsubr 从负基准减返回值；0x1021f26a..f27c 把结果放入新结构的+0x10。0x1021f0b8..f0d1 把每帧负基准写入数组。

`traceback-standard.asm.txt`：0x1021ddac..ddca 把反向链接 +0x10 的浮点量减去对应帧偏移并写到输出结构+0x0c。若写入和读取对应同一帧，基准偏移代数上抵消，输出该项为虚函数返回值的负数。数据结构字段与调用桥的完整语义、该题运行时 FST 实例和 cache 实例尚未在本次静态追踪闭合，不得仅以该推导声称 frame_gop 公式已完整确认。

## 对象绑定的进一步检查

polly::Decoder::Decoder 的入口 0x10099a60，调用者 0x100e6e17；0x1009a118..a128 依赖 decoder 类型字段等于 1 和第 3 个栈参数为空，才进入 0x1009a1b5 的对象创建分支。该分支构造外层对象，在 outer+0x10 放上述 cache，在 outer+0xb8 创建 decoder 成员。wrapper 虚表为 0x103f2bf4，其首槽 0x100a62d0，代码见 wrapper-cache-call.asm.txt:28：将 outer+0x10 的 cache 传给 outer+0xb8 对象的 0x100cb2f0。此处调用 0x100cb2f0，不能直接当成前文标准 decoder 的 0x1021e370，也尚未证明本次题目进入该分支。相关对象构造与缓存使用关系已经明确，但该题是否使用，以及与前述标准类的相应实例是否相同，仍需独立核实。

0x100cb2f0 是 FST 类型分派（cache-emitting-dispatch.asm.txt）；const FST 路径 0x100cbf70 中，0x100cc0b8..0x100cc0c9 保存负基准偏移，0x100cc1f6..0x100cc21a 调 cache 首虚函数后用该偏移减返回值，0x100cc327..0x100cc338 写入链接 +0x10，见 cache-emitting-const.asm.txt。该构造分支内 cache 到解码弧的链接已证明；本题是否使用这一分支及该路径的回溯与 frame_gop 的完整数据链尚未独立证明。
