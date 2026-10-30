"""读取本机文件；不复制或分发原程序模型。"""

import json
import struct
from dataclasses import dataclass
from pathlib import Path


def read_payload(path):
    data = Path(path).read_bytes()
    if data[:4] != b"encr":
        return data
    if len(data) < 8:
        raise ValueError("模型封装头不完整")
    length = struct.unpack_from("<I", data, 4)[0]
    payload = data[8:]
    if len(payload) != length:
        raise ValueError("模型封装长度不一致")
    return bytes(byte ^ (i % 8 + 1) for i, byte in enumerate(payload))


def read_scalers(path):
    return json.loads(read_payload(path).decode("utf-8"))


@dataclass
class SvrModel:
    gamma: float
    rho: float
    vectors: list

    @classmethod
    def read(cls, path):
        content = read_payload(path).decode("ascii")
        header, sep, rows = content.partition("\nSV\n")
        if not sep:
            raise ValueError("缺少 LIBSVM SV 标记")
        fields = dict(line.split(maxsplit=1) for line in header.splitlines())
        if fields.get("svm_type") != "epsilon_svr" or fields.get("kernel_type") != "rbf":
            raise ValueError("只支持 RBF epsilon-SVR")
        vectors = []
        for row in rows.splitlines():
            items = row.split()
            if not items:
                continue
            sparse = {}
            for item in items[1:]:
                key, value = item.split(":", 1)
                idx = int(key)
                if idx <= 0 or idx in sparse:
                    raise ValueError("无效的支持向量索引")
                sparse[idx] = float(value)
            vectors.append((float(items[0]), sparse))
        if len(vectors) != int(fields["total_sv"]):
            raise ValueError("支持向量数量与头部不一致")
        return cls(float(fields["gamma"]), float(fields["rho"]), vectors)

    def predict(self, features):
        from .formulas import rbf_svr_predict
        return rbf_svr_predict(features, self.gamma, self.rho, self.vectors)
