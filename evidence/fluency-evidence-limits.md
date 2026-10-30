# Bounded static evidence: sentence fluency

Target: installed `resources/plugins/ases/ia32/win32/lsx-ases.dll`, SHA256 `f290ad5c396cf95353edcf7444385b7fa8bebebe04a42997a13a0207d34007b5`.

Source disassembly: `../sentence-fluency.asm.txt`; virtual addresses below, image base `0x10000000`. This note records observed code only. The engine was not executed, and no audio was recorded or uploaded.

## Confirmed prediction and postprocessing

`PaScoreIntegration::__Default_Feature_Sentence_Fluency` starts at `0x101890a0` (its diagnostic string is at VA `0x10402444`, file offset `0x401644`).

1. Six float values are appended at `0x10189b63..0x10189c91`.
2. At `0x10189cc0..0x10189cd6`, each value is converted to double, subtracts the corresponding mean from the vector at `this+0x65c`, divides by the corresponding scale at `this+0x668`, then converts back to float.
3. The model filename string is read from `this+0x644`; the call at `0x10189d0c` targets `SvmScorePredict` (`0x101e7e10`).
4. Successful prediction `p` is postprocessed at `0x10189d1e..0x10189d75`:

```text
m = float32(this[0x26c])
t = float32(clamp(p, 0, m) * m)
if t > 75:
    t = min(100, float32(2*t - 75))
F_sentence = this[0x504][sentence_index] * t
```

The `75` comparison uses float at VA `0x1041aa9c`; the subtraction uses double `75.0` at `0x1041a9c0`; the cap is `100.0`. The assignment/meaning of `this+0x26c` was **not established in this bounded pass**. Do not substitute `10` or `100` without separate evidence. The multiplier at `this+0x504` is also retained as a structural fact rather than given an unproven semantic name.

## Six feature positions: exact local provenance, incomplete semantic labels

The feature constructor has no descriptive per-feature strings. These statements identify the machine operations and source fields, not inferred training feature names.

* x0: the number of selected integer entries divided by local integer `[ebp-0xb4]`, at `0x101899f7..0x10189a4b`, appended at `0x10189b63`. Entries come from local vector `[ebp-0x34]` constructed at `0x10189730..0x10189874`.
* x1: population variance of those selected integer entries, at `0x10189a47..0x10189a95`, appended at `0x10189b80`. The squared-difference accumulation is rounded to float inside the loop; there is **no square root** for x1.
* x2: `len(D) / (sum(D) * 3.0 / 100.0)`, at `0x10189ab4..0x10189b46`, appended at `0x10189bc0`. D is the integer vector `[ebp-0x28]` populated at `0x10189650..0x101896ba` using lengths of nested vectors rooted at `this+0x31c`.
* x3: the per-sentence float at `this+0x528`, loaded at `0x10189afe..0x10189b35`, appended at `0x10189bfa`. `__Feature_Sentence_Speed` (start `0x10185ad0`, own name string VA `0x10401cb8`) writes this vector; the precise units/display conversion are not resolved here.
* x4: population standard deviation of `0.03 * D`, computed by sum, mean, squared deviations, division by vector length and square root at `0x101898f0..0x101899cf`; appended at `0x10189c28`.
* x5: `sum(selected entries) / sum(D)`, computed at `0x10189a10..0x10189ad3`, appended at `0x10189c62`.

Selection details are visible at `0x101897a0..0x10189825`: index lies between the first/last selected boundaries, `this+0x328[index] <= 10`, index is absent from an excluded-gap-index list, and nested vector length at `this+0x31c[index]` is greater than `24`. The excluded-gap-index list is constructed at `0x101893b0..0x101894c3`. Full semantic identities of all nested structures and empty-vector edge behavior are **not completely mapped**, so this is not a complete audio-to-feature reconstruction.

At `0x1018971f..0x1018972a`, an outer count `<=3` or no qualifying nonempty entries bypasses the six-feature prediction. The fallback at `0x10189dda..0x10189e32` uses the per-sentence accuracy vector `this+0x558`, multiplied by the same `this+0x504` value.

## Limits for reporting

The local model format, normalization, model invocation, postprocessing, and paragraph aggregation are distinct evidence claims. A confirmed 14-dimensional pronunciation model does not by itself identify every pronunciation input feature. This pass did not fully name all 14 pronunciation features or fully map all six fluency source structures. It therefore supports a truthful partial reconstruction and an explicit limit, not a claim of complete reproduction from raw audio.
