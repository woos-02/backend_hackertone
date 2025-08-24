"""
전국 데이터를 csv 파일로 받아 json으로 반환하는 파일 생성
modelproject/modelproject/data/locations.json 파일로 생성됨
"""

import csv
import json
import os

# 다운로드한 CSV 파일 경로
csv_file_path = os.path.join(
    os.path.expanduser('~'),
    'Downloads',
    '국토교통부_전국 법정동_20250415.csv'
)

# JSON으로 저장할 파일 경로
# 현재 위치에 있는 data 폴더 아래에 locations.json 파일이 생성됩니다.
json_file_path = os.path.join('modelproject', 'data', 'locations.json')

data = {}

try:
    with open(csv_file_path, 'r', encoding='utf-8') as csv_file:
        reader = csv.reader(csv_file)

        header = next(reader)
        header = [h.replace('\ufeff', '').strip() for h in header]  # BOM/공백 정리
        delete_col_idx = None
        for key in ('삭제일자', '폐지일자', '말소일자'):
            if key in header:
                delete_col_idx = header.index(key)
                break
        for row in reader:
            if len(row) < 4:
                continue
            
            if delete_col_idx is not None and delete_col_idx < len(row):
                if row[delete_col_idx].strip():
                    continue

            # 구글 스프레드시트의 A, B, C 열 순서에 맞춰 인덱스를 1,2,3 으로 설정
            province = row[1].strip() # A열: 시/도
            city = row[2].strip()     # B열: 시/군/구
            district = row[3].strip() # C열: 읍/면/동
            
            # 읍/면/동 값이 비어있거나 소계 등 불필요한 값은 건너뛰기
            if not district or '소계' in district:
                continue
            
            # 시/도 기준으로 딕셔너리에 추가
            if province not in data:
                data[province] = {}

            # 시/군/구 기준으로 딕셔너리에 추가
            if city not in data[province]:
                data[province][city] = []

            # 읍/면/동을 리스트에 추가
            if district not in data[province][city]:
                data[province][city].append(district)

except FileNotFoundError:
    print(f"오류: 파일을 찾을 수 없습니다. 경로를 다시 확인해 주세요: {csv_file_path}")
except UnicodeDecodeError:
    print("오류: 인코딩 문제! `cp949` 대신 `utf-8`이나 다른 인코딩을 시도해 보세요.")

with open(json_file_path, 'w', encoding='utf-8') as json_file:
    json.dump(data, json_file, ensure_ascii=False, indent=2)

print(f"JSON 파일이 {json_file_path}에 성공적으로 생성되었습니다.")