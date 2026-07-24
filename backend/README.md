# Clinical Trial Tracker — Backend

FastAPI 기반 백엔드. 패키지 관리는 [uv](https://docs.astral.sh/uv/)를 사용한다.

## 개발 계획

프로젝트 목표/사용자 요구사항/기능 명세는 다음 문서를 참고한다.

- [../docs/01-project-goals.mdc](../docs/01-project-goals.mdc)
- [../docs/02-user-requirements.mdc](../docs/02-user-requirements.mdc)
- [../docs/03-feature-spec.mdc](../docs/03-feature-spec.mdc)

## 시작하기

```bash
# 의존성 설치 (가상환경 자동 생성)
uv sync

# 개발 서버 실행
uv run fastapi dev app/main.py

# 테스트 실행 (TDD)
uv run pytest

# 린트 검사
uv run ruff check .
```

## 폴더 구조

```
app/
  api/            # FastAPI 라우터
  core/           # 설정, 공통 유틸
  domain/         # Pydantic 도메인 모델 (UserProfile, ClinicalTrial 등)
  services/       # 비즈니스 로직 (매칭 엔진 등)
  infrastructure/ # DB, 외부 API 클라이언트 (ClinicalTrials.gov 등)
  main.py         # FastAPI 앱 진입점
tests/            # pytest 테스트 (TDD: 테스트 우선 작성)
```

## 개발 원칙

- **TDD**: 기능 코드를 작성하기 전에 실패하는 테스트를 먼저 작성한다 (Red → Green → Refactor)
- **Clean Code**: 계층 간 낮은 결합도를 유지하고, 매칭 로직 등 핵심 비즈니스 로직은 인터페이스 뒤에 추상화하여 구현체 교체가 가능하도록 설계한다
