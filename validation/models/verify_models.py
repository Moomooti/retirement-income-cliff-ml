"""모델별 상세 설계도 검정 → 통과하면 모델별 사양(models_spec.json) 작성.
코드(문자열)와 결과 파일(숫자)을 서로 맞춰 보고, 하나라도 어긋나면 사양을 쓰지 않는다.
출력: design_check/models_verify.md · models_verify.json · models_spec.json (집계만, 사람 단위 값 없음)"""
import numpy as np, pandas as pd, pickle, json, re, os, sys
from common_ml import COMMON, CATEG, W
OUT = W + 'design_check/'; os.makedirs(OUT, exist_ok=True)
src = {f: open(W + f, encoding='utf-8').read() for f in ['label_v3.py', 'common_ml.py', 'v3_full.py', 'm_abc.py', 's_model.py', 'b_model.py',
                                                       'make_spkg.py', 'spkg_predict.py', 'build_common.py']}
O = pd.read_pickle(W + 'v3_out.pkl'); AC = pd.read_pickle(W + 'mabc_out_AC.pkl'); S = pd.read_pickle(W + 's_out.pkl'); BO = pd.read_pickle(W + 'b_out.pkl')
PC = pd.read_pickle(W + 's_pathcheck.pkl'); L3 = pd.read_csv(W + 'label_v3.csv')
META = {t: json.load(open(W + f'spkg/mirisaju_model/model/{t}_meta.json', encoding='utf-8')) for t in ['S20', 'S21', 'B20']}
checks = []


def chk(model, step, claim, ok, ev):
    checks.append(dict(model=model, step=step, claim=claim, result='통과' if ok else '불일치', evidence=str(ev)))


def has(f, *subs):
    s = re.sub(r'\s+', ' ', src[f]); return all(re.sub(r'\s+', ' ', x) in s for x in subs)


# ---------------- 변수 이름표 (뜻은 변환 코드 주석·정의에서 옮김) ----------------
LAB = {
    'log_ratio': '지금 소득(경상 기준선 대비)', 'd_log_ratio_2y': '2년 사이 소득 변화', 'd_log_ratio_4y': '4년 사이 소득 변화',
    'vol_hist': '과거 소득 출렁임(t·t−2·t−4)', 'min_ratio_hist': '과거 3시점 중 최저 소득', 'ever_below_hist': '과거 기준선 아래 경험',
    'age': '나이', 'age_to_60': '60세까지 남은 기간', 'age_to_nps': '국민연금 개시까지 남은 기간', 'female': '성별', 'edu3': '학력',
    'married': '배우자', 'hhsize': '가구원 수', 'hh_change_2y': '2년 사이 가구원 변화', 'employed': '지금 일함', 'lost_job_2y': '2년 내 일 그만둠',
    'employed_l2': '2년 전 일함',
    'x_selfemp': '자영업', 'x_temp_daily': '임시·일용직', 'x_regular': '상용직', 'x_occ': '직업 대분류(범주)', 'employed_l1': '1년 전 일함',
    'x_own_earn_l2': '2년 전 본인 근로소득', 'x_earn_share': '가구소득 중 본인 근로소득 비중', 'x_retired': '은퇴 여부',
    'x_pension_recv': '공적연금 수령', 'x_pension_type': '공적연금 종류(범주)', 'x_private_pension': '개인연금', 'x_retire_pension': '퇴직연금',
    'x_pension_enrolled': '공적연금 가입', 'x_pension_amt_r': '연금 수령액(소득 대비)',
    'x_health_bad': '주관적 건강(나쁠수록 큼)', 'x_chronic': '만성질환', 'x_health_bad_l2': '2년 전 건강', 'x_health_bad_d2': '건강 변화(2년)',
    'x_mental_bad': '정신건강(나쁠수록 큼)', 'x_adl': '일상생활 제한(ADL)', 'x_iadl': '수단적 일상생활 제한(IADL)',
    'x_owner': '자가', 'x_fin_assets_r': '금융자산(소득 대비)', 'x_debt_r': '부채(소득 대비)', 'x_realestate_r': '부동산(소득 대비)',
    'x_house_value_r': '사는 집 가격(소득 대비)', 'x_net_assets_r': '순자산(소득 대비)', 'lg_x_fin_assets': '금융자산(로그)', 'lg_x_debt': '부채(로그)',
    'lg_x_realestate': '부동산(로그)', 'lg_x_house_value': '사는 집 가격(로그)', 'lg_x_net_assets': '순자산(로그)',
    'x_hh_earn_r': '가구 근로·사업소득(소득 대비)', 'x_pub_transfer_r': '공적이전소득(소득 대비)', 'x_priv_transfer_r': '사적이전소득(소득 대비)',
    'x_fin_income_r': '금융·임대소득(소득 대비)', 'x_transfer_from_children_r': '자녀에게 받은 돈(소득 대비)',
    'log_dratio': '지금 소득(판정 기준선 대비)', 'd_log_dratio_2y': '2년 사이 소득 변화(판정 기준)', 'd_log_ratio_1y': '1년 사이 소득 변화',
    'log_rneed': '지금 소득(필요 최소생활비 대비)', 'x_need_min': '필요 최소생활비', 'x_cover_ratio': '충족률(소득 ÷ 필요생활비)',
    'x_worry': '노후 준비 걱정', 'x_short_exp': '생활비 부족 경험', 'x_region': '지역(범주)',
}
GRP_COMMON = [('소득 수준·흐름', ['log_ratio', 'd_log_ratio_2y', 'd_log_ratio_4y', 'vol_hist', 'min_ratio_hist', 'ever_below_hist']),
              ('나이·연금 시점', ['age', 'age_to_60', 'age_to_nps']),
              ('사람·가구', ['female', 'edu3', 'married', 'hhsize', 'hh_change_2y']),
              ('일', ['employed', 'lost_job_2y', 'employed_l2'])]
GRP_EXTRA = [('기준선 대비 소득', ['log_dratio', 'd_log_dratio_2y', 'log_rneed', 'd_log_ratio_1y', 'x_need_min', 'x_cover_ratio']),
             ('일·직업', ['x_regular', 'x_temp_daily', 'x_selfemp', 'x_occ', 'employed_l1', 'x_own_earn_l2', 'x_earn_share', 'x_retired']),
             ('연금', ['x_pension_recv', 'x_pension_type', 'x_pension_enrolled', 'x_pension_amt_r', 'x_retire_pension', 'x_private_pension']),
             ('건강', ['x_health_bad', 'x_chronic', 'x_health_bad_l2', 'x_health_bad_d2', 'x_mental_bad', 'x_adl', 'x_iadl']),
             ('자산·부채', ['x_owner', 'x_fin_assets_r', 'x_debt_r', 'x_realestate_r', 'x_house_value_r', 'x_net_assets_r',
                         'lg_x_fin_assets', 'lg_x_debt', 'lg_x_realestate', 'lg_x_house_value', 'lg_x_net_assets']),
             ('소득 구성·이전', ['x_hh_earn_r', 'x_pub_transfer_r', 'x_priv_transfer_r', 'x_fin_income_r', 'x_transfer_from_children_r']),
             ('노후 인식', ['x_worry', 'x_short_exp']), ('지역', ['x_region'])]
assert sum(len(v) for _, v in GRP_COMMON) == 17 and set(sum([v for _, v in GRP_COMMON], [])) == set(COMMON)

NAME = {'KOWEPS': '한국복지패널', 'NaSTaB': '재정패널', 'KReIS': '국민노후보장패널', 'KLIPS': '한국노동패널', 'KHP': '한국의료패널', 'KLoSA': '고령화연구패널'}
ROLE = {'main': '판정', 'need': '판정 보조(필요생활비)', 'repl': '재현', 'transfer': '이식'}
TASKS = [t for t in O['tasks']]
TU = O['tune'].copy(); TU['params'] = TU.params.apply(lambda p: p if isinstance(p, dict) else eval(p))
Z = O['zoo'].pivot(index='task', columns='model', values='auc'); CMP = O['cmp']
A_ = AC['A'].set_index('task'); C_ = AC['C'].set_index('task')
spec = {'models': []}
fmt = lambda n: f'{int(n):,}'

# ================= 공통 코드 규칙 (모든 패널 모델) =================
G = '연구 모델(공통)'
chk(G, '대상·정답', '대상 = 50~69세 · 지금 r ≥ 1 · t+2와 t+4 관측, y = t+2~t+4 중 2번 이상 r<1(격년은 2번 중 2번)',
    has('label_v3.py', "D0.age.between(50, 69)", "d = d[ok & (d[base] >= 1)]", "below >= 2", "(f[2] < 1) & (f[4] < 1)"), 'label_v3.py label() · 대상 필터')
chk(G, '분할', '시험 = 그 과제의 최근 2개 조사연도, 학습 = 시험 시작 4년 전까지',
    has('label_v3.py', "ty = ys[-2:]", "d.svy_year <= min(ty) - 4"), 'label_v3.py')
chk(G, '열 고르기', '공통 17개 + (학습셋에서 20% 이상 채워지고 값이 2종 이상인 x_ 변수) + 판정용 소득 열',
    has('label_v3.py', 'cols = COMMON + EX + extra_inc') and has('common_ml.py', 'v.notna().mean() >= 0.2 and v.nunique(dropna=True) > 1'), 'label_v3.py · common_ml.extra_features')
chk(G, '열 고르기', '자산·부채 원금액은 넣지 않고 소득 대비 배수(_r, −50~200으로 자름)와 sign·log(1+|x|)로 넣음',
    has('common_ml.py', "tr['lg_' + c] = np.sign(tr[c]) * np.log1p(np.abs(tr[c]))", "EXCL = {") and has('build_common.py', "(S[c] / S.hhinc).clip(-50, 200)"), 'common_ml.EXCL · build_common.py')
chk(G, '극단값', '학습셋 0.5%·99.5% 분위로 자르고 시험셋에도 같은 경계 적용(범주·값 3종 이하 제외)',
    has('v3_full.py', "if c in CATEG or X[c].nunique() <= 3: continue", "X[c].quantile([0.005, 0.995])", "Xt[c] = Xt[c].clip(lo, hi)"), 'v3_full.winsor')
chk(G, '내부 분할', '내부 검증 = 학습셋 마지막 2개 연도, 내부 학습 = 그 4년 전까지',
    has('v3_full.py', "vy = sorted(tr.svy_year.unique())[-2:]; iv = tr.svy_year.isin(vy).values; it = (tr.svy_year <= min(vy) - 4).values"), 'v3_full.py')
chk(G, 'LightGBM', '격자 num_leaves 15/31 × min_child_samples 40/150, 학습률 0.03 · 행 0.8 · 열 0.8 · L2 1.0, 최대 3000회 + 조기 종료 100(내부 검증 AUC)',
    has('v3_full.py', "dict(num_leaves=n, min_child_samples=m) for n in (15, 31) for m in (40, 150)", "n_estimators=3000, learning_rate=0.03, subsample=0.8, subsample_freq=1, colsample_bytree=0.8",
        "reg_lambda=1.0", "lgb.early_stopping(100"), 'v3_full.tune')
chk(G, 'LightGBM', '고른 설정으로 학습셋 전체 재학습, 반복 수 = max(50, 조기 종료 지점 × 1.1)', has('v3_full.py', "n = max(50, int(n * 1.1))", "return m.fit(X, y)"), 'v3_full.tune')
chk(G, '로지스틱', '숫자 열: 중앙값 대체 + 결측 표시 → 표준화 / 범주 열: −1 채움 → 원-핫(50건 미만 묶음) → L2 로지스틱 C=1',
    has('v3_full.py', "SimpleImputer(strategy='median', add_indicator=True), StandardScaler()", "OneHotEncoder(handle_unknown='infrequent_if_exist', min_frequency=50",
        "'LR_L2': make_pipeline(prep(cols), LogisticRegression(C=1.0, max_iter=3000))"), 'v3_full.prep')
chk(G, '앙상블', '최종 = 시험셋 안에서 LightGBM 순위 + 로지스틱 순위', has('v3_full.py', "rankdata(S['LightGBM']) + rankdata(S['LR_L2'])"), 'v3_full.py')
chk(G, '기준선', 'B0 = −지금 소득, B1 = [지금 소득, 나이, 취업] 로지스틱', has('v3_full.py', "S = {'B0 지금 소득': -te[b0col].values}", "[[b0col, 'age', 'employed']]"), 'v3_full.py')
chk(G, '평가', '최종 − B0 AUC 차이를 DeLong으로 검정', has('v3_full.py', "'최종−지금소득': ('최종: LightGBM+로지스틱', 'B0 지금 소득')") and has('common_ml.py', 'def delong_diff'), 'v3_full.py · common_ml.delong')
chk(G, '이유', 'LightGBM pred_contrib(TreeSHAP) 기여 중 위험을 올린 상위 3개 · 중앙값으로 바꿔 무작위 3개와 비교',
    has('m_abc.py', "pred_contrib=True", "top3 = np.argsort(-con, axis=1)[:, :3]", "med.values"), 'm_abc.py M-A')
chk(G, '판단 보류', '내부 학습 모델로 내부 검증 점수 → 클래스별 경계 q1·q0(α=0.10) → 둘 다 포함이면 보류',
    has('m_abc.py', "mc = mk().fit(X[it], y[it])", "a = 0.10", "np.ceil((1 - a) * ((ycal == 1).sum() + 1))", "both = inc1 & inc0"), 'm_abc.py M-C')
chk(G, '이유·보류 범위', '이유·판단 보류 실험은 5개 과제(판정 3 + 필요생활비 + 노동)만, 의료·고령화(이식)는 안 함',
    set(A_.index) == set(C_.index) == {'KOWEPS_r', 'NaSTaB_r', 'KReIS_r', 'KReIS_rn', 'KLIPS_r'}, f'mabc_out_AC: {sorted(A_.index)}')

# ================= 과제별 모델 =================
for (p, base, b0col, role) in TASKS:
    k = f'{p}_{base}'; di = O['data_info'][k]; cols = di['cols']; M = NAME[p] + (' · 필요생활비 기준' if base == 'rn' else '')
    tr, te, cols2 = pickle.load(open(W + f'v3_data_{p}_{base}.pkl', 'rb'))
    ok_cols = cols2 == cols and cols[:17] == COMMON
    extra = cols[17:]
    chk(M, '입력', f'입력 {len(cols)}개 = 공통 17 + 추가 {len(extra)}', ok_cols and di['n_feat'] == len(cols), f"v3_data 열 == v3_out data_info 열: {cols2 == cols}, 앞 17개 == COMMON: {cols[:17] == COMMON}")
    unk = [c for c in extra if c not in LAB]
    grouped = sum([v for _, v in GRP_EXTRA], [])
    chk(M, '입력', '추가 입력이 모두 이름표·묶음에 들어감', not unk and all(c in grouped for c in extra), f'이름표 없는 열: {unk}')
    fill = {c: float(tr[c].notna().mean()) for c in cols}
    low_x = [c for c in extra if c.startswith('x_') and not c.endswith('_r') and fill[c] < 0.2]
    chk(M, '열 고르기', '추가 x_ 변수는 모두 학습셋 20% 이상 채워짐', not low_x, f'20% 미만: {low_x}')
    ty = sorted(te.svy_year.unique()); try_ = sorted(tr.svy_year.unique())
    ok_split = len(ty) == 2 and max(try_) <= min(ty) - 4 and len(tr) == di['n_tr'] and len(te) == di['n_te']
    l3 = L3[(L3.panel == p) & (L3.label.str.contains('필요') == (base == 'rn'))].iloc[0]
    chk(M, '분할', f"학습 {fmt(len(tr))}행({try_[0]}–{try_[-1]}) · 시험 {fmt(len(te))}행({ty[0]}·{ty[1]})",
        ok_split and int(l3.n_tr) == len(tr) and int(l3.n_te) == len(te), f'label_v3.csv 학습 {l3.n_tr} · 시험 {l3.n_te}')
    vy = try_[-2:]; iv = tr.svy_year.isin(vy); it = tr.svy_year <= min(vy) - 4
    t = TU[(TU.task == k) & (TU.model == 'LightGBM')].iloc[0]
    chk(M, 'LightGBM', f"고른 설정 leaves {t.params['num_leaves']} · min_child {t.params['min_child_samples']} · 반복 {t.iters}회 (내부 검증 AUC {t.inner:.3f})",
        t.params['num_leaves'] in (15, 31) and t.params['min_child_samples'] in (40, 150) and t.iters >= 50, 'v3_out tune')
    au = {m: float(Z.loc[k, m]) for m in ['B0 지금 소득', 'B1 계산기형', 'LR_L2', 'LightGBM', '최종: LightGBM+로지스틱']}
    c0 = CMP[(CMP.task == k) & (CMP.comp == '최종−지금소득')].iloc[0]
    chk(M, '평가', f"시험 AUC 최종 {au['최종: LightGBM+로지스틱']:.3f} vs 지금 소득 {au['B0 지금 소득']:.3f} (차이 {c0.delta:+.3f}, 95% {c0.delta - 1.96 * c0.se:+.3f}~{c0.delta + 1.96 * c0.se:+.3f})",
        abs(c0.auc_a - au['최종: LightGBM+로지스틱']) < 1e-9 and abs(c0.auc_b - au['B0 지금 소득']) < 1e-9, 'v3_out zoo == cmp')
    cats = [c for c in cols if c in CATEG]
    m = dict(id=k, kind='task', title=M, panel=NAME[p], role=ROLE[role], base=base,
             target=('필요 최소생활비 대비 소득 비율이 1 이상인 사람의 2년 뒤 반복 부족' if base == 'rn' else
                     ('가처분' if p in ('KOWEPS', 'NaSTaB', 'KReIS') else '경상') + ' 기준선 위인 사람의 2년 뒤 반복 하락'),
             b0col=b0col, n_feat=len(cols), n_extra=len(extra), cats=cats,
             groups_common=[(g, [(c, LAB[c], round(fill[c] * 100)) for c in v]) for g, v in GRP_COMMON],
             groups_extra=[(g, [(c, LAB[c], round(fill[c] * 100)) for c in v if c in extra]) for g, v in GRP_EXTRA if any(c in extra for c in v)],
             n_tr=len(tr), n_te=len(te), tr_years=f'{try_[0]}–{try_[-1]}', te_years=f'{ty[0]}·{ty[1]}', pos_te=float(te.y.mean()),
             n_it=int(it.sum()), n_iv=int(iv.sum()), it_years=f'{try_[0]}–{int(tr.svy_year[it].max())}', iv_years=f'{vy[0]}·{vy[1]}',
             lgb=dict(leaves=int(t.params['num_leaves']), min_child=int(t.params['min_child_samples']), iters=int(t.iters), inner=float(t.inner)),
             auc=dict(b0=au['B0 지금 소득'], b1=au['B1 계산기형'], lr=au['LR_L2'], lgb=au['LightGBM'], fin=au['최종: LightGBM+로지스틱']),
             delta=float(c0.delta), lo=float(c0.delta - 1.96 * c0.se), hi=float(c0.delta + 1.96 * c0.se))
    if k in A_.index:
        a, c = A_.loc[k], C_.loc[k]
        top = AC['A_top'][AC['A_top'].task == k].head(3)
        m['shap'] = dict(ratio=float(a.ratio), top=[(r.feature, LAB.get(r.feature, r.feature), float(r.share)) for r in top.itertuples()])
        m['conf'] = dict(cov_pos=float(c.cov_pos), cov_neg=float(c.cov_neg), abstain=float(c.abstain), n_cal=int(c.n_cal))
        chk(M, '판단 보류', f'보정 행 = 내부 검증 {fmt(c.n_cal)}행', int(c.n_cal) == int(iv.sum()), f'내부 검증 행 {int(iv.sum())}')
    spec['models'].append(m)

# ================= 통합 모델 =================
M = '통합 모델(판정 3 + 노동)'
chk(M, '입력', '입력 = 공통 17 + 지금 소득(판정 기준) + 2년 변화(판정 기준) + 패널 표시 4개 = 23개',
    has('v3_full.py', "PK = MAIN + ['KLIPS_r']", "ccols = COMMON + ['log_dratio', 'd_log_dratio_2y']", "pc = ccols + ['pn_' + k for k in PK]"), 'v3_full.py 4절')
ntr = sum(O['data_info'][k]['n_tr'] for k in ['KOWEPS_r', 'NaSTaB_r', 'KReIS_r', 'KLIPS_r']); nte = sum(O['data_info'][k]['n_te'] for k in ['KOWEPS_r', 'NaSTaB_r', 'KReIS_r', 'KLIPS_r'])
chk(M, '데이터', f'4개 과제 학습셋 합 {fmt(ntr)}행 = 학습곡선 100% 지점', int(O['lc'].n.max()) == ntr, f"lc 최대 n {int(O['lc'].n.max())}")
chk(M, 'LightGBM', '고정 설정(격자 탐색 없음): leaves 31 · min_child 80 · 학습률 0.03 · 행·열 0.8, 600회(학습곡선)·800회(반복 곡선)·300회(셔플)',
    has('v3_full.py', "mkp = lambda n=600: lgb.LGBMClassifier(n_estimators=n, learning_rate=0.03, num_leaves=31, min_child_samples=80", "mp = mkp(800)", "m = mkp(300).fit(ptr[pc], ptr.y.sample(frac=1"), 'v3_full.py 4절')
lc = O['lc']; perm = O['perm']
chk(M, '학습곡선', f"학습 행 {fmt(lc.n.min())} → {fmt(lc.n.max())}에서 시험 AUC {lc.test_auc.iloc[0]:.3f} → {lc.test_auc.iloc[-1]:.3f}", lc.test_auc.iloc[-1] > lc.test_auc.iloc[0], 'v3_out lc')
chk(M, '셔플', f'정답만 섞어 5번 학습 → 시험 AUC 평균 {np.mean(perm):.3f}', len(perm) == 5 and abs(np.mean(perm) - 0.5) < 0.05, np.round(perm, 3).tolist())
bands = O['bands']
spec['models'].append(dict(id='pooled', kind='pooled', title=M, n_tr=ntr, n_te=nte,
    inputs=[('공통 17', [(c, LAB[c]) for c in COMMON]), ('판정 기준 소득', [('log_dratio', LAB['log_dratio']), ('d_log_dratio_2y', LAB['d_log_dratio_2y'])]),
            ('패널 표시', [(f'pn_{k}', NAME[k.split('_')[0]] + ' 행이면 1') for k in ['KOWEPS_r', 'NaSTaB_r', 'KReIS_r', 'KLIPS_r']])],
    parts=[(NAME[k.split('_')[0]], O['data_info'][k]['n_tr'], O['data_info'][k]['n_te']) for k in ['KOWEPS_r', 'NaSTaB_r', 'KReIS_r', 'KLIPS_r']],
    lc=dict(n0=int(lc.n.min()), n1=int(lc.n.max()), a0=float(lc.test_auc.iloc[0]), a1=float(lc.test_auc.iloc[-1]),
            g0=float(lc.train_auc.iloc[0] - lc.test_auc.iloc[0]), g1=float(lc.train_auc.iloc[-1] - lc.test_auc.iloc[-1])),
    perm=float(np.mean(perm)), pool_all=float(O['pool_all']), pool_b0=float(O['pool_b0']),
    pool_auc={NAME[k.split('_')[0]]: float(v) for k, v in O['pool_auc'].items()},
    bands=[dict(lo=float(r.lo), hi=float(r.hi), n=int(r.n), ml=float(r.auc_ml), b0=float(r.auc_b0)) for r in bands.itertuples()],
    staged=dict(tr=float(O['staged'].train_auc.iloc[-1]), te=float(O['staged'].test_auc.iloc[-1]), te_max=float(O['staged'].test_auc.max()))))

# ================= 이식 모델 =================
M = '이식 모델(공통 입력)'
chk(M, '입력', '입력 = 공통 17 + 지금 소득(그 패널 기준선 대비) = 18개', has('v3_full.py', "cc = COMMON + ['log_dratio']"), 'v3_full.py 6절')
chk(M, 'LightGBM', '고정 설정: 500회 · leaves 15 · min_child 80 · 학습률 0.03, 패널 A 학습셋으로 학습 → 패널 B 시험셋에 적용',
    has('v3_full.py', "m = lgb.LGBMClassifier(n_estimators=500, learning_rate=0.03, num_leaves=15, min_child_samples=80", ".fit(A_['tr'][cc], A_['tr'].y)", "q = m.predict_proba(Bd['te'][cc])"), 'v3_full.py 6절')
chk(M, '보정', '다른 패널에 쓸 때 확률 크기는 그 패널 내부 검증으로 Platt 재보정(순위·AUC는 그대로)',
    has('v3_full.py', "rec = Bd['tr'][Bd['iv']]", "pl = LogisticRegression().fit(lg_(qr).reshape(-1, 1), rec.y)"), 'v3_full.py 6절')
TM = O['transfer']; TC = O['transfer_cal']
chk(M, '결과', '6×6 교차 AUC 표 모두 채워짐', TM.shape == (6, 6) and TM.notna().all().all(), TM.shape)
spec['models'].append(dict(id='transfer', kind='transfer', title=M, inputs=[('공통 17', [(c, LAB[c]) for c in COMMON]), ('지금 소득', [('log_dratio', '그 패널 기준선 대비 지금 소득')])],
    names=[NAME[k.split('_')[0]] for k in TM.index], matrix=TM.values.round(3).tolist(),
    cal=dict(raw_gap=float((TC.pred_raw - TC.obs).abs().mean()), cal_gap=float((TC.pred_cal - TC.obs).abs().mean()))))

# ================= 서비스 모델 S20 / S21 =================
BASE = eval(re.search(r"BASE = (\[.*?\])", src['s_model.py'], re.S).group(1))
SLAB = {'s_hhchg': '최근 2년 가구원 변화', 's_log_r': '지금 소득(기준선 대비)', 's_d1': '1년 사이 소득 변화', 's_d2': '2년 사이 소득 변화',
        's_min3': '최근 3년 중 최저 소득', 's_vol3': '최근 3년 소득 출렁임', 's_emp_l1': '1년 전 일함', 's_emp_l2': '2년 전 일함',
        's_lost': '최근 2년 내 일 그만둠', 's_owner': '사는 집 자가', 's_fin_r': '금융자산(소득 대비)', 's_debt_r': '부채(소득 대비)',
        's_real_r': '부동산(소득 대비)', 's_lg_fin': '금융자산(로그)', 's_lg_debt': '부채(로그)', 's_lg_real': '부동산(로그)', 's_health': '건강(선택)'}
SL = lambda c: SLAB.get(c, LAB.get(c, c))
SG = [('나와 가족', ['age', 'age_to_60', 'age_to_nps', 'female', 'married', 'edu3', 'hhsize', 's_hhchg']),
      ('연금 곳간', ['x_pension_recv', 'x_retire_pension', 'x_private_pension']),
      ('소득의 흐름', ['s_log_r', 's_d1', 's_d2', 's_min3', 's_vol3']),
      ('일과 재산', ['employed', 's_emp_l1', 's_emp_l2', 's_lost', 'x_regular', 'x_temp_daily', 'x_selfemp', 's_owner',
                  's_fin_r', 's_debt_r', 's_real_r', 's_lg_fin', 's_lg_debt', 's_lg_real']), ('선택', ['s_health'])]
for tag in ['S20', 'S21']:
    r = S[('KOWEPS', tag)]['res']; Mo = S[('KOWEPS', tag)]['M']; M = f'서비스 모델 {tag}'
    want = BASE + (['s_health'] if tag == 'S21' else [])
    chk(M, '입력', f'입력 {len(want)}개 = 화면 문항으로 만들 수 있는 변수만', r['cols'] == want == META[tag]['features'], '코드 BASE == s_out 열 == 배포 meta 열')
    chk(M, '학습', '연구 모델과 같은 학습 함수(극단값·내부 분할·2×2 격자·×1.1 재학습·로지스틱) · 복지패널 같은 학습/시험 행',
        has('s_model.py', "dict(num_leaves=n, min_child_samples=m) for n in (15, 31) for m in (40, 150)", "n = max(50, int(best[2] * 1.1))",
            "SimpleImputer(strategy='median', add_indicator=True), StandardScaler(), LogisticRegression(C=1.0") and r['n_tr'] == O['data_info']['KOWEPS_r']['n_tr'] and r['n_te'] == O['data_info']['KOWEPS_r']['n_te'],
        f"학습 {r['n_tr']} · 시험 {r['n_te']}")
    chk(M, '앙상블', '최종 = LightGBM·로지스틱 점수를 각각 시험셋 분포(1001개 분위)에서의 위치로 바꿔 평균 (연구 모델의 순위 평균을 한 사람에게도 쓰도록 바꾼 것)',
        has('s_model.py', "fin = (np.interp(sg, ref['g'], G) + np.interp(sl, ref['l'], G)) / 2") and has('spkg_predict.py', "fin = (np.interp(sg, self.qg, self.G) + np.interp(sl, self.ql, self.G)) / 2")
        and len(META[tag]['ref_quantiles']['lgb']) == 1001, 'spkg_predict.run · meta ref_quantiles 1001개')
    chk(M, '판단 보류', f"보류 경계 q1 {Mo['q1']:.4f} · q0 {Mo['q0']:.4f} (α=0.10) = 배포 파일 값", abs(META[tag]['conformal']['q1'] - Mo['q1']) < 1e-12 and abs(META[tag]['conformal']['q0'] - Mo['q0']) < 1e-12, 'meta conformal')
    chk(M, '평가', f"시험 AUC {r['auc_service']:.3f} (전체 입력 {r['auc_full']:.3f}, 지금 소득 {r['auc_b0']:.3f}) · 포함률 {r['cov_pos']:.3f}/{r['cov_neg']:.3f} · 보류 {r['abstain']:.1%}",
        bool(r['pass1']) and bool(r['pass2']), f"사전 기준 pass1 {r['pass1']} · pass2 {r['pass2']}")
    spec['models'].append(dict(id=tag, kind='service', title=M, tag=tag, n_tr=r['n_tr'], n_te=r['n_te'], n_feat=len(want),
        groups=[(g, [(c, SL(c)) for c in v if c in want]) for g, v in SG if any(c in want for c in v)],
        lgb=dict(leaves=r['params']['num_leaves'], min_child=r['params']['min_child_samples'], iters=r['iters'], inner=r['inner']),
        auc=dict(svc=r['auc_service'], full=r['auc_full'], lgb=r['auc_lgb'], lr=r['auc_lr'], b0=r['auc_b0']), loss=r['loss'],
        conf=dict(cov_pos=r['cov_pos'], cov_neg=r['cov_neg'], abstain=r['abstain']),
        nastab=dict(auc=S[('NaSTaB', 'S20')]['res']['auc_service'], b0=S[('NaSTaB', 'S20')]['res']['auc_b0'], n_feat=S[('NaSTaB', 'S20')]['res']['n_feat']) if tag == 'S20' else None))
G = '서비스 공통(배포 코드)'
chk(G, '대상 확인', '50~69세만, 지금 소득 > 0, 기준선 아래(r<1)면 B20으로', has('spkg_predict.py', "if not (50 <= age <= 69):", "if not (r0 == r0 and r0 > 0):", "if r0 < 1:", "out = self.b20.run(F)"), 'spkg_predict.predict')
chk(G, '건강 문항', '건강 답이 있으면 S21, 없으면 S20', has('spkg_predict.py', "m = self.m21 if 's_health' in F else self.m20"), 'spkg_predict.predict')
chk(G, '변환', '월 실수령 × 12 → 2023년 가격 → √가구원 → 그 해 기준선 대비 → 로그', has('spkg_predict.py', "m * 12 * self._cpi(2023) / self._cpi(y) / np.sqrt(h) / self._line(y)"), 'spkg_predict.features')
chk(G, '등급', '상위 20% = high, 20~40% = mid, 나머지 = low', has('spkg_predict.py', "band='high' if top <= 0.2 else 'mid' if top <= 0.4 else 'low'"), 'spkg_predict.run')
chk(G, '이유', '이유 3개 = LightGBM 기여의 절댓값 상위 3개(올린 쪽·내린 쪽 모두)', has('spkg_predict.py', "con = self.gbm.predict(X, pred_contrib=True)[0, :-1]; idx = np.argsort(-np.abs(con))[:3]"), 'spkg_predict.run')
chk(G, '화면 경로', f"시험 행을 화면 답으로 되돌려 같은 변수가 나오는지: 점수 상관 {PC['corr']:.4f}, AUC {PC['auc_train']:.4f} → {PC['auc_api']:.4f}",
    PC['corr'] > 0.99 and abs(PC['auc_train'] - PC['auc_api']) < 0.005, 's_pathcheck.pkl')

# ================= B20 =================
R = BO['res']; M = '기준선 아래 모델 B20'
chk(M, '대상', '복지패널 50~69세 · 0 < r < 1 · 같은 정답 정의 → y=1이면 2년 뒤에도 아래에 머묾',
    has('b_model.py', "(D0.panel == 'KOWEPS') & D0.age.between(50, 69)", "d = d[ok & (d.r > 0) & (d.r < 1)]"), 'b_model.py')
chk(M, '입력', '입력 = S20과 같은 30개', BO['M']['cols'] == BASE == META['B20']['features'], 'b_out 열 == BASE == 배포 meta')
chk(M, '사전 기준', f"C1 표본 · C2 DeLong 하한 {R['delta_lo']:+.3f} > 0 · C3 포함률 {R['cov_pos']:.3f}/{R['cov_neg']:.3f} ≥ 0.85", R['C1'] and R['C2'] and R['C3'], 'prereg_B.txt')
chk(M, '분할', f"학습 {fmt(R['n_tr'])} · 시험 {fmt(R['n_te'])}행 (시험 {R['test_years'][0]}·{R['test_years'][1]})", R['n_tr'] == 11990 and R['n_te'] == 1131, 'b_out res')
spec['models'].append(dict(id='B20', kind='b20', title=M, n_tr=R['n_tr'], n_te=R['n_te'], te_years=f"{R['test_years'][0]}·{R['test_years'][1]}",
    stay=R['stay_rate'], lgb=dict(leaves=R['params']['num_leaves'], min_child=R['params']['min_child_samples'], iters=R['iters'], inner=R['inner']),
    auc=dict(fin=R['auc_model'], b0=R['auc_b0'], lgb=R['auc_lgb'], lr=R['auc_lr']), delta=R['delta'], lo=R['delta_lo'],
    conf=dict(cov_pos=R['cov_pos'], cov_neg=R['cov_neg'], abstain=R['abstain']), bins=R['bins'],
    groups=[(g, [(c, SL(c)) for c in v if c in BASE]) for g, v in SG if any(c in BASE for c in v)]))

# ---------------- 저장 ----------------
bad = [c for c in checks if c['result'] != '통과']
json.dump(checks, open(OUT + 'models_verify.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
with open(OUT + 'models_verify.md', 'w', encoding='utf-8') as f:
    f.write(f'# 모델별 상세 설계도 검정표\n\n검정 항목 {len(checks)}개 · 통과 {len(checks) - len(bad)} · 불일치 {len(bad)}\n\n| 모델 | 단계 | 주장 | 결과 | 근거 |\n|---|---|---|---|---|\n')
    for c in checks: f.write(f"| {c['model']} | {c['step']} | {c['claim']} | {c['result']} | {c['evidence'].replace('|', '/')} |\n")
if bad:
    for c in bad: print('불일치:', c['model'], c['step'], c['claim'], c['evidence'])
    if os.path.exists(OUT + 'models_spec.json'): os.remove(OUT + 'models_spec.json')
    sys.exit(1)
spec['checks'] = len(checks)
json.dump(spec, open(OUT + 'models_spec.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1, default=float)
print(f'검정 {len(checks)}개 모두 통과 → models_spec.json 작성 (모델 {len(spec["models"])}개)')
