"""从已披露的分项复算示例，或检查用户本机模型。"""
import argparse
from pathlib import Path
from .formulas import long_sentence_score, paragraph_score, scale_to_question_points
from .models import SvrModel, read_scalers


def main():
    parser = argparse.ArgumentParser(description="朗读评分：已确认部分的局部重建")
    parser.add_argument("--client-dir", type=Path, help="client 目录；设置后读取模型信息")
    parser.add_argument("--model-dir", type=Path, help="相对于 client 的模型目录，可选")
    args = parser.parse_args()
    if args.model_dir and not args.client_dir:
        parser.error("--model-dir 需要配合 --client-dir 使用")
    if args.model_dir and args.model_dir.is_absolute():
        parser.error("--model-dir 必须使用相对于 client 的路径")
    print("示例：长句发音78.87、流利度100、完整度100")
    print(f"句子分（由已显示的两位分数近似重算）：{long_sentence_score(78.87, 100, 100):.4f}")
    coeff = [0.77266539, 0.05508793, 0.18843264, -23.51403671, -15.79654803]
    value = paragraph_score([68.10014925373136, 100, 92.025, 0, 18/99], coeff, 0.1992771)
    print(f"候选BJ参数复算百分制：{value:.6f}；8分制未舍入：{scale_to_question_points(value, 8):.6f}")
    print("提示：候选参数是否由本题运行时选用尚未完全证明。")
    if args.client_dir:
        relative_model_dir = args.model_dir or Path("resources/plugins/ases/ia32/win32/model/score/readaloud")
        model_dir = args.client_dir / relative_model_dir
        config = read_scalers(model_dir / "score-basic-feature.json")
        for name, field in (("svm_accuracy_normal.model", "pron_score"),
                            ("svm-fluency.model", "sentence_flu_score")):
            model = SvrModel.read(model_dir / name)
            stats = config[field]
            print(f"{name}: 输入维度={len(stats['mean'])} gamma={model.gamma} rho={model.rho} 支持向量={len(model.vectors)}")


if __name__ == "__main__":
    main()
