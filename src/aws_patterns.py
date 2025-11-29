# src/aws_patterns.py

aws_patterns = [
    {
        "id": "small_serverless_web",
        "name": "소규모 서버리스 웹 서비스",
        "services": ["CloudFront", "S3", "API Gateway", "Lambda", "DynamoDB"],
        "when": {
            "traffic": "초기/소규모 트래픽, 비정기적 사용",
            "latency": "글로벌 사용자에게 정적 콘텐츠를 빠르게 제공해야 할 때",
            "budget": "초기 비용을 최소화하고, 사용량 기반 과금이 적합할 때",
            "ops_team": "서버 운영 인력이 거의 없거나 없는 팀",
        },
        "pros": [
            "서버 관리가 거의 필요 없음 (완전 관리형 서비스 위주)",
            "사용량 기반 과금으로 초기 비용 부담이 적음",
            "자동 확장 및 고가용성 기본 제공",
        ],
        "cons": [
            "Lambda 콜드 스타트로 인한 응답 지연 가능성",
            "복잡한 장기 실행 워크로드에는 부적합",
            "서비스가 커질수록 아키텍처가 복잡해질 수 있음",
        ],
    },
    {
        "id": "classic_3tier",
        "name": "클래식 3-Tier 웹 애플리케이션",
        "services": ["VPC", "ALB", "EC2 Auto Scaling", "RDS", "ElastiCache"],
        "when": {
            "traffic": "중간 이상, 비교적 지속적인 트래픽",
            "latency": "세션 관리나 캐시를 통한 빠른 응답이 중요한 서비스",
            "budget": "어느 정도의 고정 인프라 비용을 감수할 수 있을 때",
            "ops_team": "기본적인 서버/DB 운영 인력이 있는 팀",
        },
        "pros": [
            "전통적인 구조로 이해 및 운영이 비교적 쉬움",
            "RDS로 안정적인 관계형 데이터 관리",
            "Auto Scaling + ALB로 수평 확장 가능",
        ],
        "cons": [
            "EC2 인스턴스 패치/모니터링 등 운영 부담",
            "서버리스 대비 기본 비용이 높을 수 있음",
            "초기 VPC/서브넷/보안그룹 설계가 다소 복잡",
        ],
    },
    {
        "id": "batch_analytics_pipeline",
        "name": "배치 데이터 분석 파이프라인",
        "services": ["S3", "Glue", "Athena", "Lambda", "EventBridge"],
        "when": {
            "traffic": "실시간이 아닌, 주기적인 데이터 처리/분석",
            "latency": "결과를 실시간으로 볼 필요는 없고 일정 주기로 보면 되는 경우",
            "budget": "대규모 분석 플랫폼 대신, 서버리스 기반으로 비용 절감이 필요한 경우",
            "ops_team": "데이터 파이프라인 전담 인력이 많지 않은 팀",
        },
        "pros": [
            "서버리스 위주 구성으로 인프라 관리 부담 적음",
            "S3 + Athena로 저렴한 데이터 레이크/쿼리 환경 구성",
            "EventBridge로 스케줄링/이벤트 기반 배치 처리 가능",
        ],
        "cons": [
            "실시간 스트리밍 처리에는 적합하지 않음",
            "스키마/파티션 설계를 잘못하면 쿼리 비용 증가 가능",
            "Glue/Athena의 사용법을 익혀야 하는 러닝 커브 존재",
        ],
    },
]
