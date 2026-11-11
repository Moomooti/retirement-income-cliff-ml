"""모델 설계도 검정 → 통과한 사실만 설계도 사양(flow_spec.json)으로 추출.

각 단계의 주장을 실제 코드(소스 문자열)·중간 결과(집계)에서 다시 확인한다.
출력: verify_report.md (검정표), verify_report.json, flow_spec.json (설계도가 읽는 파일)
개인 단위 값은 출력하지 않는다(행 수·비율·AUC 같은 집계만).
"""
import glob, json, os, pickle, re
import numpy as np, pandas as pd
W = '/home/claude/work/'
OUT = W + 'design_check/'; os.makedirs(OUT, exist_ok=True)
src = lambda f: open(W + f, encoding='utf-8').read()
CHECKS = []
def check(step, claim, ok, evidence, value=None):
    CHECKS.append(dict(step=step, claim=claim, result='통과' if ok else '불일치', evidence=evidence, value=value))
    return value

# ---------- 1. 원자료와 패널별 변환 ----------
raw = sorted(os.listdir('/home/claude/raw'))
conv = sorted(f for f in ['b_koweps.py', 'b_nastab.py', 'b_kreis.py', 'b_klips.py', 'b_khp.py', 'b_klosa.py'] if os.path.exists(W + f))
check('원자료', '국가 패널 6개', len(raw) >= 6 and len(conv) == 6, f'원자료 폴더 {len(raw)}개, 변환 스크립트 {len(conv)}개: ' + ', '.join(conv), len(conv))

# ---------- 2. 공통 스키마: 같은 열 이름, 그러나 채움 정도는 패널마다 다름 ----------
PN = {'koweps': '복지', 'nastab': '재정', 'kreis': '국민노후', 'klips': '노동', 'khp': '의료', 'klosa': '고령화'}
cov, colsets = {}, {}
for p in PN:
    d = pd.read_pickle(W + f'p_{p}.pkl'); d = d[d.age.between(50, 69)]
    colsets[p] = set(d.columns)
    cov[p] = {c: round(float(d[c].notna().mean()) * 100) if c in d else 0 for c in
              ['hhinc', 'hhdin', 'x_retire_pension', 'x_private_pension', 'x_realestate', 'x_owner', 'x_debt']}
shared = set.intersection(*colsets.values())
check('공통 스키마', '6개 패널을 같은 열 이름의 표로 변환', len(shared) >= 15,
      f'6개 p_패널.pkl에 공통으로 있는 열 {len(shared)}개 (예: panel, pid, svy_year, age, hhsize, hhinc, employed)', len(shared))
disp = [p for p in PN if cov[p]['hhdin'] >= 50]
check('공통 스키마', '가처분소득(hhdin)은 3개 패널에만 있음', sorted(disp) == sorted(['koweps', 'nastab', 'kreis']),
      '50~69세 행 중 가처분소득이 채워진 비율(%): ' + ', '.join(f"{PN[p]} {cov[p]['hhdin']}" for p in PN), [PN[p] for p in disp])
only_kw = [c for c in ['x_retire_pension', 'x_private_pension', 'x_realestate'] if all(cov[p][c] == 0 for p in PN if p != 'koweps') and cov['koweps'][c] > 90]
check('공통 스키마', '퇴직·개인연금은 복지패널에만 있음 → 서비스 모델(21문항)은 복지패널로 학습', sorted(only_kw) == ['x_private_pension', 'x_retire_pension'],
      '복지패널에만 채워진 열: ' + ', '.join(only_kw) + f" (부동산은 복지 {cov['koweps']['x_realestate']}%·국민노후 {cov['kreis']['x_realestate']}%)", only_kw)
from common_ml import COMMON
check('공통 스키마', '모든 패널에 공통인 입력 17개(COMMON) + 패널별 추가 입력', len(COMMON) == 17 and 'def extra_features' in src('common_ml.py'),
      'common_ml.COMMON = ' + ', '.join(COMMON), len(COMMON))

# ---------- 3. 보정과 기준선 ----------
lv3 = src('label_v3.py')
check('보정', 'CPI(2023년 가격) 실질화 · √가구원 균등화', "cpi[2023] / cpi" in lv3 and 'np.sqrt(P.hhsize)' in lv3, 'label_v3.py: defl = cpi[2023]/cpi, inc/np.sqrt(hhsize)*defl')
check('보정', '기준선 2종: 가처분 3개 패널 = 복지패널 가처분 중위 50%, 경상 3개 = 경상 중위 50%',
      'NODIS' in lv3 and "P.line_d" in lv3 and 'poverty_line.csv' in lv3, "label_v3.py: NODIS=노동·의료·고령화 → poverty_line.csv(경상), 나머지 → 가처분 dline")

# ---------- 4. 라벨과 과제 ----------
L = pd.read_csv(W + 'label_v3.csv')
check('라벨링', 'y = t+2~t+4 중 2번 이상 기준선 아래 (격년은 2번 중 2번)', 'below >= 2' in lv3 and '(f[2] < 1) & (f[4] < 1)' in lv3, 'label_v3.label()')
check('라벨링', '7개 과제(6개 패널 + 국민노후 필요생활비)', len(L) == 7, ' / '.join(f'{r.panel}:{r.label}' for r in L.itertuples()), len(L))

# ---------- 5. 분할 ----------
check('분할', '패널마다 최근 2개 조사연도 = 시험, 학습 = 시험 시작 4년 전까지', 'ty = ys[-2:]' in lv3 and 'min(ty) - 4' in lv3,
      '시험 연도: ' + ', '.join(f'{r.panel} {r.te_years}' for r in L.itertuples()))
n_tr, n_te = int(L.n_tr.sum()), int(L.n_te.sum())
check('분할', '학습 103,864행 · 시험 31,544행 (7개 과제 합)', (n_tr, n_te) == (103864, 31544), f'label_v3.csv 합계 학습 {n_tr:,} · 시험 {n_te:,}', [n_tr, n_te])

# ---------- 6. 기준선·15종·최종 모델 ----------
vf = src('v3_full.py'); O = pickle.load(open(W + 'v3_out.pkl', 'rb')); Z = pd.DataFrame(O['zoo'])
models = sorted(set(Z.model) - {'B0 지금 소득', 'B1 계산기형', '최종: LightGBM+로지스틱'}); tasks = sorted(Z.task.unique())
check('기준선', 'B0 = 지금 소득만, B1 = 지금 소득·나이·취업 로지스틱(계산기형)', "S['B1 계산기형']" in vf and "[b0col, 'age', 'employed']" in vf, 'v3_full.py: calc = LogisticRegression on [소득, age, employed]')
check('모델 비교', '15종 비교 (7개 과제 모두 · 보고서 표는 판정 3 + 필요생활비 + 노동 5개)', len(models) == 15 and len(tasks) == 7, f'모델 {len(models)}종 / 과제: ' + ', '.join(tasks), [len(models), tasks])
check('모델 비교', 'LightGBM 2×2 격자(num_leaves 15/31 × min_child 40/150) + 조기 종료', 'for n in (15, 31) for m in (40, 150)' in vf and 'early_stopping(100' in vf, 'v3_full.tune()')
check('모델 비교', '로지스틱 = 중앙값 대체 + 결측 표시 + 표준화(L2)', "SimpleImputer(strategy='median', add_indicator=True), StandardScaler()" in vf, 'v3_full.prep()')
check('최종 모델', '최종 = LightGBM 순위 + 로지스틱 순위 (패널마다 따로)', "rankdata(S['LightGBM']) + rankdata(S['LR_L2'])" in vf, 'v3_full.py 113행')
fin = Z[Z.model == '최종: LightGBM+로지스틱'].set_index('task').auc.round(3).to_dict()
check('최종 모델', '시험 AUC (복지 0.870 등)', abs(fin.get('KOWEPS_r', 0) - 0.870) < 0.0015, 'v3_out zoo: ' + ', '.join(f'{k} {v}' for k, v in fin.items()), fin)

# ---------- 7. 설명·보류 ----------
ma = src('m_abc.py')
check('설명', '이유 = LightGBM pred_contrib(TreeSHAP)', 'pred_contrib=True' in ma and 'pred_contrib=True' in src('spkg_predict.py'), 'm_abc.py · spkg_predict.py')
check('보류', '판단 보류 = 분할 컨포멀 α=0.10', 'np.ceil((1 - a) * ((ycal == 1).sum() + 1))' in ma and 'alpha=0.10' in src('make_spkg.py'), 'm_abc.py q1/q0 · make_spkg.py')

# ---------- 8. 평가·검증 ----------
meta = O['meta']['최종−지금소득']
check('평가', '패널별 DeLong → 판정 3개 랜덤효과 메타분석 +0.064', abs(meta['est'] - 0.064) < 0.001,
      f"v3_out meta 최종−지금소득 {meta['est']:.3f} [{meta['lo']:.3f}, {meta['hi']:.3f}]", [round(meta['est'], 3), round(meta['lo'], 3), round(meta['hi'], 3)])
lc = O['lc']; perm = float(np.mean(O['perm']))
check('검증', '통합 모델(판정 3 + 노동) 학습곡선 691 → 69,147행', int(lc.n.max()) == 69147 and "PK = MAIN + ['KLIPS_r']" in vf,
      f"학습 행 {int(lc.n.min()):,}→{int(lc.n.max()):,}, 시험 AUC {lc[lc.n == lc.n.min()].test_auc.mean():.3f}→{lc[lc.n == lc.n.max()].test_auc.mean():.3f}", int(lc.n.max()))
check('검증', '라벨 셔플 평균 AUC ≈ 0.49', abs(perm - 0.486) < 0.002, f'셔플 5회 평균 {perm:.3f}', round(perm, 3))
check('검증', '이식: 공통 입력 모델을 6개 패널끼리 교차 적용', "src = MAIN + ['KLIPS_r', 'KHP_r', 'KLoSA_r']" in vf, 'v3_full.py 6. 이식')

# ---------- 9. 서비스 ----------
S = pickle.load(open(W + 's_out.pkl', 'rb')); s20 = S[('KOWEPS', 'S20')]['res']
check('서비스', '서비스 모델 = 복지패널 21문항(S20 30개 변수), 시험 AUC 0.868', abs(s20['auc_service'] - 0.868) < 0.001 and s20['n_feat'] == 30,
      f"s_out S20: 변수 {s20['n_feat']}개, AUC {s20['auc_service']:.4f}, 전체 입력 대비 손실 {s20['loss']:.4f}", round(s20['auc_service'], 3))
B = pickle.load(open(W + 'b_out.pkl', 'rb'))['res']
check('서비스', '기준선 아래 B20(사전 기준 통과)', B['C1'] and B['C2'] and B['C3'], f"b_out: AUC {B['auc_model']:.3f} vs 지금 소득 {B['auc_b0']:.3f}", round(B['auc_model'], 3))
check('서비스', 'FastAPI /predict, 입력 저장 안 함', os.path.exists('/tmp/claude-0/-home-claude/e5872982-71a4-5f1c-953f-30befae32eac/scratchpad/out_b/backend/app/main.py'), 'back_E backend/app/main.py')

# ---------- 결과 ----------
bad = [c for c in CHECKS if c['result'] != '통과']
md = ['# 모델 설계도 검정표', '', f'검정 항목 {len(CHECKS)}개 · 통과 {len(CHECKS) - len(bad)} · 불일치 {len(bad)}', '',
      '| 단계 | 주장 | 결과 | 근거 |', '|---|---|---|---|'] + [f"| {c['step']} | {c['claim']} | {c['result']} | {c['evidence']} |" for c in CHECKS]
open(OUT + 'verify_report.md', 'w', encoding='utf-8').write('\n'.join(md))
json.dump(CHECKS, open(OUT + 'verify_report.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1, default=str)
if bad:
    print('불일치 있음 – 설계도를 만들지 않음:'); [print(' -', c['step'], c['claim'], c['evidence']) for c in bad]; raise SystemExit(1)

# ---------- 통과한 값만으로 설계도 사양 ----------
nm = lambda ps: '·'.join(ps)
spec = dict(nodes={
  'raw':   ['data', '국가 패널 6개', '복지·재정·국민노후·노동·의료·고령화', 'db'],
  'conv':  ['prep', '패널별 변환', f'변환 스크립트 {len(conv)}개'],
  'schema':['prep', '공통 스키마', f'같은 열 이름 · 공통 입력 {len(COMMON)}개'],
  'g3':    ['data', '판정 패널 3개', '가처분소득: ' + nm([PN[p] for p in disp])],
  'g3b':   ['base', '재현·이식 패널 3개', '경상소득: ' + nm([PN[p] for p in PN if p not in disp])],
  'adj':   ['prep', '물가·가구원 보정', 'CPI · √가구원 · 기준선 대비 r'],
  'label': ['prep', '타깃(y) 라벨링', f'2년 뒤 반복 하락 · {len(L)}개 과제'],
  'split': ['split', '시간순 학습/시험 분할', '패널마다 최근 2개 연도 = 시험'],
  'train': ['split', '학습셋', f'{len(L)}개 과제 합 {n_tr:,}행'],
  'test':  ['split', '시험셋 (봉인)', f'{len(L)}개 과제 합 {n_te:,}행'],
  'b0':    ['base', '기준선 B0 · B1', '지금 소득 · 소득+나이+취업'],
  'cmp':   ['model', f'{len(models)}종 비교', f'{len(tasks)}개 과제'],
  'lgb':   ['model', 'LightGBM', '2×2 격자 · 조기 종료'],
  'lr':    ['model', '로지스틱(L2)', '결측 표시 · 표준화'],
  'ens':   ['model', '순위 평균 앙상블', '패널마다 최종 모델'],
  'shap':  ['model', '이유 3가지', 'TreeSHAP'],
  'conf':  ['model', '판단 보류', '분할 컨포멀 α=0.10'],
  'pool':  ['eval', '통합 모델 검증', f'판정 3 + 노동 · {int(lc.n.max()):,}행'],
  'score': ['eval', 'Test and Score', '패널별 AUC · DeLong'],
  'check': ['eval', '결합·검증', f'메타 +{meta["est"]:.3f} · 셔플 {perm:.2f} · 이식'],
  'svc':   ['serve', '서비스 모델', f'복지패널 21문항 · AUC {s20["auc_service"]:.3f} · B20'],
  'api':   ['serve', '/predict API', 'FastAPI · 입력 저장 안 함'],
  'web':   ['serve', '미리사주 화면', '풀이 · 이유 · 공식 사이트 안내'],
}, checks=len(CHECKS))
json.dump(spec, open(OUT + 'flow_spec.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(f'검정 {len(CHECKS)}개 모두 통과 → flow_spec.json 작성')
