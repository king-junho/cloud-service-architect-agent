# src/cloud_agent_assignment.py

from strands import Agent
from strands.types.exceptions import MaxTokensReachedException
import os
import sys
import io
import json
from typing import Any, Tuple

# ─────────────────────────────────────────────
# 0. Bedrock 리전 고정 (논문 도우미와 동일하게 us-east-1 사용)
# ─────────────────────────────────────────────
DEFAULT_BEDROCK_REGION = "us-east-1"
os.environ.setdefault("AWS_REGION", DEFAULT_BEDROCK_REGION)
os.environ.setdefault("AWS_DEFAULT_REGION", DEFAULT_BEDROCK_REGION)

# ─────────────────────────────────────────────
# 1. AWS 아키텍처 패턴 (과제용 간단 버전)
# ─────────────────────────────────────────────
AWS_PATTERNS = [
    {
        "id": "small_serverless_web",
        "name": "소규모 서버리스 웹 서비스",
        "services": ["CloudFront", "S3", "API Gateway", "Lambda", "DynamoDB"],
        "when": {
            "traffic": "초기/소규모 트래픽, 비정기적 사용",
            "latency": "정적 콘텐츠를 글로벌하게 빠르게 제공하고 싶을 때",
            "budget": "초기 비용을 최소화하고, 사용량 기반 과금이 적합할 때",
            "ops_team": "서버 운영 인력이 거의 없거나 없는 팀",
        },
        "pros": [
            "서버 관리가 거의 필요 없음",
            "사용량 기반 과금으로 초기 비용이 낮음",
            "자동 확장 및 고가용성 기본 제공",
        ],
        "cons": [
            "Lambda 콜드 스타트로 인한 지연 가능성",
            "복잡한 장기 실행 워크로드에는 부적합",
        ],
        "iac_snippets": {
            # 정적 웹(S3) + NoSQL(DynamoDB) 중심의 최소 예시
            "cloudformation_yaml": """Resources:
  AppBucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: !Sub "${AWS::StackName}-static-site"

  AppTable:
    Type: AWS::DynamoDB::Table
    Properties:
      TableName: !Sub "${AWS::StackName}-data"
      BillingMode: PAY_PER_REQUEST
      AttributeDefinitions:
        - AttributeName: id
          AttributeType: S
      KeySchema:
        - AttributeName: id
          KeyType: HASH
""",
            "terraform_hcl": """resource "aws_s3_bucket" "app_bucket" {
  bucket = "${var.project_name}-static-site"
}

resource "aws_dynamodb_table" "app_table" {
  name         = "${var.project_name}-data"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "id"

  attribute {
    name = "id"
    type = "S"
  }
}
""",
        },
    },
    {
        "id": "classic_3tier",
        "name": "클래식 3-Tier 웹 애플리케이션",
        "services": ["VPC", "ALB", "EC2 Auto Scaling", "RDS", "ElastiCache"],
        "when": {
            "traffic": "중간 이상, 비교적 지속적인 트래픽",
            "latency": "세션/캐시를 통해 빠른 응답이 중요한 서비스",
            "budget": "어느 정도 고정 인프라 비용을 감수할 수 있을 때",
            "ops_team": "기본적인 서버/DB 운영 인력이 있는 팀",
        },
        "pros": [
            "전통적인 구조로 이해 및 운영이 쉬움",
            "RDS로 안정적인 관계형 데이터 관리",
            "Auto Scaling + ALB로 수평 확장 가능",
        ],
        "cons": [
            "EC2 인스턴스 운영/패치 부담",
            "서버리스 대비 기본 비용이 높을 수 있음",
        ],
        "iac_snippets": {
            # 매우 단순화된 3-Tier 구조 예시 (VPC/ALB/EC2/RDS 스켈레톤)
            "cloudformation_yaml": """Resources:
  AppVPC:
    Type: AWS::EC2::VPC
    Properties:
      CidrBlock: 10.0.0.0/16

  AppSubnet:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref AppVPC
      CidrBlock: 10.0.1.0/24

  AppSecurityGroup:
    Type: AWS::EC2::SecurityGroup
    Properties:
      GroupDescription: Allow HTTP
      VpcId: !Ref AppVPC
      SecurityGroupIngress:
        - IpProtocol: tcp
          FromPort: 80
          ToPort: 80
          CidrIp: 0.0.0.0/0

  AppLoadBalancer:
    Type: AWS::ElasticLoadBalancingV2::LoadBalancer
    Properties:
      Subnets:
        - !Ref AppSubnet
      SecurityGroups:
        - !Ref AppSecurityGroup

  AppDB:
    Type: AWS::RDS::DBInstance
    Properties:
      Engine: mysql
      DBInstanceClass: db.t3.micro
      AllocatedStorage: 20
      MasterUsername: admin
      MasterUserPassword: ExamplePassw0rd
""",
            "terraform_hcl": """resource "aws_vpc" "app_vpc" {
  cidr_block = "10.0.0.0/16"
}

resource "aws_subnet" "app_subnet" {
  vpc_id     = aws_vpc.app_vpc.id
  cidr_block = "10.0.1.0/24"
}

resource "aws_security_group" "app_sg" {
  name        = "app-sg"
  description = "Allow HTTP"
  vpc_id      = aws_vpc.app_vpc.id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_lb" "app_lb" {
  name               = "app-lb"
  load_balancer_type = "application"
  subnets            = [aws_subnet.app_subnet.id]
  security_groups    = [aws_security_group.app_sg.id]
}

resource "aws_db_instance" "app_db" {
  engine               = "mysql"
  instance_class       = "db.t3.micro"
  allocated_storage    = 20
  name                 = "appdb"
  username             = "admin"
  password             = "ExamplePassw0rd"
  skip_final_snapshot  = true
}
""",
        },
    },
    {
        "id": "batch_analytics_pipeline",
        "name": "배치 데이터 분석 파이프라인",
        "services": ["S3", "Glue", "Athena", "Lambda", "EventBridge"],
        "when": {
            "traffic": "실시간이 아닌, 주기적인 데이터 처리/분석",
            "latency": "결과를 실시간으로 볼 필요는 없을 때",
            "budget": "전용 분석 플랫폼 대신 서버리스 기반으로 비용 절감이 필요할 때",
            "ops_team": "데이터 파이프라인 전담 인력이 많지 않은 팀",
        },
        "pros": [
            "서버리스 위주 구성으로 인프라 관리 부담이 적음",
            "S3 + Athena로 저렴한 데이터 레이크/쿼리 환경",
        ],
        "cons": [
            "실시간 스트리밍 처리에는 부적합",
            "잘못된 스키마/파티션 설계 시 쿼리 비용 증가 가능",
        ],
        "iac_snippets": {
            # S3 데이터 레이크 + Glue DB + Athena 워크그룹 정도의 기본 골격
            "cloudformation_yaml": """Resources:
  RawDataBucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: !Sub "${AWS::StackName}-raw-data"

  GlueDatabase:
    Type: AWS::Glue::Database
    Properties:
      CatalogId: !Ref AWS::AccountId
      DatabaseInput:
        Name: !Sub "${AWS::StackName}_db"

  AthenaWorkGroup:
    Type: AWS::Athena::WorkGroup
    Properties:
      Name: !Sub "${AWS::StackName}_wg"
      State: ENABLED
""",
            "terraform_hcl": """resource "aws_s3_bucket" "raw_data" {
  bucket = "${var.project_name}-raw-data"
}

resource "aws_glue_catalog_database" "db" {
  name = "${var.project_name}_db"
}

resource "aws_athena_workgroup" "wg" {
  name = "${var.project_name}_wg"
  state = "ENABLED"
}
""",
        },
    },
]
# ─────────────────────────────────────────────
# 2. 시스템 프롬프트 (과제용, 짧고 안정적으로)
# ─────────────────────────────────────────────
REQUIREMENTS_ANALYSIS_SYSTEM_PROMPT = """
당신은 AWS 클라우드 아키텍트입니다.
사용자가 만들고 싶은 서비스에 대해 자연어로 설명하면,
서비스 요구사항을 JSON 형식으로 정리해야 합니다.

1. 먼저, 사용자의 설명만 보고 합리적으로 추론해서 아래 필드를 채우세요.
   - service_type: "웹 서비스", "내부관리도구", "배치 처리" 등
   - expected_users: "10명 미만", "10~100명", "100명 이상" 중 하나 (대략적인 추정 허용)
   - latency_sensitivity: "높음" | "보통" | "낮음"
   - budget_sensitivity: "매우 민감" | "보통" | "여유 있음"
   - ops_team_size: "1명", "2~5명", "5명 이상" 중 하나 (학생 팀이면 보통 1명 또는 2~5명)
   - data_characteristics: 데이터 유형과 특징 (정형/비정형, 트랜잭션 중요도 등)
   - availability_requirement: "매우 높음(24x7)" | "보통" | "낮음"

2. 사용자의 설명만으로는 애매해서 추론이 어려운 부분이 있다면,
   그때만 followup_questions에 자연스러운 추가 질문을 넣으세요.

   추가 질문 작성 규칙:
   - 반드시 사용자가 쓴 표현이나 키워드를 참고해서, 대화를 이어가는 느낌으로 질문하세요.
     예) 사용자가 "사내에서 쓰는 재고 관리 툴"이라고 하면:
         "사내 재고 관리 툴은 하루에 대략 몇 명 정도 사용하실 것 같아요?" 처럼 묻기
   - 선택지(예: "높음/보통/낮음")를 괄호로 나열하지 말고, 자연스러운 말로 묻습니다.
     (예: "응답 속도가 어느 정도 중요한지 알려주실 수 있을까요?")
   - 너무 교과서 같은 문장이 아니라, 실제 사람 상담처럼 편안한 존댓말을 사용하세요.
   - 질문은 최대 3개까지만 작성하세요.
   - 정말 충분히 추론 가능하면 followup_questions는 빈 배열([])로 두세요.

출력 형식(예):
{
  "requirements": {
    "service_type": "...",
    "expected_users": "...",
    "latency_sensitivity": "...",
    "budget_sensitivity": "...",
    "ops_team_size": "...",
    "data_characteristics": "...",
    "availability_requirement": "..."
  },
  "followup_questions": ["질문1", "질문2"]
}

중요:
- 반드시 위와 같은 JSON 형식만 출력하세요.
- JSON 바깥에 자연어 문장을 쓰지 마세요.
"""

# TODO: iac_snippets
#  - 현재는 LLM이 단순 스켈레톤 문자열을 생성하는 수준이지만,
#  - 나중에는 실제로 배포 가능한 CloudFormation/Terraform 템플릿 구조를 정의하고,
#    정적 분석(예: cfn-lint)으로 검증하는 단계까지 확장 가능.
ARCH_RECOMMENDATION_SYSTEM_PROMPT = """
당신은 AWS 클라우드 아키텍처 설계 도우미입니다.

입력으로:
1) 사용자의 요구사항 JSON
2) 추가 질문에 대한 답변 (있다면)
3) 미리 정의된 AWS 아키텍처 패턴 목록

이 주어집니다.

해야 할 일:
- 요구사항과 패턴의 when 조건을 비교하여 가장 적합한 패턴 1개를 선택하세요.
- 선택한 패턴의 id와 이름을 명시하세요.
- 사용되는 각 AWS 서비스의 역할을 짧게 설명하세요.
- 텍스트 기반 아키텍처 다이어그램을 한 줄으로 작성하세요.
- 왜 이 패턴을 선택했는지, 장점/단점을 간단히 설명하세요.
- AWS 관리 콘솔에서 따라할 수 있는 단계별 세팅 가이드와, 선택적인 AWS CLI 예시를 작성하세요.
- 선택적으로, 추천 아키텍처에 해당하는 IaC 스니펫(CloudFormation 또는 Terraform)을 제공하세요.

제한:
- 모든 설명은 자연스러운 한국어로 작성하세요.
- 각 문자열은 최대 1~2문장만 사용하세요.
- "pros" / "cons" 배열은 최대 3개까지만 채우세요.
- 전체 응답은 짧고 간결하게 작성하세요.

출력 형식 (반드시 이 JSON 구조만 사용):
{
  "selected_pattern_id": "...",
  "selected_pattern_name": "...",
  "services_detail": [
    {"service": "서비스이름", "role": "역할 설명"}
  ],
  "architecture_diagram_text": "사용자 -> CloudFront -> S3 -> API Gateway -> Lambda -> DynamoDB",
  "setup_guide": {
    "console_steps": [
      "1단계에서 무엇을 클릭하고 설정해야 하는지 한국어로 설명",
      "2단계 설명"
    ],
    "cli_examples": [
      "aws s3 mb s3://example-bucket",
      "aws dynamodb create-table ..."
    ]
  },
  "iac_snippets": {
    "cloudformation_yaml": "선택적. CloudFormation YAML 스켈레톤 문자열",
    "terraform_hcl": "선택적. Terraform HCL 스켈레톤 문자열"
  },
  "reasoning": {
    "fit_to_requirements": "요구사항과 어떻게 맞는지",
    "pros": ["장점1", "장점2"],
    "cons": ["단점1"],
    "tradeoffs": "간단한 트레이드오프 설명"
  }
}

중요:
- setup_guide의 설명은 실제 AWS 콘솔을 사용하는 대학생이 따라할 수 있을 정도로 구체적이어야 합니다.
- 너무 많은 서비스를 한 번에 만들지 말고, 핵심 서비스 위주로 안내하세요.
- iac_snippets는 선택 사항이지만, 가능하다면 간단한 스켈레톤을 제공하세요.
- JSON 바깥에 다른 텍스트는 쓰지 마세요.
"""
IAC_GENERATOR_SYSTEM_PROMPT = """
당신은 AWS 인프라를 코드(IaC)로 작성해 주는 도우미입니다.

입력으로는:
1) 사용자의 요구사항 JSON (requirements)
2) 선택된 아키텍처 패턴 정보 (selected_pattern_id, selected_pattern_name)
3) 사용 서비스 목록 및 역할 (services_detail)

이 정보들을 보고,
- 해당 아키텍처를 대략적으로 구현할 수 있는
  CloudFormation(YAML) 스니펫과
  Terraform(HCL) 스니펫을 생성하세요.

제약 사항:
- 과제/데모용이므로, 모든 리소스를 완벽하게 생성할 필요는 없습니다.
- 핵심 리소스 몇 개(S3, DynamoDB, VPC, RDS 등) 위주로 작성하세요.
- 비밀번호나 민감한 값은 하드코딩하지 말고 예시 값 또는 TODO 주석을 사용하세요.
- 템플릿은 실제로 CloudFormation/Terraform 문법과 최대한 호환되도록 작성하세요.
- 너무 길어지지 않도록 최소한의 리소스만 포함하세요.

출력 형식(JSON만, 설명 없이):

{
  "cloudformation_yaml": "여기에 YAML 문자열",
  "terraform_hcl": "여기에 HCL 문자열"
}

중요:
- JSON 바깥에 다른 텍스트를 출력하지 마세요.
- 코드 블록 마크다운(```yaml 같은 것)은 사용하지 마세요.
"""


# ─────────────────────────────────────────────
# 3. safe_input (논문 에이전트와 동일 패턴)
# ─────────────────────────────────────────────
def safe_input(prompt: str) -> str:
    """UTF-8 인코딩 오류를 안전하게 처리하는 input 함수."""
    try:
        return input(prompt).strip()
    except UnicodeDecodeError:
        try:
            if hasattr(sys.stdin, "buffer"):
                sys.stdin = io.TextIOWrapper(
                    sys.stdin.buffer, encoding="utf-8", errors="replace"
                )
            return input(prompt).strip()
        except (UnicodeDecodeError, UnicodeError):
            try:
                sys.stdout.write(prompt)
                sys.stdout.flush()
                line = sys.stdin.buffer.readline()
                return line.decode("utf-8", errors="replace").strip()
            except Exception:
                raise


# ─────────────────────────────────────────────
# 4. JSON 파싱 유틸 (LLM 응답 방어용)
# ─────────────────────────────────────────────
def safe_parse_json(raw: Any) -> Tuple[dict, bool]:
    """LLM/Agent 응답을 최대한 안전하게 JSON으로 파싱한다.
    반환값: (data, is_error)
    """
    # 이미 dict면 그대로
    if isinstance(raw, dict):
        return raw, False

    # dict() 메소드가 있으면 시도
    if hasattr(raw, "dict"):
        try:
            data = raw.dict()
            if isinstance(data, dict):
                return data, False
        except Exception:
            pass

    # 문자열로 변환 후 시도
    text = raw if isinstance(raw, str) else str(raw)
    text = text.strip()

    # 전체 파싱 시도
    try:
        return json.loads(text), False
    except Exception:
        pass

    # {...} 부분만 잘라서 파싱 시도
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and start < end:
        json_part = text[start : end + 1]
        try:
            return json.loads(json_part), False
        except Exception:
            pass

    # 완전 실패
    return {"raw_response": text}, True


# ─────────────────────────────────────────────
# 5. Agent 생성 (툴 없이 단순 텍스트 모델만 사용)
# ─────────────────────────────────────────────
def create_agents() -> tuple[Agent, Agent]:
    requirements_agent = Agent(
        model="us.amazon.nova-lite-v1:0",
        system_prompt=REQUIREMENTS_ANALYSIS_SYSTEM_PROMPT,
        tools=[],
    )

    arch_agent = Agent(
        model="us.amazon.nova-lite-v1:0",
        system_prompt=ARCH_RECOMMENDATION_SYSTEM_PROMPT,
        tools=[],
    )
    iac_agent = Agent(
        model="us.amazon.nova-lite-v1:0",
        system_prompt=IAC_GENERATOR_SYSTEM_PROMPT,
        tools=[],
    )

    return requirements_agent, arch_agent, iac_agent


# ─────────────────────────────────────────────
# 6. 1단계: 요구사항 분석
# ─────────────────────────────────────────────
def analyze_requirements(agent: Agent, description: str) -> dict:
    """사용자 설명 → 요구사항 JSON + 추가 질문."""
    raw_response = agent(description)
    data, is_error = safe_parse_json(raw_response)
    if is_error:
        data["parse_error"] = True
    return data


# 2단계: 아키텍처 추천
# TODO: 패턴이 5개 이상으로 늘어나면,
#       LLM에 넘기는 정보량을 줄이기 위해
#       "services"와 "when"만 추려서 보내는 경량화 버전도 고려하기.
def recommend_architecture(
    agent: Agent,
    requirements: dict,
    followup_answers: dict | None = None,
) -> dict:
    """요구사항 + 추가 답변 + 패턴 목록 → 추천 결과 JSON."""
    payload = {
        "requirements": requirements,
        "followup_answers": followup_answers or {},
        "patterns": AWS_PATTERNS,
    }
    user_message = json.dumps(payload, ensure_ascii=False, indent=2)
    raw_response = agent(user_message)
    data, is_error = safe_parse_json(raw_response)
    if is_error:
        data["parse_error"] = True
    return data


# ─────────────────────────────────────────────
# 8. 출력 예쁘게 포맷팅 (발표/데모용)
# ─────────────────────────────────────────────
def pretty_print_architecture(arch_result: dict) -> None:
    selected_name = arch_result.get("selected_pattern_name")
    selected_id = arch_result.get("selected_pattern_id")
    services_detail = arch_result.get("services_detail", [])
    diagram = arch_result.get("architecture_diagram_text")
    reasoning = arch_result.get("reasoning", {})
    setup_guide = arch_result.get("setup_guide", {})
    iac_snippets = arch_result.get("iac_snippets", {})
    print("[추천 아키텍처 요약]")

    if selected_name:
        print(f"- 선택된 패턴: {selected_name} ({selected_id})")

    if diagram:
        print("\n- 텍스트 아키텍처 다이어그램:")
        print(f"  {diagram}")

    if services_detail:
        print("\n- 사용 서비스 및 역할:")
        for s in services_detail:
            svc = s.get("service")
            role = s.get("role")
            print(f"  · {svc}: {role}")
    if setup_guide:
        console_steps = setup_guide.get("console_steps", [])
        cli_examples = setup_guide.get("cli_examples", [])

        if console_steps:
            print("\n[콘솔로 따라하는 세팅 가이드]")
            for i, step in enumerate(console_steps, start=1):
                print(f"  {i}. {step}")

        if cli_examples:
            print("\n[AWS CLI 예시 명령어]")
            for cmd in cli_examples:
                print(f"  $ {cmd}")
    if iac_snippets:
        cf = iac_snippets.get("cloudformation_yaml")
        tf = iac_snippets.get("terraform_hcl")

        if cf:
            print("\n[CloudFormation YAML 스니펫]")
            print(cf)

        if tf:
            print("\n[Terraform HCL 스니펫]")
            print(tf)

    if reasoning:
        fit = reasoning.get("fit_to_requirements")
        pros = reasoning.get("pros", [])
        cons = reasoning.get("cons", [])
        tradeoffs = reasoning.get("tradeoffs")

        if fit:
            print("\n- 요구사항 적합성:")
            print(f"  {fit}")
        if pros:
            print("\n- 장점:")
            for p in pros:
                print(f"  · {p}")
        if cons:
            print("\n- 단점/주의사항:")
            for c in cons:
                print(f"  · {c}")
        if tradeoffs:
            print("\n- 트레이드오프:")
            print(f"  {tradeoffs}")


def generate_iac_from_architecture(
    iac_agent: Agent,
    requirements: dict,
    arch_result: dict,
) -> dict:
    """요구사항 + 선택된 아키텍처를 기반으로 LLM에게 IaC 템플릿 생성을 부탁한다."""
    payload = {
        "requirements": requirements,
        "selected_pattern_id": arch_result.get("selected_pattern_id"),
        "selected_pattern_name": arch_result.get("selected_pattern_name"),
        "services_detail": arch_result.get("services_detail", []),
    }

    user_message = json.dumps(payload, ensure_ascii=False, indent=2)
    raw_response = iac_agent(user_message)
    data, is_error = safe_parse_json(raw_response)
    if is_error:
        data["parse_error"] = True
    return data


# ─────────────────────────────────────────────
# 9. main() – 논문 에이전트 스타일 CLI 루프
# ─────────────────────────────────────────────
def main():
    requirements_agent, arch_agent, iac_agent = create_agents()

    print(
        "클라우드 서비스 추천 에이전트를 시작합니다.\n"
        "만들고 싶은 서비스(웹/앱/내부 시스템 등)를 자유롭게 설명하면,\n"
        "미리 정의한 AWS 아키텍처 패턴 중 하나를 추천해줍니다.\n"
        "종료하려면 '종료', 'exit', 'quit', 'q' 중 하나를 입력하세요.\n"
    )

    while True:
        try:
            desc = safe_input("▶ 만들고 싶은 서비스 설명: ")

            if desc.lower() in ["종료", "exit", "quit", "q"]:
                print("클라우드 서비스 추천 에이전트를 종료합니다.")
                break

            if not desc:
                print("설명을 입력해주세요.\n")
                continue

            # 1단계: 요구사항 분석
            print("\n[1단계] 요구사항 분석 중...\n")
            req_result = analyze_requirements(requirements_agent, desc)

            if req_result.get("parse_error"):
                print("⚠️ 요구사항 JSON 파싱에 실패했습니다. 원본 응답:")
                print(req_result.get("raw_response"))
                print()
                continue

            requirements = req_result.get("requirements", {})
            followup_questions = req_result.get("followup_questions", [])

            print(
                "[요구사항 요약]\n",
                json.dumps(requirements, ensure_ascii=False, indent=2),
            )

            # 1.5단계: 추가 질문
            followup_answers: dict[str, dict[str, str]] = {}

            if followup_questions:
                print("\n[추가 질문] 더 정확한 추천을 위해 몇 가지를 더 여쭤볼게요.\n")

                last_question = None
                q_index = 1

                for (
                    q
                ) in (
                    followup_questions
                ):  # LLM이 같은 질문을 배열에 두 번 넣는 경우가 있어, 이때는 한 번만 물어본다.
                    if q == last_question:
                        continue

                    ans = safe_input(f"  Q{q_index}. {q}\n  → ")
                    followup_answers[f"Q{q_index}"] = {
                        "question": q,
                        "answer": ans,
                    }

                    last_question = q
                    q_index += 1

            # 2단계: 아키텍처 추천
            print("\n[2단계] AWS 아키텍처 패턴 추천 중...\n")
            try:
                arch_result = recommend_architecture(
                    arch_agent, requirements, followup_answers
                )
            except MaxTokensReachedException:
                print("⚠️ 모델이 응답을 너무 길게 생성해서 토큰 한도를 초과했습니다.")
                print("   - 서비스 설명을 조금 더 구체적이고 짧게 적어보거나,")
                print("   - 프롬프트에서 응답 길이를 더 줄이도록 제한해 주세요.\n")
                continue
            except Exception as e:
                print(f"⚠️ 아키텍처 추천 중 오류가 발생했습니다: {e}")
                continue

            if arch_result.get("parse_error"):
                print("⚠️ 아키텍처 추천 JSON 파싱에 실패했습니다. 원본 응답:")
                print(arch_result.get("raw_response"))
                print()
                continue

            # 2.5단계: IaC 자동 생성 (여기로 당겨오기)
            print(
                "\n[IaC] 선택된 아키텍처 기반으로 CloudFormation/Terraform 예시 생성 중...\n"
            )
            iac_result = generate_iac_from_architecture(
                iac_agent, requirements, arch_result
            )

            if not iac_result.get("parse_error"):
                arch_result["iac_snippets"] = {
                    "cloudformation_yaml": iac_result.get("cloudformation_yaml", ""),
                    "terraform_hcl": iac_result.get("terraform_hcl", ""),
                }
            else:
                print("⚠️ IaC JSON 파싱에 실패했습니다. 원본 응답:")
                print(iac_result.get("raw_response"))

            # RAW JSON 출력 (보고서용)
            print(
                "[추천 결과 RAW JSON]\n",
                json.dumps(arch_result, ensure_ascii=False, indent=2),
            )

            print()
            pretty_print_architecture(arch_result)

            print("\n--- 다른 서비스를 추천받으려면 새로 설명을 입력하세요. ---\n")

        except KeyboardInterrupt:
            print("\n\n클라우드 서비스 추천 에이전트를 종료합니다.")
            break
        except EOFError:
            print("\n\n클라우드 서비스 추천 에이전트를 종료합니다.")
            break


# TODO: 고급 버전
#  - boto3를 이용해 실제 AWS 리소스를 생성하는 @tool 함수들을 정의할 수 있음.
#    예) create_s3_static_site(), create_lambda_api(), create_dynamodb_table()
#  - arch_agent에 해당 툴을 연결하여,
#    사용자가 "진짜로 인프라 생성해줘"라고 요청하면 툴 호출 기반으로 구성하도록 확장.
#  - 이 경우 IAM 권한, 비용, 리소스 삭제 전략까지 함께 설계 필요.

if __name__ == "__main__":
    main()
