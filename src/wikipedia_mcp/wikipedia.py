from __future__ import annotations

import html
import re
from typing import Any
from urllib.parse import quote

import httpx
from pydantic import BaseModel, Field

WIKIPEDIA_API_URL = "https://en.wikipedia.org/w/api.php"
WIKIPEDIA_REST_URL = "https://en.wikipedia.org/api/rest_v1/page/summary"
USER_AGENT = "wikipedia-mcp-server/0.1.0 (https://github.com/example/wikipedia-mcp-server)"


class WikipediaError(RuntimeError):
    """Raised when Wikipedia cannot return a useful response."""


class SearchResult(BaseModel):
    title: str
    pageid: int
    snippet: str = Field(description="HTML-stripped search snippet from Wikipedia.")
    wordcount: int | None = None
    timestamp: str | None = None


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResult]


class ArticleSummary(BaseModel):
    title: str
    description: str | None = None
    extract: str
    url: str | None = None
    thumbnail: str | None = None


class QuestionAnswer(BaseModel):
    question: str
    selected_title: str
    summary: ArticleSummary
    candidates: list[SearchResult]


async def search_wikipedia(keyword: str, limit: int = 5) -> SearchResponse:
    keyword = keyword.strip()
    if not keyword:
        raise WikipediaError("Search keyword must not be empty.")

    params: dict[str, Any] = {
        "action": "query",
        "list": "search",
        "format": "json",
        "srsearch": keyword,
        "srlimit": max(1, min(limit, 10)),
    }

    async with httpx.AsyncClient(headers={"User-Agent": USER_AGENT}, timeout=10.0) as client:
        response = await client.get(WIKIPEDIA_API_URL, params=params)
        response.raise_for_status()
        payload = response.json()

    results = [
        SearchResult(
            title=item["title"],
            pageid=item["pageid"],
            snippet=_strip_search_snippet(item.get("snippet", "")),
            wordcount=item.get("wordcount"),
            timestamp=item.get("timestamp"),
        )
        for item in payload.get("query", {}).get("search", [])
    ]
    return SearchResponse(query=keyword, results=results)


async def get_wikipedia_summary(title: str) -> ArticleSummary:
    title = title.strip()
    if not title:
        raise WikipediaError("Article title must not be empty.")

    encoded_title = quote(title.replace(" ", "_"), safe="")
    url = f"{WIKIPEDIA_REST_URL}/{encoded_title}"

    async with httpx.AsyncClient(headers={"User-Agent": USER_AGENT}, timeout=10.0) as client:
        response = await client.get(url)
        if response.status_code == 404:
            raise WikipediaError(f"Wikipedia article not found: {title}")
        response.raise_for_status()
        payload = response.json()

    extract = payload.get("extract")
    if not extract:
        raise WikipediaError(f"Wikipedia summary is empty: {title}")

    content_urls = payload.get("content_urls") or {}
    desktop_urls = content_urls.get("desktop") or {}
    thumbnail = payload.get("thumbnail") or {}

    return ArticleSummary(
        title=payload.get("title", title),
        description=payload.get("description"),
        extract=extract,
        url=desktop_urls.get("page"),
        thumbnail=thumbnail.get("source"),
    )


async def answer_wikipedia_question(question: str, limit: int = 5) -> QuestionAnswer:
    search = await search_wikipedia(question, limit=limit)
    if not search.results:
        raise WikipediaError(f"No Wikipedia search results for: {question}")

    selected = search.results[0]
    summary = await get_wikipedia_summary(selected.title)
    return QuestionAnswer(
        question=question,
        selected_title=selected.title,
        summary=summary,
        candidates=search.results,
    )


def _strip_search_snippet(snippet: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", snippet))
