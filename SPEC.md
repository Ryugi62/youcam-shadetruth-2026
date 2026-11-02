# ShadeTruth — SPEC

## 목적
립 컬러 가상 시착의 「색이 정말 브랜드 색인가」를 숫자로 확인한다. 소매업체가 가상 시착을 켜기 전에, 그리고 쇼핑객이 보는 순간에, 보낸 브랜드 디지털 색(HEX)과 렌더된 입술 색이 얼마나 다른지 CIEDE2000로 재고 배지로 표시한다.
정직한 범위: 정답은 「API에 보낸 HEX(브랜드 디지털 색)」이다. 병 실물·화면 색 차이는 측정하지 않는다. 의료·진단 주장 없음(미용 용도).

## 유비쿼터스 언어
- 브랜드 디지털 색(brand shade): API에 보낸 `#RRGGBB`.
- 렌더 영역(rendered region): 원본 대비 바뀐 픽셀 중 가장자리 번짐을 걷어낸 안쪽 입술 픽셀.
- 드리프트(drift): 렌더 영역 평균 색과 브랜드 디지털 색의 CIEDE2000 중 색상·채도 항만 합친 값 `ΔE00_HC = sqrt((ΔC'/S_C)^2 + (ΔH'/S_H)^2)`. 명도 L*는 따로 `ΔL*`(밝다/어둡다)로 표시한다.
- 배지: `Matches brand digital shade`(드리프트 ≤ 5) · `Close to brand digital shade`(≤ 10) · `Approximate preview`(> 10) · `Unverifiable`(렌더 영역을 못 잡음). 판정선 5·10은 첫 API 호출 전에 고정(2026-10-17)했고 문헌 근거는 없는 우리 선택값이다.
- 독립 판독(cross-read): 같은 렌더 이미지를 YouCam Face Tone Analyzer(`skin-tone-analysis`)에 다시 넣어 얻은 `lip_color`와 브랜드 디지털 색의 드리프트. 내 영역 측정과 두 값이 4 이내면 `agree`.

## 사용하는 YouCam API (서버에서만 호출)
1. File API `POST /s2s/v2.0/file` + 사전서명 URL PUT — 사진 업로드.
2. AI Makeup VTO `POST/GET /s2s/v2.0/task/makeup-vto` — `lip_color`, matte, colorIntensity 100, skin_smooth 0.
3. AI Facial Color Tones Analyzer `POST/GET /s2s/v2.0/task/skin-tone-analysis` — 렌더 결과의 입술 색 독립 판독.
API 키는 서버 환경변수 `YOUCAM_API_KEY`에만 둔다.

## 성공 조건 (숫자)
| # | 조건 | 판정 방법 |
|---|---|---|
| S1 | 사진 1장 + HEX 1개 → 배지·드리프트·ΔL*·독립 판독이 한 화면에 나온다 | 실호출 1회 결과 파일 |
| S2 | 드리프트 표 ≥ 12행(사진 ≥ 2 × 색 ≥ 6) 실호출 측정, 표본 N을 화면에 표시 | `data/drift.json` |
| S3 | 색 수학 단위 시험: Sharma 2005 CIEDE2000 검증 쌍 ≥ 5 일치(소수 4자리), 배지 경계 시험 통과 | `pytest` 전부 통과 |
| S4 | 키 노출 0: 레포·커밋 이력·영상·스크린샷에서 키 문자열 grep 0건 | `scripts/check_no_secret.sh` |
| S5 | 호출당 유닛 표 일치: VTO 1 + 톤 분석 20 = 21유닛/검사 | 실행 전후 잔액 조회 |
| S6 | 클론 후 명령 1줄(`make run`)로 서버 기동 | README |
| S7 | 정직 표기 3종이 화면에 있다: 합성·샘플 얼굴 사용 / 측정 한계 / 브랜드 디지털 색 기준 | 화면 캡처 |

## Given / When / Then
- Given 사진과 `#C2185B`, When 검사하면, Then 렌더 입술 영역 평균 Lab과 `#C2185B`의 ΔE00_HC, ΔL*, 배지 이름, 독립 판독 HEX가 나온다.
- Given 얼굴이 없는 사진, When 검사하면, Then 배지는 `Unverifiable`이고 API 오류 원문을 보여 준다(만들어 낸 숫자 없음).
- Given 바뀐 픽셀이 화면의 0.1% 미만이거나 12% 초과, When 영역을 잡으면, Then `Unverifiable`.

## 비목표
- 병 실물·모니터 색 보정, 피부 진단·의료 주장, 파운데이션 톤 매칭, 사용자 얼굴 저장(요청 처리 뒤 즉시 폐기), 계정·결제, 모델 학습.
- 입술 외 영역(블러셔·헤어·네일)은 이번 제출 범위 밖(확장 설계만 README에 적음).

## 구조 (Clean Architecture)
`shadetruth/domain`(색 수학·배지 규칙·영역 판정 — 외부 I/O 없음) ← `application`(검사 유스케이스, 포트 정의) ← `adapters`(YouCam HTTP) ← `server.py`(infra).

## UI 수용기준 (notes/원칙-디자인 체크리스트 10을 이 화면에 구체화)
1. 모바일 우선: viewport 메타 있음, 390px에서 가로 스크롤 0(표만 자체 가로 스크롤 영역), 1280px 정상.
2. 한 화면 한 질문: 사진 → 색 → 「Check shade」 한 흐름, 주 행동 1개.
3. 타이포: 본문 16px, 보조 13~15px, 제목 20·28px, 줄간격 1.55, 12px 미만 없음.
4. 여백: 간격 값은 4/8 배수, 카드 라운드 ≥12px, 좌우 16px.
5. 주 버튼 높이 ≥48px, 모든 터치 목표 ≥44px.
6. 결과 카드: 배지가 가장 먼저, 그 아래 색 3종(브랜드·렌더·독립 판독)과 숫자.
7. 근거: 측정 방법·한계는 하단 카드에 문장으로, 첫 화면에는 검사 폼과 결과가 먼저.
8. 문안: 오류는 원인 + 할 일 1줄(예: 「Enter a HEX like #C2185B.」), 코드 노출 없음.
9. 색: 상태 3종(Matches·Close·Approximate) + 회색(Unverifiable), 글자 대비 ≥4.5:1(라이트·다크), 배지는 색만이 아니라 글자로도 구분, 포커스 표시 유지.
10. 의존·상태: 외부 폰트·CDN 0, 로딩·오류·빈 상태(데이터 없음·Unverifiable) 화면 3종 제공.
