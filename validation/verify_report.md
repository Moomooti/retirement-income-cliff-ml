# 모델 설계도 검정표

검정 항목 26개 · 통과 26 · 불일치 0

| 단계 | 주장 | 결과 | 근거 |
|---|---|---|---|
| 원자료 | 국가 패널 6개 | 통과 | 원자료 폴더 8개, 변환 스크립트 6개: b_khp.py, b_klips.py, b_klosa.py, b_koweps.py, b_kreis.py, b_nastab.py |
| 공통 스키마 | 6개 패널을 같은 열 이름의 표로 변환 | 통과 | 6개 p_패널.pkl에 공통으로 있는 열 19개 (예: panel, pid, svy_year, age, hhsize, hhinc, employed) |
| 공통 스키마 | 가처분소득(hhdin)은 3개 패널에만 있음 | 통과 | 50~69세 행 중 가처분소득이 채워진 비율(%): 복지 100, 재정 98, 국민노후 70, 노동 0, 의료 0, 고령화 0 |
| 공통 스키마 | 퇴직·개인연금은 복지패널에만 있음 → 서비스 모델(21문항)은 복지패널로 학습 | 통과 | 복지패널에만 채워진 열: x_retire_pension, x_private_pension (부동산은 복지 100%·국민노후 60%) |
| 공통 스키마 | 모든 패널에 공통인 입력 17개(COMMON) + 패널별 추가 입력 | 통과 | common_ml.COMMON = log_ratio, age, age_to_60, age_to_nps, female, edu3, married, hhsize, employed, d_log_ratio_2y, d_log_ratio_4y, vol_hist, min_ratio_hist, ever_below_hist, lost_job_2y, hh_change_2y, employed_l2 |
| 보정 | CPI(2023년 가격) 실질화 · √가구원 균등화 | 통과 | label_v3.py: defl = cpi[2023]/cpi, inc/np.sqrt(hhsize)*defl |
| 보정 | 기준선 2종: 가처분 3개 패널 = 복지패널 가처분 중위 50%, 경상 3개 = 경상 중위 50% | 통과 | label_v3.py: NODIS=노동·의료·고령화 → poverty_line.csv(경상), 나머지 → 가처분 dline |
| 라벨링 | y = t+2~t+4 중 2번 이상 기준선 아래 (격년은 2번 중 2번) | 통과 | label_v3.label() |
| 라벨링 | 7개 과제(6개 패널 + 국민노후 필요생활비) | 통과 | KOWEPS:가처분 상대빈곤(중위 50%) / NaSTaB:가처분 상대빈곤(중위 50%) / KReIS:가처분 상대빈곤(중위 50%) / KLIPS:경상 상대빈곤(재현용) / KHP:경상 상대빈곤(이식 검증용) / KLoSA:경상 상대빈곤(이식 검증용) / KReIS:필요 최소생활비 기준선 |
| 분할 | 패널마다 최근 2개 조사연도 = 시험, 학습 = 시험 시작 4년 전까지 | 통과 | 시험 연도: KOWEPS 2020·2021, NaSTaB 2019·2020, KReIS 2017·2019, KLIPS 2019·2020, KHP 2020·2021, KLoSA 2016·2018, KReIS 2017·2019 |
| 분할 | 학습 103,864행 · 시험 31,544행 (7개 과제 합) | 통과 | label_v3.csv 합계 학습 103,864 · 시험 31,544 |
| 기준선 | B0 = 지금 소득만, B1 = 지금 소득·나이·취업 로지스틱(계산기형) | 통과 | v3_full.py: calc = LogisticRegression on [소득, age, employed] |
| 모델 비교 | 15종 비교 (7개 과제 모두 · 보고서 표는 판정 3 + 필요생활비 + 노동 5개) | 통과 | 모델 15종 / 과제: KHP_r, KLIPS_r, KLoSA_r, KOWEPS_r, KReIS_r, KReIS_rn, NaSTaB_r |
| 모델 비교 | LightGBM 2×2 격자(num_leaves 15/31 × min_child 40/150) + 조기 종료 | 통과 | v3_full.tune() |
| 모델 비교 | 로지스틱 = 중앙값 대체 + 결측 표시 + 표준화(L2) | 통과 | v3_full.prep() |
| 최종 모델 | 최종 = LightGBM 순위 + 로지스틱 순위 (패널마다 따로) | 통과 | v3_full.py 113행 |
| 최종 모델 | 시험 AUC (복지 0.870 등) | 통과 | v3_out zoo: KOWEPS_r 0.87, NaSTaB_r 0.794, KReIS_r 0.746, KReIS_rn 0.796, KLIPS_r 0.807, KHP_r 0.773, KLoSA_r 0.774 |
| 설명 | 이유 = LightGBM pred_contrib(TreeSHAP) | 통과 | m_abc.py · spkg_predict.py |
| 보류 | 판단 보류 = 분할 컨포멀 α=0.10 | 통과 | m_abc.py q1/q0 · make_spkg.py |
| 평가 | 패널별 DeLong → 판정 3개 랜덤효과 메타분석 +0.064 | 통과 | v3_out meta 최종−지금소득 0.064 [0.053, 0.075] |
| 검증 | 통합 모델(판정 3 + 노동) 학습곡선 691 → 69,147행 | 통과 | 학습 행 691→69,147, 시험 AUC 0.750→0.804 |
| 검증 | 라벨 셔플 평균 AUC ≈ 0.49 | 통과 | 셔플 5회 평균 0.486 |
| 검증 | 이식: 공통 입력 모델을 6개 패널끼리 교차 적용 | 통과 | v3_full.py 6. 이식 |
| 서비스 | 서비스 모델 = 복지패널 21문항(S20 30개 변수), 시험 AUC 0.868 | 통과 | s_out S20: 변수 30개, AUC 0.8684, 전체 입력 대비 손실 0.0012 |
| 서비스 | 기준선 아래 B20(사전 기준 통과) | 통과 | b_out: AUC 0.813 vs 지금 소득 0.690 |
| 서비스 | FastAPI /predict, 입력 저장 안 함 | 통과 | back_E backend/app/main.py |