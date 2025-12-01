# src/cloud_agent_streamlit.py

import json
import io
import streamlit as st


from cloud_agent import (
    create_agents,
    analyze_requirements,
    recommend_architecture,
)
from aws_patterns import AWS_PATTERNS  # 패턴 메타데이터(비용/비교용)
from infra_deploy import DEPLOYERS

# ─────────────────────────────────────────────────────────────
# 0. (발표용) boto3 자동 배포 데모 코드 문자열
# ─────────────────────────────────────────────────────────────
BOTO3_DEPLOY_EXAMPLE = """\
import boto3

def deploy_small_serverless_web(project_name: str, region: str = "ap-northeast-2"):
    \"\"\"데모용: 소규모 서버리스 웹 아키텍처의 일부를 실제 AWS에 생성하는 예시 코드입니다.
    실제로 실행할 때는 IAM 권한과 과금, 삭제 전략을 반드시 확인해야 합니다.
    \"\"\"
    s3 = boto3.client("s3", region_name=region)
    bucket_name = f"{project_name}-static-site"

    # 1) S3 버킷 생성
    s3.create_bucket(
        Bucket=bucket_name,
        CreateBucketConfiguration={"LocationConstraint": region},
    )

    # TODO: 2) 정적 웹 호스팅 설정, 3) CloudFront, API Gateway, Lambda, DynamoDB 등
    # 추가 리소스 생성 로직을 여기에 작성

    return {"bucket_name": bucket_name}
"""

# ─────────────────────────────────────────────────────────────
# 1. 페이지 설정 & 세션 상태
# ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="클라우드 서비스 추천 Agent",
    page_icon="☁️",
    layout="wide",
)

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
if "input_text" not in st.session_state:
    st.session_state.input_text = ""

# cloud_agent.create_agents()가 (requirements_agent, arch_agent, iac_agent) 를 리턴하므로
requirements_agent, arch_agent, _ = st.session_state.agents

# ─────────────────────────────────────────────────────────────
# 2. 헤더
# ─────────────────────────────────────────────────────────────
st.title("☁️ 클라우드 아키텍처 설계 에이전트")
st.markdown(
    """
이 에이전트는 사용자의 **자연어 설명**을 분석하여,  
가장 적합한 **AWS 아키텍처 패턴**을 추천하고  
필요 시 **IaC 코드(Terraform / CloudFormation)** 예시까지 제공합니다.
"""
)
st.divider()

# ─────────────────────────────────────────────────────────────
# 3. 2단 레이아웃
# ─────────────────────────────────────────────────────────────
col_left, col_right = st.columns([1, 1.2], gap="large")

# === [왼쪽] 요구사항 입력 & 분석 ===
with col_left:
    st.header("📝 1. 서비스 요구사항 입력")

    preset = st.selectbox(
        "💡 예시 시나리오 선택 (직접 입력 가능)",
        (
            "직접 작성",
            "대학생 동아리용 소규모 게시판 (비용 민감)",
            "트래픽이 급증하는 티켓 예매 사이트",
            "매일 밤 로그를 분석하는 데이터 파이프라인",
        ),
    )

    # 프리셋 선택 시 텍스트 자동 채움
    if preset != "직접 작성":
        if preset == "대학생 동아리용 소규모 게시판 (비용 민감)":
            st.session_state.input_text = (
                "동아리원 50명 정도가 쓸 게시판이야. "
                "돈이 거의 안 들었으면 좋겠고 관리하기도 귀찮아."
            )
        elif preset == "트래픽이 급증하는 티켓 예매 사이트":
            st.session_state.input_text = (
                "유명 가수 콘서트 티켓팅 사이트야. "
                "평소엔 조용한데 오픈 1분 만에 10만 명이 몰릴 수 있어. 절대 죽으면 안 돼."
            )
        elif preset == "매일 밤 로그를 분석하는 데이터 파이프라인":
            st.session_state.input_text = (
                "서버 로그가 S3에 쌓이는데, "
                "이걸 매일 밤 12시에 한 번씩 분석해서 리포트를 만들고 싶어."
            )
    else:
        # 직접 작성 모드일 때는 기존 입력 유지
        if not st.session_state.input_text:
            st.session_state.input_text = ""

    desc = st.text_area(
        "만들고 싶은 서비스를 자유롭게 설명해주세요:",
        value=st.session_state.input_text,
        height=150,
        placeholder="예: 강아지 산책 친구를 구하는 앱을 만들고 싶어. 위치 기반 기능이 필요하고...",
    )

    # [요구사항 분석 버튼]
    if st.button("🔍 요구사항 분석 시작", use_container_width=True):
        if not desc.strip():
            st.warning("내용을 입력해주세요.")
        else:
            with st.status(
                "🤖 요구사항을 분석하고 있습니다...", expanded=True
            ) as status:
                req_result = analyze_requirements(requirements_agent, desc)
                if req_result.get("parse_error"):
                    status.update(label="분석 실패", state="error")
                    st.error("JSON 파싱 오류가 발생했습니다.")
                else:
                    st.session_state.requirements = req_result.get("requirements", {})
                    st.session_state.followup_questions = req_result.get(
                        "followup_questions", []
                    )
                    st.session_state.followup_answers = {}
                    st.session_state.arch_result = None
                    status.update(label="분석 완료!", state="complete")

    # 분석 결과 / 추가 질문
    if st.session_state.requirements:
        st.divider()
        st.subheader("✅ 분석된 핵심 요구사항")
        st.json(st.session_state.requirements, expanded=False)

        if st.session_state.followup_questions:
            st.info(
                "더 정확한 추천을 위해 아래 질문에 답변해 주시면 좋습니다. (선택사항)"
            )
            with st.form("followup_form"):
                new_answers = {}
                last_question = None
                q_index = 1

                # 같은 질문이 두 번 들어오는 LLM 버그 방어
                for q in st.session_state.followup_questions:
                    if q == last_question:
                        continue
                    key = f"Q{q_index}"
                    ans = st.text_input(f"Q{q_index}. {q}")
                    new_answers[key] = {"question": q, "answer": ans}
                    last_question = q
                    q_index += 1

                if st.form_submit_button(
                    "답변 적용 및 아키텍처 생성 🚀", use_container_width=True
                ):
                    st.session_state.followup_answers = new_answers
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
            # 추가 질문이 없으면 바로 아키텍처 생성 버튼
            if st.button("🚀 아키텍처 설계 실행", use_container_width=True):
                with st.spinner("최적의 아키텍처를 설계 중입니다..."):
                    arch_result = recommend_architecture(
                        arch_agent,
                        st.session_state.requirements,
                        st.session_state.followup_answers,
                    )
                    st.session_state.arch_result = arch_result

# === [오른쪽] 아키텍처 결과 ===
with col_right:
    st.header("🏗️ 2. 아키텍처 설계 결과")

    arch = st.session_state.arch_result

    if arch:
        # 탭: 요약 / IaC & 가이드 / JSON / 패턴 비교
        tab1, tab2, tab3, tab4 = st.tabs(
            [
                "📊 아키텍처 요약",
                "💻 IaC 코드 & 가이드",
                "⚙️ 원본 데이터",
                "📈 패턴 비교",
            ]
        )

        # ─────────────────────────────────────
        # 탭 1: 요약
        # ─────────────────────────────────────
        with tab1:
            st.success(f"### 💡 추천 패턴: {arch.get('selected_pattern_name')}")

            st.markdown("#### 📐 구조도 (Text Diagram)")
            st.code(arch.get("architecture_diagram_text", ""), language="text")

            st.markdown("#### 🛠️ 사용되는 핵심 서비스")
            services = arch.get("services_detail", [])
            for s in services:
                st.markdown(f"- **{s.get('service')}**: {s.get('role')}")

            st.markdown("---")

            reasoning = arch.get("reasoning", {})
            r_col1, r_col2 = st.columns(2)

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

            # 🔹 비용 힌트 추가
            selected_id = arch.get("selected_pattern_id")
            cost_hint = None
            if selected_id:
                for p in AWS_PATTERNS:
                    if p.get("id") == selected_id:
                        cost_hint = p.get("cost_hint")
                        break

            st.markdown("---")
            st.markdown("#### 💰 대략적인 비용 가이드")
            if cost_hint:
                st.write(f"- **예상 기본 비용 범위:** {cost_hint.get('monthly_base')}")
                st.write("- **비용에 크게 영향을 주는 요소들:**")
                for f in cost_hint.get("major_factors", []):
                    st.write(f"  • {f}")
            else:
                st.write("이 패턴에 대한 비용 정보가 정의되어 있지 않습니다.")

        # ─────────────────────────────────────
        # 탭 2: IaC 코드 & 가이드
        # ─────────────────────────────────────
        with tab2:
            st.subheader("💻 인프라 코드 (IaC)")
            st.caption(
                "이 코드를 복사하거나 파일로 내려받아 인프라를 배포할 수 있습니다."
            )

            iac = arch.get("iac_snippets", {})

            iac_type = st.radio(
                "포맷 선택",
                ["Terraform (HCL)", "CloudFormation (YAML)"],
                horizontal=True,
            )

            if iac_type == "Terraform (HCL)":
                code = iac.get(
                    "terraform_hcl", "# Terraform 코드가 생성되지 않았습니다."
                )
                st.code(code, language="hcl")
            else:
                code = iac.get(
                    "cloudformation_yaml",
                    "# CloudFormation 코드가 생성되지 않았습니다.",
                )
                st.code(code, language="yaml")

            # 🔹 IaC 파일 다운로드 버튼
            st.markdown("##### 📥 IaC 파일로 다운로드")
            tf_code = iac.get("terraform_hcl", "")
            cf_code = iac.get("cloudformation_yaml", "")

            dl_col1, dl_col2 = st.columns(2)
            with dl_col1:
                if tf_code:
                    st.download_button(
                        "Terraform(main.tf) 다운로드",
                        data=tf_code.encode("utf-8"),
                        file_name="main.tf",
                        mime="text/plain",
                        use_container_width=True,
                    )
                else:
                    st.button(
                        "Terraform 코드 없음",
                        disabled=True,
                        use_container_width=True,
                    )
            with dl_col2:
                if cf_code:
                    st.download_button(
                        "CloudFormation(YAML) 다운로드",
                        data=cf_code.encode("utf-8"),
                        file_name="cloudformation_template.yaml",
                        mime="text/yaml",
                        use_container_width=True,
                    )
                else:
                    st.button(
                        "CloudFormation 코드 없음",
                        disabled=True,
                        use_container_width=True,
                    )

            st.markdown("---")
            st.subheader("📖 설정 가이드")
            setup = arch.get("setup_guide", {})

            with st.expander("AWS 콘솔에서 직접 만들기 (클릭해서 펼치기)"):
                for i, step in enumerate(setup.get("console_steps", []), 1):
                    st.write(f"**{i}.** {step}")

            with st.expander("AWS CLI 명령어 보기"):
                for cmd in setup.get("cli_examples", []):
                    st.code(cmd, language="bash")

            # 🔹 실제 AWS에 데모로 배포하는 버튼 (선택 기능)
        st.markdown("---")
        st.subheader("🚀 실제 AWS 계정에 데모로 배포해 보기")

        st.caption(
            "※ 과금 / 리소스 정리를 직접 책임질 수 있을 때만 사용하세요.\n"
            "   학교 과제 데모용으로 S3 + DynamoDB 정도만 생성합니다."
        )

        selected_pattern_id = arch.get("selected_pattern_id")

        if not selected_pattern_id or selected_pattern_id not in DEPLOYERS:
            st.warning(
                "이 패턴은 아직 자동 배포 함수가 연결되지 않았습니다. "
                "현재는 `소규모 서버리스 웹 서비스` 패턴만 데모 지원합니다."
            )
        else:
            # 프로젝트 이름 & 리전 선택
            proj_col, region_col = st.columns(2)
            with proj_col:
                project_name = st.text_input(
                    "프로젝트 이름 (리소스 이름 prefix)",
                    value="demo-project",
                    help="예: smart-kitchen, club-board 등. S3 버킷 이름에 들어갑니다.",
                )
            with region_col:
                region = st.selectbox(
                    "배포 리전 선택",
                    options=[
                        "ap-northeast-2",  # 서울
                        "ap-northeast-1",  # 도쿄
                        "us-east-1",
                    ],
                    index=0,
                )

            if st.button(
                "⚠️ 이 패턴으로 실제 AWS에 데모 리소스 생성하기",
                type="primary",
                use_container_width=True,
            ):
                if not project_name.strip():
                    st.error("프로젝트 이름을 입력해주세요.")
                else:
                    deploy_fn = DEPLOYERS[selected_pattern_id]
                    with st.spinner("boto3로 AWS 리소스를 생성하는 중입니다..."):
                        try:
                            result = deploy_fn(project_name.strip(), region)
                            st.success("✅ 데모 리소스 생성 요청을 완료했습니다.")
                            st.write("생성/시도 결과 로그:")
                            for line in result.get("logs", []):
                                st.text(line)
                            st.info(
                                "AWS 콘솔에서 S3 / DynamoDB에 들어가 "
                                f"`{result.get('bucket_name')}` / "
                                f"`{result.get('table_name')}` 리소스를 확인해 보세요."
                            )
                        except Exception as e:
                            st.error(f"리소스 생성 중 오류가 발생했습니다: {e}")

        # ─────────────────────────────────────
        # 탭 3: 원본 JSON
        # ─────────────────────────────────────
        with tab3:
            st.subheader("🔍 디버깅용 원본 JSON")
            st.json(arch)

        # ─────────────────────────────────────
        # 탭 4: 패턴 비교
        # ─────────────────────────────────────
        with tab4:
            st.subheader("📈 다른 패턴과 비교")

            selected_id = arch.get("selected_pattern_id")
            if not selected_id:
                st.info("선택된 패턴 ID가 없어 패턴 비교를 할 수 없습니다.")
            else:
                for p in AWS_PATTERNS:
                    is_selected = p.get("id") == selected_id
                    title = f"✅ {p['name']}" if is_selected else p["name"]
                    st.markdown(f"### {title}")

                    when = p.get("when", {})
                    st.write(f"- **트래픽 전제:** {when.get('traffic')}")
                    st.write(f"- **응답 지연 요구:** {when.get('latency')}")
                    st.write(f"- **예산 특성:** {when.get('budget')}")
                    st.write(f"- **운영 팀 규모:** {when.get('ops_team')}")

                    st.write(f"- **장점:** {', '.join(p.get('pros', []))}")
                    st.write(f"- **단점:** {', '.join(p.get('cons', []))}")

                    cost_hint = p.get("cost_hint")
                    if cost_hint:
                        st.write(
                            f"- **대략적인 비용 범위:** {cost_hint.get('monthly_base')}"
                        )

                    st.markdown("---")

    else:
        st.info("👈 왼쪽에서 서비스 내용을 입력하고 '요구사항 분석 시작'을 눌러주세요.")
        st.markdown(
            """
        **사용 가이드:**
        1. 만들고 싶은 서비스를 왼쪽 입력창에 적습니다.
        2. `🔍 요구사항 분석 시작` 버튼을 누릅니다.
        3. 필요하다면 추가 질문에 답하고 `아키텍처 설계` 버튼을 누릅니다.
        4. 오른쪽에서 설계된 아키텍처, 비용 힌트, IaC 코드 및 비교 결과를 확인합니다.
        """
        )
