"""
국토교통부 법정동 CSV -> JSON(locations.json) 변환기

적용:
- 말소/삭제/폐지 일자 있는 행 제외
- '리' 단위 제거(읍/면/동이 비면 스킵)
- 동일 시/군/구 내 '동명' 중복 제거(동명이 여러 코드로 중복되면 번호가 작은 코드 1개만 채택)
- 출력 JSON: (루트)/data/locations.json + (루트)/modelproject/data/locations.json

출력 스키마 예:
{
  "hierarchy": {
    "서울특별시": {
      "종로구": [
        {"district": "가회동", "code": "1111010100"},
        ...
      ],
      ...
    },
    ...
  },
  "index": [
    {"province": "서울특별시", "city": "종로구", "district": "가회동", "code": "1111010100"},
    ...
  ]
}
"""

from pathlib import Path
import csv, json
from collections import defaultdict

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

# 출력 대상(로컬/배포 둘 다 반영)
OUTPUTS = [
    BASE_DIR / "data" / "locations.json",                  # (루트)/data/locations.json
    BASE_DIR / "modelproject" / "data" / "locations.json", # modelproject/modelproject/data/locations.json
]

# CSV 검색(파일명 조금 달라도 찾게)
def find_csv_path() -> Path:
    candidates = [
        DATA_DIR / "국토교통부_전국 법정동_20250415.csv",
        DATA_DIR / "국토교통부_전국_법정동_20250415.csv",
    ] + list(DATA_DIR.glob("국토교통부*법정동*2025*.csv")) + list(DATA_DIR.glob("국토교통부*법정동*.csv"))
    for p in candidates:
        if p.exists():
            return p
    raise FileNotFoundError(f"CSV가 없습니다: {DATA_DIR}/(국토교통부*법정동*.csv)")

# 헤더 alias
ALIAS = {
    "법정동코드": ["법정동코드"],
    "시도명":    ["시도명", "시도"],
    "시군구명":  ["시군구명", "시군구"],
    "읍면동명":  ["읍면동명", "읍면동"],
    "리명":      ["리명", "리"],
    "말소일자":  ["말소일자", "삭제일자", "폐지일자"],
}

def get(row, key):
    for cand in ALIAS[key]:
        if cand in row:
            return (row[cand] or "").strip()
    return ""

def is_deleted(row):
    for cand in ALIAS["말소일자"]:
        if cand in row and (row[cand] or "").strip():
            return True
    return False

def norm_code(code: str) -> str:
    """
    법정동코드는 보통 10자리. 혹시 공백/하이픈 등 섞여오면 정리.
    """
    c = "".join(ch for ch in str(code) if ch.isdigit())
    return c.zfill(10)[:10] if c else ""

def open_csv(path: Path):
    # 인코딩 자동 감지: BOM → UTF-8 → CP949
    for enc in ("utf-8-sig", "utf-8", "cp949"):
        try:
            f = open(path, "r", encoding=enc, newline="")
            _ = f.read(2048); f.seek(0)
            print(f"[INFO] CSV encoding detected: {enc}")
            return f
        except UnicodeDecodeError:
            continue
    return open(path, "r", newline="")

def main():
    csv_path = find_csv_path()

    # data[시도][시군구] -> list[{"district": str, "code": str}]
    data = defaultdict(lambda: defaultdict(list))
    # seen[시도][시군구][동명] -> 채택한 code (번호가 작은 걸 유지)
    seen = defaultdict(lambda: defaultdict(dict))
    # index = []  # 평탄화 인덱스

    with open_csv(csv_path) as f:
        sample = f.read(2048); f.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample)
        except csv.Error:
            dialect = csv.excel
        reader = csv.DictReader(f, dialect=dialect)

        for r in reader:
            if is_deleted(r):
                continue

            code     = norm_code(get(r, "법정동코드"))
            province = get(r, "시도명")
            city     = get(r, "시군구명")
            district = get(r, "읍면동명")
            # '리'는 사용하지 않음: 읍/면/동이 비면 스킵
            if not (province and city and district):
                continue
            if not code:
                # 코드가 비면 스킵(원하면 나중에 None으로 채우는 로직으로 바꿔도 됨)
                continue

            chosen = seen[province][city].get(district)
            if chosen is None or code < chosen:
                # 더 작은 코드를 채택(동명이 여러 코드로 중복일 때 일관성 유지)
                seen[province][city][district] = code

        # seen을 data/index로 변환
        for province, cities in seen.items():
            for city, dmap in cities.items():
                for district, code in dmap.items():
                    data[province][city].append({"district": district, "code": code})
                    #index.append({"province": province, "city": city, "district": district, "code": code})

    # 보기 좋게 정렬
    for prov in data.values():
        for c, lst in list(prov.items()):
            prov[c] = sorted(lst, key=lambda x: (x["district"], x["code"]))
    # index.sort(key=lambda x: (x["province"], x["city"], x["district"], x["code"]))

    payload = {"hierarchy": data 
               # "index": index
               }

    # 두 군데 모두 저장
    for out_path in OUTPUTS:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with out_path.open("w", encoding="utf-8") as out:
            json.dump(payload, out, ensure_ascii=False, indent=2)
        print(f"[OK] JSON 파일 생성: {out_path}")

if __name__ == "__main__":
    main()
