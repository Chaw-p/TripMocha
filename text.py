import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D 
from matplotlib.patches import Patch

# --- 1. 데이터 로드 및 전처리 ---
# ⚠️ 파일 로드 안전성 확보: 두 가지 경로를 모두 시도합니다.
try:
    df = pd.read_csv("end_list.csv", encoding='latin-1')
    print("✅ 데이터 로드 성공: 'end_list.csv'로 로드됨.")
except Exception:
    try:
        df = pd.read_csv("end_list.csv", encoding='latin-1')
        print("✅ 데이터 로드 성공: 'end_list.csv' 경로로 로드됨.")
    except Exception as e:
        print(f"❌ 오류: 파일 로드 실패. 모든 경로 시도 실패: {e}")
        exit()

# ⚠️ 수정: 범주형 코드를 문자열로 변환하여 그룹화 에러를 방지합니다.
df['VISIT_AREA_TYPE_CD'] = df['VISIT_AREA_TYPE_CD'].astype(str)
df['TRAVEL_MISSION_INT'] = df['TRAVEL_MISSION_INT'].astype(str)


# 변수 정의
cat_cols = ['VISIT_AREA_TYPE_CD', 'TRAVEL_STATUS_ACCOMPANY', 'TRAVEL_MISSION_INT', 'VISIT_AREA_NM']
plot_details = {
    'VISIT_AREA_TYPE_CD': '방문지 유형',
    'TRAVEL_STATUS_ACCOMPANY': '동반자',
    'TRAVEL_MISSION_INT': '여행 목적',
    'VISIT_AREA_NM': '방문 지역명'
}

# --- 2. 변수별 DGSTFN 평균 계산 및 영향력(변동폭) 계산 ---

influence_data = {} # 변수별 영향력(변동폭) 저장
mean_data = {}      # 강조 그래프를 위한 상세 평균 저장
max_range = 0
most_influential_var = ''

for col, title in plot_details.items():
    if col == 'VISIT_AREA_NM':
        top_10_areas = df[col].value_counts().head(10).index
        temp_df = df[df[col].isin(top_10_areas)]
        avg_df = temp_df.groupby(col)['DGSTFN'].mean().reset_index()
    else:
        avg_df = df.groupby(col)['DGSTFN'].mean().reset_index()
    
    avg_df.columns = ['Category', 'Mean_DGSTFN']
    mean_data[col] = avg_df

    # 영향력(변동폭) 계산: 최대 평균과 최소 평균의 차이
    current_range = avg_df['Mean_DGSTFN'].max() - avg_df['Mean_DGSTFN'].min()
    
    # 변수별 영향력 데이터프레임 구성
    influence_data[col] = {'Variable_Name': title, 'Influence_Range': current_range}

    if current_range > max_range:
        max_range = current_range
        most_influential_var = col

# 통합 비교 그래프를 위한 DataFrame 생성
df_influence = pd.DataFrame(list(influence_data.values()))
df_influence = df_influence.sort_values(by='Influence_Range', ascending=False)
print(f"가장 영향력이 큰 변수: {plot_details[most_influential_var]} (변동폭: {max_range:.4f})")

# --- 3. Matplotlib 설정 및 2개 그래프 그리기 (2행 1열) ---

plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False 

# 2행 1열 그리드 생성 (총 2개의 그래프)
fig, axes = plt.subplots(nrows=2, ncols=1, figsize=(12, 12), 
                         gridspec_kw={'height_ratios': [1, 1.5]}, sharex=False) 

# --- 3.1 첫 번째 그래프: 4개 변수 영향력 통합 비교 (Summary Chart) ---

ax1 = axes[0]
bars = ax1.bar(df_influence['Variable_Name'], df_influence['Influence_Range'], 
               color=['coral' if name == plot_details[most_influential_var] else 'skyblue' for name in df_influence['Variable_Name']])

ax1.set_ylabel('만족도 평균 변동폭 (영향력 크기)', fontsize=12)
ax1.set_xlabel('변수', fontsize=12)
ax1.set_title('만족도에 대한 영향력 비교', fontsize=16, pad=20)
ax1.grid(axis='y', linestyle='--', alpha=0.7)
ax1.tick_params(axis='x', rotation=0)

# 막대 위에 변동폭 값 표시
for bar in bars:
    ax1.text(bar.get_x() + bar.get_width() / 2., bar.get_height() + 0.01,
             f'{bar.get_height():.3f}', ha='center', va='bottom', fontsize=9, color='black')


# --- 3.2 두 번째 그래프: 최대 영향력 변수 상세 분포 강조 (Emphasized Chart) ---

ax2 = axes[1]
empha_data = mean_data[most_influential_var]
empha_data = empha_data.sort_values(by='Mean_DGSTFN', ascending=False)

# 세로 막대 그래프 그리기
bars = ax2.bar(empha_data['Category'], empha_data['Mean_DGSTFN'], color='darkred')

ax2.set_ylabel('평균 만족도', fontsize=14) 
ax2.set_ylim(df['DGSTFN'].min() - 0.1, df['DGSTFN'].max() + 0.1) # Y축 범위 통일

empha_title = plot_details[most_influential_var]
ax2.set_xlabel(f'{empha_title} 카테고리', fontsize=14, labelpad=15)
ax2.set_title(f"최대 영향력 변수 강조: {empha_title}별 만족도 상세 분포", 
              fontsize=18, color='darkred', pad=20)

# X축 레이블 45도 회전
ax2.tick_params(axis='x', rotation=45, labelsize=12)

# 막대 위에 평균 값 표시
for bar in bars:
    height = bar.get_height()
    ax2.text(bar.get_x() + bar.get_width() / 2., height + 0.05,
             f'{height:.2f}',
             ha='center', va='bottom', fontsize=10)

# 레이아웃 조정 및 전체 제목 설정
plt.tight_layout(rect=[0, 0.03, 1, 0.95])
fig.suptitle('DGSTFN(만족도) 영향력 요약 및 상세 분석 ', fontsize=22, y=0.98)

# 파일 저장
plt.savefig('테스트1.png')
print("\n✅ 시각화가 완료되었습니다. '테스트1.png' 파일이 생성되었습니다.")