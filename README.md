# Wikipedia MCP Server

Wikipedia API를 사용해 문서를 검색하고, 가장 관련 높은 문서의 요약을 반환하는 Python FastAPI 기반 MCP Server입니다.

## 기능

- `wikipedia_search`: 키워드로 English Wikipedia 문서를 검색합니다.
- `wikipedia_summary`: 문서 제목으로 Wikipedia 요약을 가져옵니다.
- `wikipedia_answer`: 인물, 국가, 기술, 역사 등 자연어 질문을 검색어로 사용해 가장 적절한 문서를 고르고 요약을 반환합니다.
- REST API도 함께 제공합니다.

## API

이 서버는 아래 Wikipedia API를 사용합니다.

- 검색: `https://en.wikipedia.org/w/api.php?action=query&list=search&format=json&srsearch={keyword}`
- 문서 요약: `https://en.wikipedia.org/api/rest_v1/page/summary/{title}`

## 로컬 실행

Python 3.11 이상이 필요합니다.

```bash
python -m venv .venv
.venv\Scripts\activate
pip install .
uvicorn wikipedia_mcp.app:app --reload --host 0.0.0.0 --port 8000
```

macOS/Linux에서는 가상환경 활성화 명령만 다릅니다.

```bash
source .venv/bin/activate
```

서버가 실행되면 아래 주소를 사용할 수 있습니다.

- Health check: `http://localhost:8000/health`
- REST search: `http://localhost:8000/api/search?keyword=Alan%20Turing`
- REST summary: `http://localhost:8000/api/summary/Alan%20Turing`
- REST answer: `http://localhost:8000/api/answer?question=Who%20invented%20the%20World%20Wide%20Web`
- MCP endpoint: `http://localhost:8000/mcp`
- OpenAPI docs: `http://localhost:8000/docs`

## MCP Inspector로 테스트

서버를 먼저 실행한 뒤, 다른 터미널에서 MCP Inspector를 실행합니다.

```bash
npx -y @modelcontextprotocol/inspector
```

Inspector에서 transport는 `Streamable HTTP`, URL은 아래로 설정합니다.

```text
http://localhost:8000/mcp
```

사용 가능한 MCP tool은 다음과 같습니다.

```text
wikipedia_search(keyword: str, limit: int = 5)
wikipedia_summary(title: str)
wikipedia_answer(question: str, limit: int = 5)
```

예시 질문:

```text
What is quantum computing?
Who was Cleopatra?
Tell me about the history of Korea.
```

## Render 배포

이 저장소에는 Render 배포용 `render.yaml`과 `Procfile`이 포함되어 있습니다.

1. GitHub에 이 프로젝트를 push합니다.
2. Render Dashboard에서 **New +**를 누릅니다.
3. **Blueprint**를 선택하고 이 저장소를 연결합니다.
4. Render가 `render.yaml`을 읽어 web service를 생성합니다.
5. 배포가 끝나면 아래 주소로 확인합니다.

```text
https://YOUR_RENDER_SERVICE.onrender.com/health
https://YOUR_RENDER_SERVICE.onrender.com/mcp
```

Blueprint를 사용하지 않고 Web Service로 직접 만들 경우:

- Build Command: `pip install .`
- Start Command: `uvicorn wikipedia_mcp.app:app --host 0.0.0.0 --port $PORT`
- Health Check Path: `/health`

## Claude, Cursor 등 MCP 클라이언트 연결

HTTP MCP 연결을 지원하는 클라이언트에서 URL을 Render 주소로 설정합니다.

```text
https://YOUR_RENDER_SERVICE.onrender.com/mcp
```

로컬에서는 다음 URL을 사용합니다.

```text
http://localhost:8000/mcp
```

## 프로젝트 구조

```text
.
├── Procfile
├── README.md
├── pyproject.toml
├── render.yaml
└── src
    └── wikipedia_mcp
        ├── __init__.py
        ├── app.py
        └── wikipedia.py
```

## 참고

- 현재 구현은 English Wikipedia를 대상으로 합니다.
- `wikipedia_answer`는 Wikipedia 검색 결과의 첫 번째 문서를 가장 적절한 문서로 선택합니다.
- 검색 결과가 없거나 요약이 없는 문서는 에러로 반환합니다.

