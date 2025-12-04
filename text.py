import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl

# --- 폰트 설정 (한글 깨짐 방지) ---
mpl.rc('font', family='Malgun Gothic') 
plt.rcParams['axes.unicode_minus'] = False 

# --- 설정 (파일 및 컬럼 정보) ---
FILE_PATH = 'end_list.csv'  # test.py와 같은 폴더에 있으므로 파일 이름만 사용

# 실제 컬럼 이름으로 설정합니다.
CATEGORY_COL = 'VISIT_AREA_NM'  # 막대 그래프의 그룹 기준 (방문 지역)
GROUP_COL = 'TRAVEL_PERSONA'    # 그룹 비교 기준 (여행 페르소나)
VALUE_COL = 'DGSTFN'            # 만족도/평점 등 숫자 값 (꺾은선 그래프 값)


def create_travel_charts_from_csv(file_path, cat_col, group_col, value_col):
    """CSV 파일을 읽어와 여행 데이터를 기반으로 막대그래프와 꺾은선 그래프를 생성합니다."""
    
    # 1. 파일 불러오기 및 인코딩 처리
    try:
        try:
            df = pd.read_csv(file_path, encoding='utf-8')
        except UnicodeDecodeError:
            df = pd.read_csv(file_path, encoding='cp949')

    except FileNotFoundError:
        print(f" 오류: 지정된 파일 '{file_path}'을(를) 찾을 수 없습니다. 경로를 확인하세요.")
        return
    
    # 2. 데이터 확인 및 준비
    required_cols = [cat_col, group_col, value_col]
    if not all(col in df.columns for col in required_cols):
        print(f" 오류: 필수 컬럼 ({required_cols}) 중 일부가 데이터에 없습니다. 현재 컬럼: {list(df.columns)}")
        return

    # DGSTFN(만족도)을 숫자형 데이터로 변환하고 결측치를 0으로 채움
    df[value_col] = pd.to_numeric(df[value_col], errors='coerce').fillna(0)
    
    # ----------------------------------------------
    # --- 3. 막대 그래프: Top 3 방문 지역별 횟수 (빈도 분석) ---
    # ----------------------------------------------
    # 방문 지역별 횟수를 계산하여 DataFrame 생성 (가장 흔한 3개만 추출)
    visit_counts = df[cat_col].value_counts().nlargest(3).reset_index()
    visit_counts.columns = [cat_col, 'Count']
    
    plt.figure(figsize=(8, 5)) 
    plt.bar(visit_counts[cat_col], visit_counts['Count'], color='#007BFF', label='방문 횟수')
    
    plt.title(f'Top 3 방문 지역별 빈도수 ({cat_col})', fontsize=16)
    plt.xlabel(cat_col, fontsize=14)
    plt.ylabel('방문 횟수 (Count)', fontsize=14)
    plt.xticks(rotation=0) # 3개 항목이므로 회전 제거
    plt.legend(loc='upper right', fontsize=12) # UserWarning 해결
    plt.tight_layout() 
    plt.grid(axis='y', linestyle='--', alpha=0.6)
    plt.show()
    
    # --- 4. 두 번째 그래프: Top 10 여행 페르소나별 빈도수 (가로 막대 그래프) ---

    # 그룹별 데이터 개수(빈도수) 계산 (.size() 사용)
    persona_count = df.groupby(group_col).size().reset_index(name='Count')
    
    # 빈도수가 높은 Top 10 항목 추출
    persona_top10 = persona_count.nlargest(10, columns='Count')

    # 빈도수가 낮은 순서부터 표시되도록 정렬 (그래프에서 위로 갈수록 많아지게)
    persona_top10 = persona_top10.sort_values(by='Count', ascending=True)

    plt.figure(figsize=(10, 8))
    
    # 가로 막대 그래프 생성 (X축 값으로 'Count' 컬럼을 사용)
    plt.barh(persona_top10[group_col], persona_top10['Count'], color='red') 
    
    plt.title(f'Top 10 {group_col}별 데이터 빈도수 비교', fontsize=18)
    plt.xlabel('데이터 개수 (Count)', fontsize=14)
    plt.ylabel(group_col, fontsize=14)
    plt.tight_layout()
    plt.grid(axis='x', linestyle=':', alpha=0.7) 
    plt.show()
    


# --- 함수 실행 ---
# 'end_list.csv' 파일이 test.py와 같은 폴더에 있어야 합니다.
create_travel_charts_from_csv(FILE_PATH, CATEGORY_COL, GROUP_COL, VALUE_COL)