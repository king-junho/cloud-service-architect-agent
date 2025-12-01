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
<img width="1750" height="1062" alt="1단계" src="https://github.com/user-attachments/assets/b14479c1-efb1-4ed5-9376-ff41f006ac44" />
사용자는 만들고 싶은 서비스를 예시에서 가져오거나 또는 직접 설명을 입력할 수 있습니다.

<img width="1676" height="1132" alt="1단계 버튼누름" src="https://github.com/user-attachments/assets/a97c32d4-66db-4267-97c8-8dd0f093aad6" />
분석 시작 버튼 클릭 시 사용자가 입력한 정보에 맞춰서 요구사항이 요약되어 보여지며 추가 정보가 필요할 시 추가 질문을 통해서 사용자가 원하는 페이지를 잘 만들 수 있도록 도와줍니다.

<img width="946" height="932" alt="2-1" src="https://github.com/user-attachments/assets/0f556f37-6c0c-4858-8444-aaa4c83692cf" />
<img width="995" height="997" alt="2-2" src="https://github.com/user-attachments/assets/0597f3a4-a0ff-4c72-9749-a9f3efaab9e5" />
설계 실행 버튼 클릭 시 추천하는 아키텍처 패턴을 보여줍니다. 이 때 패턴의 핵심 서비스 및 구조도, 장점과 주의사항, 비용 가이드를 같이 알려줍니다.

<img width="960" height="1123" alt="2-3" src="https://github.com/user-attachments/assets/d34b9b02-7e2b-47cb-8fa3-9886cc630f15" />
<img width="924" height="479" alt="2-4" src="https://github.com/user-attachments/assets/db40954e-b19d-4a8b-abb8-28b8433f0344" />
사용자는 IaC 코드를 확인하고 다운로드 할 수 있으며 밑의 가이드를 통해서 어떻게 해야 할지 더욱 자세하게 알 수 있습니다

<img width="950" height="1179" alt="2-5" src="https://github.com/user-attachments/assets/ae4b3356-a776-449d-aa83-206e7336384b" />
사용자는 원본 Json 파일을 확인하고 이를 참고할 수도 있습니다.

<img width="1069" height="1326" alt="2-7" src="https://github.com/user-attachments/assets/26eb0d15-a521-450e-8317-015358826fa3" />
<img width="918" height="927" alt="2-6" src="https://github.com/user-attachments/assets/3d0ee74f-1088-4ab5-b5c7-d5a0ee4b703a" />
다른 패턴과의 비교를 통해서 왜 이러한 패턴을 사용해야 하는지 알 수 있습니다.


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

