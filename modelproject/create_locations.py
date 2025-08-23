"""
국토교통부 '전국 법정동' CSV를 읽어
프론트 셀렉트박스(시/도 → 시/군/구 → 읍/면/동) 구조에 딱 맞는 JSON으로 변환합니다.

출력 예:
{
  "서울특별시": {
    "종로구": [
      {"name": "청운동", "code": "1111010100"},
      {"name": "신교동", "code": "1111010200"}
    ],
    "중구": [ ... ]
  },
  "부산광역시": { ... }
}
"""
from __future__ import annotations
import argparse, csv, json, os
from pathlib import Path
from typing import Dict, List, Tuple

def read_csv_rows(path: Path) -> List[dict]:
    for enc in ("utf-8", "cp949"):
        try:
            with path.open("r", encoding=enc, newline="") as f:
                return list(csv.DictReader(f))
        except UnicodeDecodeError:
            continue
    raise UnicodeDecodeError("csv", b"", 0, 1, "encoding failed")

def normalize_and_filter(rows: List[dict]) -> List[Tuple[str,str,str,str]]:
    out: List[Tuple[str,str,str,str]] = []
    for r in rows:
        prov = (r.get("시도명") or "").strip()
        city = (r.get("시군구명") or "").strip()
        dong = (r.get("읍면동명") or "").strip()
        ri   = (r.get("리명") or "").strip()
        code = (r.get("법정동코드") or "").strip()
        deleted = (r.get("삭제일자") or "").strip()

        if deleted: continue      # 폐지 제외
        if ri:      continue      # '리' 제외
        if not dong: continue     # 요약행 제외
        if "소계" in dong: continue
        if not prov or not city or not code: continue

        out.append((prov, city, dong, code))
    return out

def build_nested(rows: List[Tuple[str,str,str,str]]) -> Dict[str, Dict[str, List[dict]]]:
    nested: Dict[str, Dict[str, List[dict]]] = {}
    rows_sorted = sorted(rows, key=lambda x: (x[0], x[1], x[2]))
    seen = set()
    for prov, city, dong, code in rows_sorted:
        key = (prov, city, dong)
        if key in seen: 
            continue
        seen.add(key)
        nested.setdefault(prov, {})
        nested[prov].setdefault(city, [])
        nested[prov][city].append({"name": dong, "code": str(code)})
    for prov in nested:
        for city in nested[prov]:
            nested[prov][city].sort(key=lambda d: d["name"])
    return nested

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--csv",
        default=os.path.join(os.path.expanduser("~"), "Downloads", "국토교통부_전국 법정동_20250415.csv"),
        help="국토교통부 CSV 파일 경로"
    )
    parser.add_argument(
        "--out",
        default=None,
        help="출력 JSON 경로(기본: 프로젝트 루트/modelproject/data/locations.json)"
    )
    args = parser.parse_args()

    csv_path = Path(args.csv).resolve()
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV 파일을 찾을 수 없습니다: {csv_path}")

    base = Path(__file__).resolve().parent
    out_path = Path(args.out).resolve() if args.out else \
        (base / "modelproject" / "data" / "locations.json" if (base / "modelproject").exists()
         else base / "data" / "locations.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    nested = build_nested(normalize_and_filter(read_csv_rows(csv_path)))
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(nested, f, ensure_ascii=False, indent=2)

    np = len(nested)
    nc = sum(len(nested[p]) for p in nested)
    nd = sum(len(nested[p][c]) for p in nested for c in nested[p])
    print(f"[완료] {out_path} 저장")
    print(f"  - 시/도: {np}개, 시/군/구: {nc}개, 읍/면/동: {nd}개")

if __name__ == "__main__":
    main()

