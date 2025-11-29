# 🌥️ 클라우드 서비스 추천 Agent
생성형 AI를 활용한 AWS 아키텍처 설계 도우미
## 📘 프로젝트 소개

클라우드 서비스 추천 Agent는 사용자가 자연어로 서비스 요구사항을 설명하면,
그 내용을 기반으로 적절한 AWS 아키텍처 패턴을 자동 추천하고,
참고용 IaC(CloudFormation / Terraform) 스니펫,
설정 가이드, 서비스 구성 설명, 아키텍처 다이어그램까지 생성해주는
경량 설계·구현 보조 Agent입니다.

## 🎯 주요 목표

자연어 요구사항 → 구조화된 요구사항(JSON) 자동 추출
요구사항 분석 기반 AWS 아키텍처 패턴 추천
맞춤형 설정 가이드(Console / CLI) 자동 생성
선택된 패턴 기반 IaC 템플릿 초안 자동 생성
학생/초급 개발자의 클라우드 설계 학습 경험 향상
소규모 팀/스타트업에서도 활용할 수 있는 실무형 프로토타입

## 🏗️ 시스템 구성
● UI 계층
- Streamlit 웹 UI
- 터미널 기반 CLI
● 핵심 로직
- 요구사항 분석 Agent
- 아키텍처 패턴 추천 Agent
- IaC 템플릿 자동 생성 Agent
- AWS 패턴 룰베이스(AWS_PATTERNS) 내장

## ⚙️ 사용 방법
<img width="1583" height="1246" alt="1단계 버튼 누름" src="https://github.com/user-attachments/assets/17dbb3ea-91a3-4e55-bdd6-b5db6eb0d696" />
사용자는 만들고 싶은 서비스를 예시에서 가져오거나 또는 직접 설명을 입력할 수 있습니다.

<img width="1667" height="1394" alt="1단계" src="https://github.com/user-attachments/assets/38532e90-d10a-4179-9220-90b37153fbc1" />
버튼 클릭 시 사용자가 입력한 정보에 맞춰서 요구사항이 요약되어 보여지며 추가 정보가 필요할 시 추가 질문을 통해서 사용자가 원하는 페이지를 잘 만들 수 있도록 도와줍니다.

<img width="1447" height="1337" alt="2단계1" src="https://github.com/user-attachments/assets/ac15f01c-509f-4d78-bdfe-d891ee2de753" />
<img width="1722" height="871" alt="2단계2" src="https://github.com/user-attachments/assets/a181c490-2b8d-44fe-a54d-c49368409bda" />
2단계 버튼 클릭 시 추천하는 아키텍처 패턴을 보여줍니다. 이 때 패턴의 사용 서비스 및 역할, 다이어그램, 장점과 단점을 같이 알려줍니다.

<img width="2677" height="1291" alt="2단계 3" src="https://github.com/user-attachments/assets/ff98c288-749e-4dad-9718-a2c4094852f6" />
세팅 가이드를 선택할 시 사용자가 어떤 순서에 따라서 만들어야 하는지에 대해 순서를 알려줍니다. 이 떄 aws cli를 사용해서 만드는 방법 또한 같이 알려줍니다.

<img width="2661" height="1300" alt="2단계 4" src="https://github.com/user-attachments/assets/0a07e360-db38-4fa0-a3e0-0b9ac1f53c38" />
<img width="2679" height="785" alt="2단계 6" src="https://github.com/user-attachments/assets/a45cfa52-21f9-4f46-bdac-edcd64fdba7e" />
<img width="2751" height="1310" alt="2단계 7" src="https://github.com/user-attachments/assets/32272340-f397-467b-85b5-19cfbb516212" />
원한다면 사용자는 IaC 코드, 또는 Raw Json 파일을 확인해볼 수 있습니다.


## 💡 예시 시나리오
시나리오 1 — 소규모 서버리스 웹 서비스

입력 예시
“하루 방문자 1,000명 미만의 웹 서비스를 만들고 싶습니다.
서버를 직접 관리하고 싶지 않고, 비용을 최소화하고 싶어요.”
결과 요약
추천 패턴: 소규모 서버리스 웹 서비스
구성: CloudFront, S3, API Gateway, Lambda, DynamoDB
IaC 예시:
- S3 정적 사이트 버킷
- DynamoDB 테이블 생성

시나리오 2 — 내부 사내 시스템(3-Tier)

“직원 50명이 사용하는 주문 관리 시스템을 만들려고 합니다.
관계형 DB가 필요하고 안정성이 중요합니다.”
추천 패턴: 클래식 3-Tier 웹 애플리케이션
구성: VPC, Subnet, ALB, EC2 Auto Scaling, RDS, ElastiCache
IaC 예시:
- VPC / Subnet
- ALB / SecurityGroup
- RDS DB Instance

시나리오 3 — 배치 로그 분석 파이프라인

“매일 새벽에 로그를 모아서 분석하고, Athena로 조회만 하면 됩니다.”
추천 패턴: 배치 데이터 분석 파이프라인
구성: S3, Glue, Athena, Lambda, EventBridge
IaC 예시:
- S3 버킷
- Glue DB
- Athena WorkGroup
