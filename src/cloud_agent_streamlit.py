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

# ─────────────────────────────────────────────────────────────
# 1. 초기화 및 세션 상태 관리
# ─────────────────────────────────────────────────────────────
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

# [수정됨] 반환값이 3개이므로 _(언더바)로 세 번째 값(iac_agent)을 받아 무시 처리
requirements_agent, arch_agent, _ = st.session_state.agents

# ─────────────────────────────────────────────────────────────
# 2. 메인 UI 헤더
# ─────────────────────────────────────────────────────────────
st.title("☁️ 클라우드 아키텍처 설계 에이전트")
st.markdown("""
이 에이전트는 사용자의 **자연어 설명**을 분석하여, 
가장 적합한 **AWS 아키텍처 패턴**을 추천하고 **IaC 코드(Terraform/CloudFormation)** 까지 생성해 줍니다.
""")
st.divider()

# ─────────────────────────────────────────────────────────────
# 3. 2단 컬럼 레이아웃 (왼쪽: 입력 / 오른쪽: 결과)
# ─────────────────────────────────────────────────────────────
col_left, col_right = st.columns([1, 1.2], gap="large")

# === [왼쪽 컬럼] 입력 및 분석 단계 ===
with col_left:
    st.header("📝 1. 서비스 요구사항 입력")
    
    # 예시 선택 프리셋
    preset = st.selectbox(
        "💡 예시 시나리오 선택 (직접 입력 가능)",
        (
            "직접 작성",
            "대학생 동아리용 소규모 게시판 (비용 민감)",
            "트래픽이 급증하는 티켓 예매 사이트",
            "매일 밤 로그를 분석하는 데이터 파이프라인",
        ),
    )

    if "input_text" not in st.session_state:
        st.session_state.input_text = ""

    # 프리셋 선택 시 텍스트 자동 채움
    if preset != "직접 작성":
        if preset == "대학생 동아리용 소규모 게시판 (비용 민감)":
            st.session_state.input_text = "동아리원 50명 정도가 쓸 게시판이야. 돈이 거의 안 들었으면 좋겠고 관리하기도 귀찮아."
        elif preset == "트래픽이 급증하는 티켓 예매 사이트":
            st.session_state.input_text = "유명 가수 콘서트 티켓팅 사이트야. 평소엔 조용한데 오픈 1분 만에 10만 명이 몰릴 수 있어. 절대 죽으면 안 돼."
        elif preset == "매일 밤 로그를 분석하는 데이터 파이프라인":
            st.session_state.input_text = "서버 로그가 S3에 쌓이는데, 이걸 매일 밤 12시에 한 번씩 분석해서 리포트를 만들고 싶어."
    
    desc = st.text_area(
        "만들고 싶은 서비스를 자유롭게 설명해주세요:",
        value=st.session_state.input_text,
        height=150,
        placeholder="예: 강아지 산책 친구를 구하는 앱을 만들고 싶어. 위치 기반 기능이 필요하고..."
    )

    # [분석 버튼]
    if st.button("🔍 요구사항 분석 시작", use_container_width=True):
        if not desc.strip():
            st.warning("내용을 입력해주세요.")
        else:
            with st.status("🤖 요구사항을 분석하고 있습니다...", expanded=True) as status:
                req_result = analyze_requirements(requirements_agent, desc)
                if req_result.get("parse_error"):
                    status.update(label="분석 실패", state="error")
                    st.error("JSON 파싱 오류가 발생했습니다.")
                else:
                    st.session_state.requirements = req_result.get("requirements", {})
                    st.session_state.followup_questions = req_result.get("followup_questions", [])
                    st.session_state.followup_answers = {}
                    st.session_state.arch_result = None # 결과 초기화
                    status.update(label="분석 완료!", state="complete")

    # [추가 질문 섹션]
    if st.session_state.requirements:
        st.divider()
        st.subheader("✅ 분석된 핵심 요구사항")
        st.json(st.session_state.requirements, expanded=False)

        if st.session_state.followup_questions:
            st.info("더 정확한 추천을 위해 아래 질문에 답변해 주시면 좋습니다. (선택사항)")
            with st.form("followup_form"):
                new_answers = {}
                for idx, q in enumerate(st.session_state.followup_questions, start=1):
                    key = f"Q{idx}"
                    ans = st.text_input(f"Q{idx}. {q}")
                    new_answers[key] = {"question": q, "answer": ans}
                
                if st.form_submit_button("답변 적용 및 아키텍처 생성 🚀", use_container_width=True):
                    st.session_state.followup_answers = new_answers
                    # 바로 아키텍처 생성 트리거
                    with st.spinner("최적의 아키텍처를 설계 중입니다..."):
                        arch_result = recommend_architecture(
                            arch_agent,
                            st.session_state.requirements,
                            st.session_state.followup_answers,
                        )
                    if arch_result.get("parse_error"):
                        st.error("아키텍처 생성 중 오류가 발생했습니다.")
                    else:
                        st.session_state.arch_result = arch_result
        else:
            # 추가 질문이 없는 경우 바로 생성 버튼 노출
            if st.button("🚀 아키텍처 설계 실행", use_container_width=True):
                 with st.spinner("최적의 아키텍처를 설계 중입니다..."):
                    arch_result = recommend_architecture(
                        arch_agent,
                        st.session_state.requirements,
                        st.session_state.followup_answers,
                    )
                    st.session_state.arch_result = arch_result

# === [오른쪽 컬럼] 결과 출력 단계 ===
with col_right:
    st.header("🏗️ 2. 아키텍처 설계 결과")

    if st.session_state.arch_result:
        arch = st.session_state.arch_result
        
        # [수정됨] 탭 구조 개선 (요약 / 코드 / JSON)
        tab1, tab2, tab3 = st.tabs(["📊 아키텍처 요약", "💻 IaC 코드 & 가이드", "⚙️ 원본 데이터"])

        # --- 탭 1: 요약 ---
        with tab1:
            # 패턴 이름 강조
            st.success(f"### 💡 추천 패턴: {arch.get('selected_pattern_name')}")
            
            st.markdown("#### 📐 구조도 (Text Diagram)")
            st.code(arch.get("architecture_diagram_text"), language="text")

            st.markdown("#### 🛠️ 사용되는 핵심 서비스")
            services = arch.get("services_detail", [])
            for s in services:
                st.markdown(f"- **{s.get('service')}**: {s.get('role')}")

            st.markdown("---")
            
            # 이유 설명 (컬럼으로 분리)
            r_col1, r_col2 = st.columns(2)
            reasoning = arch.get("reasoning", {})
            
            with r_col1:
                st.markdown("##### 👍 장점 (Pros)")
                for p in reasoning.get("pros", []):
                    st.write(f"✔️ {p}")
            
            with r_col2:
                st.markdown("##### ⚠️ 주의사항 (Cons)")
                for c in reasoning.get("cons", []):
                    st.write(f"❗ {c}")

            if reasoning.get("fit_to_requirements"):
                st.info(f"**선정 이유:** {reasoning.get('fit_to_requirements')}")

        # --- 탭 2: IaC & 가이드 ---
        with tab2:
            st.subheader("💻 인프라 코드 (IaC)")
            st.caption("이 코드를 복사해서 바로 인프라를 배포할 수 있습니다.")
            
            iac = arch.get("iac_snippets", {})
            
            # IaC 선택 라디오 버튼
            iac_type = st.radio("포맷 선택", ["Terraform (HCL)", "CloudFormation (YAML)"], horizontal=True)
            
            if iac_type == "Terraform (HCL)":
                code = iac.get("terraform_hcl", "# Terraform 코드가 생성되지 않았습니다.")
                st.code(code, language="hcl")
            else:
                code = iac.get("cloudformation_yaml", "# CloudFormation 코드가 생성되지 않았습니다.")
                st.code(code, language="yaml")

            st.markdown("---")
            st.subheader("📖 설정 가이드")
            setup = arch.get("setup_guide", {})
            
            with st.expander("AWS 콘솔에서 직접 만들기 (클릭해서 펼치기)"):
                for i, step in enumerate(setup.get("console_steps", []), 1):
                    st.write(f"**{i}.** {step}")

            with st.expander("AWS CLI 명령어 보기"):
                for cmd in setup.get("cli_examples", []):
                    st.code(cmd, language="bash")

        # --- 탭 3: JSON ---
        with tab3:
            st.subheader("🔍 디버깅용 원본 JSON")
            st.json(arch)

    else:
        # 결과가 없을 때 보여줄 플레이스홀더
        st.info("👈 왼쪽에서 서비스 내용을 입력하고 '분석 시작'을 눌러주세요.")
        st.markdown("""
        **사용 가이드:**
        1. 만들고 싶은 서비스를 왼쪽 입력창에 적습니다.
        2. [요구사항 분석] 버튼을 누릅니다.
        3. 필요하다면 추가 질문에 답하고 [아키텍처 설계] 버튼을 누릅니다.
        4. 오른쪽에서 설계된 아키텍처와 코드를 확인합니다.
        """)