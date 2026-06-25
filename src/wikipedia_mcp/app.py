from __future__ import annotations

import contextlib
import os
from typing import Annotated

import uvicorn
from fastapi import FastAPI, HTTPException, Path, Query
from fastapi.middleware.cors import CORSMiddleware
from mcp.server.fastmcp import FastMCP

from wikipedia_mcp.wikipedia import (
    ArticleSummary,
    QuestionAnswer,
    SearchResponse,
    WikipediaError,
    answer_wikipedia_question,
    get_wikipedia_summary,
    search_wikipedia,
)

mcp = FastMCP(
    "Wikipedia Search MCP Server",
    host="0.0.0.0",
    stateless_http=True,
    json_response=True,
    streamable_http_path="/",
)


@mcp.tool()
async def wikipedia_search(keyword: str, limit: int = 5) -> SearchResponse:
    """Search English Wikipedia articles by keyword and return ranked candidates."""
    return await search_wikipedia(keyword, limit=limit)


@mcp.tool()
async def wikipedia_summary(title: str) -> ArticleSummary:
    """Return a concise summary for an English Wikipedia article title."""
    return await get_wikipedia_summary(title)


@mcp.tool()
async def wikipedia_answer(question: str, limit: int = 5) -> QuestionAnswer:
    """Search Wikipedia for a natural-language question and summarize the best article."""
    return await answer_wikipedia_question(question, limit=limit)


@mcp.resource("wikipedia://summary/{title}")
async def wikipedia_summary_resource(title: str) -> str:
    """Expose an article summary as an MCP resource."""
    summary = await get_wikipedia_summary(title)
    source = f"\n\nSource: {summary.url}" if summary.url else ""
    return f"{summary.title}\n\n{summary.extract}{source}"


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    async with mcp.session_manager.run():
        yield


app = FastAPI(
    title="Wikipedia MCP Server",
    description="Search Wikipedia and return summaries through REST endpoints and MCP tools.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["Mcp-Session-Id"],
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/search", response_model=SearchResponse)
async def rest_search(
    keyword: Annotated[str, Query(min_length=1, description="Wikipedia search keyword.")],
    limit: Annotated[int, Query(ge=1, le=10)] = 5,
) -> SearchResponse:
    try:
        return await search_wikipedia(keyword, limit=limit)
    except WikipediaError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - defensive HTTP boundary
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/api/summary/{title}", response_model=ArticleSummary)
async def rest_summary(
    title: Annotated[str, Path(min_length=1, description="Wikipedia article title.")],
) -> ArticleSummary:
    try:
        return await get_wikipedia_summary(title)
    except WikipediaError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - defensive HTTP boundary
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/api/answer", response_model=QuestionAnswer)
async def rest_answer(
    question: Annotated[str, Query(min_length=1, description="Natural-language question.")],
    limit: Annotated[int, Query(ge=1, le=10)] = 5,
) -> QuestionAnswer:
    try:
        return await answer_wikipedia_question(question, limit=limit)
    except WikipediaError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - defensive HTTP boundary
        raise HTTPException(status_code=502, detail=str(exc)) from exc


app.mount("/mcp", mcp.streamable_http_app())


def main() -> None:
    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run("wikipedia_mcp.app:app", host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
