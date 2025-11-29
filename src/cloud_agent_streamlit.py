import streamlit as st
import json

from cloud_agent import (
    create_agents,
    analyze_requirements,
    recommend_architecture,
)

st.set_page_config(
    page_title="클라우드 서비스 추천 Agent",
    page_icon="☁️",
    layout="wide",
)

# 한 번만 생성
if "agents" not in st.session_state:
    st.session_state.agents = create_agents()
if "requirements" not in st.session_state:
    st.session_state.requirements = None
if "followup_questions" not in st.session_state:
    st.session_state.followup_questions = []
if "followup_answers" not in st.session_state:
    st.session_state.followup_answers = {}
if "arch_result" not in st.session_state:
    st.session_state.arch_result = None

requirements_agent, arch_agent = st.session_state.agents

st.title("☁️ 클라우드 서비스 추천 Agent")
st.caption(
    "자연어로 서비스 설명을 하면, AWS 아키텍처 패턴을 추천해주는 과제용 데모입니다."
)

# --- 진행 단계 표시 ---
step_cols = st.columns(3)
with step_cols[0]:
    st.markdown("### ① 서비스 설명")
with step_cols[1]:
    st.markdown("### ② 요구사항 분석")
with step_cols[2]:
    st.markdown("### ③ 아키텍처 추천")

st.markdown("---")

# --- 상단: 입력 영역 & 요구사항 요약 ---
col_left, col_right = st.columns([1.1, 1])

with col_left:
    st.subheader("1단계 · 서비스 설명 입력")

    preset = st.selectbox(
        "예시 선택 (원하는 경우 선택하고, 아래 설명은 자유롭게 수정 가능)",
        (
            "직접 작성",
            "소규모 스마트 주방 제어 대시보드",
            "교회 예배 출석 체크 웹 서비스",
            "파일 공유용 사내 포털",
        ),
    )

    if "input_text" not in st.session_state:
        st.session_state.input_text = ""

    if preset != "직접 작성" and not st.session_state.input_text:
        # 처음 선택했을 때만 프리필 (원하면 로직 더 다듬어도 됨)
        if preset == "소규모 스마트 주방 제어 대시보드":
            st.session_state.input_text = "소규모 스마트 주방에서 기기 상태를 보고 제어할 수 있는 내부용 웹 대시보드"
        elif preset == "교회 예배 출석 체크 웹 서비스":
            st.session_state.input_text = (
                "주일 예배 출석을 간단히 체크하고 통계를 볼 수 있는 모바일 웹 서비스"
            )
        elif preset == "파일 공유용 사내 포털":
            st.session_state.input_text = (
                "팀원들이 문서와 이미지를 올리고 공유할 수 있는 간단한 사내 파일 포털"
            )

    desc = st.text_area(
        "만들고 싶은 서비스 설명",
        value=st.session_state.input_text,
        height=140,
        placeholder="예: 소규모 팀에서 쓸 스마트 주방 제어 대시보드를 만들고 싶어요...",
    )

    if st.button("1단계: 요구사항 분석하기 🚀"):
        if not desc.strip():
            st.warning("서비스 설명을 먼저 입력해주세요.")
        else:
            with st.spinner("요구사항 분석 중..."):
                req_result = analyze_requirements(requirements_agent, desc)
            if req_result.get("parse_error"):
                st.error(
                    "요구사항 JSON 파싱에 실패했습니다. 입력을 조금 더 구체적으로 바꿔보세요."
                )
                st.json(req_result.get("raw_response"))
            else:
                st.session_state.requirements = req_result.get("requirements", {})
                st.session_state.followup_questions = list(
                    dict.fromkeys(req_result.get("followup_questions", []))
                )
                st.session_state.followup_answers = {}
                st.session_state.arch_result = None  # 이전 결과 초기화
                st.success("요구사항을 정리했습니다.")

with col_right:
    st.subheader("요구사항 요약")

    if st.session_state.requirements:
        st.json(st.session_state.requirements)
    else:
        st.info("왼쪽에서 1단계 요구사항 분석을 먼저 실행해주세요.")

    if st.session_state.followup_questions:
        st.markdown("#### 추가로 확인하고 싶은 내용")
        with st.form("followup_form"):
            new_answers = {}
            for idx, q in enumerate(st.session_state.followup_questions, start=1):
                key = f"Q{idx}"
                default = st.session_state.followup_answers.get(key, {}).get(
                    "answer", ""
                )
                ans = st.text_input(f"{key}. {q}", value=default)
                new_answers[key] = {"question": q, "answer": ans}
            submitted = st.form_submit_button("추가 질문 답변 제출")
            if submitted:
                st.session_state.followup_answers = new_answers
                st.success("추가 질문 답변이 저장되었습니다.")
    else:
        st.caption("이 서비스 설명으로는 추가 질문이 필요하지 않다고 판단했습니다.")

st.markdown("---")

# --- 3단계: 아키텍처 추천 ---
st.subheader("2단계 · 아키텍처 추천")

col_btn, col_blank = st.columns([1, 3])
with col_btn:
    can_recommend = st.session_state.requirements is not None

    if st.button("2단계: 아키텍처 추천 받기 🧠", disabled=not can_recommend):
        if not can_recommend:
            st.warning("먼저 1단계에서 요구사항 분석을 실행해주세요.")
        else:
            with st.spinner("AWS 아키텍처 패턴을 추천하는 중입니다..."):
                arch_result = recommend_architecture(
                    arch_agent,
                    st.session_state.requirements,
                    st.session_state.followup_answers,
                )
            if arch_result.get("parse_error"):
                st.error("아키텍처 추천 JSON 파싱에 실패했습니다.")
                st.json(arch_result.get("raw_response"))
            else:
                st.session_state.arch_result = arch_result
                st.success("아키텍처 패턴 추천이 완료되었습니다.")

if st.session_state.arch_result:
    arch = st.session_state.arch_result
    tabs = st.tabs(["🧩 요약 보기", "🛠 세팅 가이드", "📄 IaC 코드", "🧾 RAW JSON"])

    with tabs[0]:
        st.markdown(f"### ✅ 선택된 패턴: **{arch.get('selected_pattern_name')}**")
        st.caption(f"ID: `{arch.get('selected_pattern_id')}`")

        st.markdown("#### 사용 서비스 및 역할")
        for s in arch.get("services_detail", []):
            st.write(f"- **{s.get('service')}**: {s.get('role')}")

        if arch.get("architecture_diagram_text"):
            st.markdown("#### 텍스트 아키텍처 다이어그램")
            st.code(arch["architecture_diagram_text"])

        reasoning = arch.get("reasoning", {})
        if reasoning:
            st.markdown("#### 왜 이 패턴인가?")
            if reasoning.get("fit_to_requirements"):
                st.write(reasoning["fit_to_requirements"])
            if reasoning.get("pros"):
                st.markdown("**장점**")
                for p in reasoning["pros"]:
                    st.write(f"- {p}")
            if reasoning.get("cons"):
                st.markdown("**단점/주의사항**")
                for c in reasoning["cons"]:
                    st.write(f"- {c}")
            if reasoning.get("tradeoffs"):
                st.markdown("**트레이드오프**")
                st.write(reasoning["tradeoffs"])

    with tabs[1]:
        setup = arch.get("setup_guide", {})
        st.markdown("#### 콘솔에서 따라하는 세팅 가이드")
        for i, step in enumerate(setup.get("console_steps", []), start=1):
            st.write(f"{i}. {step}")

        if setup.get("cli_examples"):
            st.markdown("#### AWS CLI 예시")
            for cmd in setup["cli_examples"]:
                st.code(cmd, language="bash")

    with tabs[2]:
        iac = arch.get("iac_snippets", {})
        if iac.get("cloudformation_yaml"):
            st.markdown("#### CloudFormation (YAML)")
            st.code(iac["cloudformation_yaml"], language="yaml")
        if iac.get("terraform_hcl"):
            st.markdown("#### Terraform (HCL)")
            st.code(iac["terraform_hcl"], language="hcl")

    with tabs[3]:
        st.markdown("#### RAW JSON 응답")
        st.code(json.dumps(arch, ensure_ascii=False, indent=2), language="json")
else:
    st.info("아직 추천 결과가 없습니다. 위에서 1단계와 2단계를 순서대로 실행해보세요.")
