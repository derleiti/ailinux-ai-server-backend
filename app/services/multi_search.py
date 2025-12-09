"""
AILinux Multi-Search Service v1.0
================================
Aggregiert Ergebnisse aus mehreren Such-APIs:
- SearXNG (self-hosted, 247 Engines)
- DuckDuckGo (direkt)
- Wiby.me (Indie Web)
- Wikipedia
- Mesh AI Filtering für Relevanz

Author: AILinux Team
"""

from __future__ import annotations
import asyncio
import aiohttp
import logging
import time
import hashlib
import html
import re
from typing import List, Dict, Any, Set, Optional
from dataclasses import dataclass, field

logger = logging.getLogger("ailinux.multi_search")

# ============================================================
# Configuration
# ============================================================

@dataclass
class SearchConfig:
    """Zentrale Such-Konfiguration."""
    searxng_url: str = "http://localhost:8089"
    cache_ttl: int = 600
    max_cache_size: int = 500
    default_lang: str = "de"
    timeout: int = 10
    
    # API Weights für Ranking - Knowledge sources get higher priority
    source_weights: Dict[str, float] = field(default_factory=lambda: {
        "google": 1.2,          # Primary search engine
        "wikipedia": 1.5,       # High-quality knowledge (boosted)
        "grokipedia": 1.4,      # AI knowledge base (boosted)
        "searxng": 1.0,         # Meta-search
        "duckduckgo": 0.9,      # Privacy search
        "ailinux_news": 0.85,   # Tech news
        "github": 0.8,          # Code/docs
        "stackoverflow": 0.8,   # Q&A
        "wiby": 0.5,            # Indie web
    })

CONFIG = SearchConfig()

# Language mappings
LANG_MAP_DDG = {
    "de": "de-de", "en": "en-us", "fr": "fr-fr", "es": "es-es",
    "it": "it-it", "nl": "nl-nl", "pl": "pl-pl", "ru": "ru-ru",
    "pt": "pt-pt", "ja": "ja-jp", "zh": "zh-cn", "ko": "ko-kr",
}

LANG_MAP_SEARXNG = {
    "de": "de", "en": "en", "fr": "fr", "es": "es",
    "it": "it", "nl": "nl", "pl": "pl", "ru": "ru",
}

# ============================================================
# Cache
# ============================================================

_cache: Dict[str, tuple] = {}

def _cache_key(prefix: str, query: str, lang: str) -> str:
    return f"{prefix}:{hashlib.md5(f'{query}:{lang}'.encode()).hexdigest()}"

def _cache_get(key: str) -> Any:
    if key in _cache:
        data, ts = _cache[key]
        if time.time() - ts < CONFIG.cache_ttl:
            return data
        del _cache[key]
    return None

def _cache_set(key: str, data: Any):
    _cache[key] = (data, time.time())
    if len(_cache) > CONFIG.max_cache_size:
        oldest = sorted(_cache.items(), key=lambda x: x[1][1])[:100]
        for k, _ in oldest:
            del _cache[k]

def _url_hash(url: str) -> str:
    """Normalisierte URL-Hash für Deduplication."""
    url = url.lower().rstrip('/').replace('https://', '').replace('http://', '').replace('www.', '')
    return hashlib.md5(url.encode()).hexdigest()[:12]

# ============================================================
# Search Providers
# ============================================================

async def _search_searxng(
    query: str, 
    max_results: int = 50, 
    lang: str = "de",
    categories: str = "general",
    engines: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """SearXNG Meta-Search (247 Engines!)."""
    results = []
    searxng_lang = LANG_MAP_SEARXNG.get(lang, "all")
    
    params = {
        "q": query,
        "format": "json",
        "language": searxng_lang,
        "categories": categories,
        "pageno": 1,
    }
    
    if engines:
        params["engines"] = ",".join(engines)
    
    try:
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=CONFIG.timeout)
        ) as session:
            async with session.get(
                f"{CONFIG.searxng_url}/search",
                params=params
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    for r in data.get("results", [])[:max_results]:
                        results.append({
                            "title": html.unescape(r.get("title", "")),
                            "url": r.get("url", ""),
                            "snippet": html.unescape(r.get("content", r.get("snippet", ""))),
                            "source": f"searxng:{r.get('engine', 'unknown')}",
                            "lang": lang,
                            "score": r.get("score", 0),
                            "engines": r.get("engines", []),
                        })
                    logger.info(f"SearXNG: {len(results)} results for '{query}' ({lang})")
                else:
                    logger.warning(f"SearXNG returned {resp.status}")
    except aiohttp.ClientError as e:
        logger.warning(f"SearXNG connection error: {e}")
    except Exception as e:
        logger.error(f"SearXNG error: {e}")
    
    return results


async def _search_ddg(query: str, max_results: int = 30, lang: str = "de") -> List[Dict[str, Any]]:
    """DuckDuckGo Direct Search via ddgs package."""
    try:
        from ddgs import DDGS
    except ImportError:
        try:
            from duckduckgo_search import DDGS
        except ImportError:
            logger.warning("ddgs/duckduckgo-search not installed")
            return []
    
    results = []
    region = LANG_MAP_DDG.get(lang, "wt-wt")
    
    def _search():
        try:
            # Use ddgs with verify=False for SSL issues
            ddgs = DDGS(verify=False)
            for r in ddgs.text(query, region=region, max_results=max_results):
                results.append({
                    "title": r.get("title", ""),
                    "url": r.get("href", r.get("url", "")),
                    "snippet": r.get("body", r.get("description", "")),
                    "source": "duckduckgo",
                    "lang": lang,
                    "score": 0,
                })
        except Exception as e:
            logger.warning(f"DDG error ({lang}): {e}")
    
    await asyncio.get_running_loop().run_in_executor(None, _search)
    return results


async def _search_wiby(query: str, max_results: int = 15) -> List[Dict[str, Any]]:
    """Wiby.me - Indie/Classic Web Index."""
    results = []
    try:
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=6)
        ) as session:
            async with session.get(f"https://wiby.me/json/?q={query}") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    for r in data[:max_results]:
                        results.append({
                            "title": html.unescape(r.get("Title", "")),
                            "url": r.get("URL", ""),
                            "snippet": html.unescape(r.get("Snippet", r.get("Description", ""))),
                            "source": "wiby",
                            "lang": "en",
                            "score": 0,
                        })
    except Exception as e:
        logger.debug(f"Wiby error: {e}")
    return results


async def _search_wikipedia(query: str, lang: str = "de", max_results: int = 5) -> List[Dict[str, Any]]:
    """Wikipedia Opensearch API."""
    results = []
    wiki_lang = LANG_MAP_SEARXNG.get(lang, "en")
    headers = {"User-Agent": "AILinux-Search/1.0"}
    
    try:
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=5),
            headers=headers
        ) as session:
            url = f"https://{wiki_lang}.wikipedia.org/w/api.php"
            params = {
                "action": "opensearch",
                "search": query,
                "limit": max_results,
                "format": "json"
            }
            async with session.get(url, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if len(data) >= 4:
                        for i in range(min(len(data[1]), max_results)):
                            results.append({
                                "title": f"📚 {data[1][i]}",
                                "url": data[3][i],
                                "snippet": data[2][i] if i < len(data[2]) else "",
                                "source": "wikipedia",
                                "lang": wiki_lang,
                                "score": 0,
                            })
    except Exception as e:
        logger.debug(f"Wikipedia error: {e}")
    return results


# ============================================================
# Result Processing
# ============================================================

def _deduplicate_results(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Entfernt Duplikate basierend auf URL-Hash.
    Bevorzugt Knowledge-Quellen (Wikipedia, Grokipedia) über Suchmaschinen.
    """
    # Priority sources - wenn ein Ergebnis von diesen Quellen kommt, wird es bevorzugt
    KNOWLEDGE_SOURCES = {"wikipedia", "grokipedia"}

    seen_urls: Dict[str, Dict[str, Any]] = {}  # url_hash -> result

    for r in results:
        url = r.get('url', '')
        if not url:
            continue
        url_id = _url_hash(url)
        source = r.get('source', 'unknown').split(':')[0]

        if url_id not in seen_urls:
            seen_urls[url_id] = r
        else:
            # Ersetze nur wenn neue Quelle eine Knowledge-Quelle ist und alte nicht
            existing_source = seen_urls[url_id].get('source', 'unknown').split(':')[0]
            if source in KNOWLEDGE_SOURCES and existing_source not in KNOWLEDGE_SOURCES:
                seen_urls[url_id] = r

    return list(seen_urls.values())


def _score_result(result: Dict[str, Any], query: str) -> float:
    """Berechnet Relevanz-Score für ein Ergebnis."""
    score = 0.0
    query_terms = set(query.lower().split())
    
    # Title match
    title = result.get("title", "").lower()
    title_matches = sum(1 for term in query_terms if term in title)
    score += title_matches * 20
    
    # Snippet match
    snippet = result.get("snippet", "").lower()
    snippet_matches = sum(1 for term in query_terms if term in snippet)
    score += snippet_matches * 10
    
    # Exact phrase bonus
    if query.lower() in title:
        score += 30
    if query.lower() in snippet:
        score += 15
    
    # Source weight
    source = result.get("source", "unknown").split(":")[0]
    source_weight = CONFIG.source_weights.get(source, 0.5)
    score *= source_weight
    
    # SearXNG engine score
    if result.get("score", 0) > 0:
        score += result["score"] * 5
    
    return score


def _rank_results(results: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
    """Sortiert Ergebnisse nach Relevanz."""
    for r in results:
        r["relevance_score"] = _score_result(r, query)
    
    return sorted(results, key=lambda x: x.get("relevance_score", 0), reverse=True)


# ============================================================
# Main Search Functions - ALL 7 PROVIDERS ALWAYS ENABLED
# ============================================================

async def multi_search(
    query: str,
    max_results: int = 50,
    lang: str = "de",
    # Legacy parameters - ignored, all providers always active
    use_searxng: bool = True,
    use_ddg: bool = True,
    use_wiby: bool = True,
    use_wikipedia: bool = True,
    use_grokipedia: bool = True,
    use_ailinux_news: bool = True,
    searxng_categories: str = "general",
    searxng_engines: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Aggregierte Multi-API Suche mit ALLEN 7 Providern.

    Providers (always enabled):
    1. Google (googlesearch-python)
    2. SearXNG (247 Engines)
    3. DuckDuckGo
    4. Wikipedia
    5. Grokipedia
    6. AILinux News
    7. Wiby

    NOTE: All use_* parameters are ignored - all providers always active.
    """
    # Delegate to multi_search_extended which uses all 7 providers
    return await multi_search_extended(
        query=query,
        max_results=max_results,
        lang=lang,
        searxng_categories=searxng_categories,
        searxng_engines=searxng_engines,
    )


async def search_with_mesh_filter(
    query: str,
    max_results: int = 30,
    lang: str = "de",
    mesh_agents: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Multi-Search mit Mesh AI Filtering.
    
    Die Mesh Agents bewerten jeden Treffer auf Relevanz.
    """
    # Erst normale Suche
    search_result = await multi_search(query, max_results * 2, lang)
    
    if not mesh_agents:
        mesh_agents = ["claude-mcp", "gemini-mcp", "codex-mcp"]
    
    # Mesh AI Integration - get relevance scores from agents
    results = search_result.get("results", [])
    
    if results:
        try:
            from .command_queue import enqueue_command, get_command_status
            import asyncio
            
            # Prepare batch for mesh scoring (top 20 results)
            top_results = results[:20]
            result_summaries = []
            for i, r in enumerate(top_results):
                result_summaries.append(f"{i}: {r.get('title', '')[:50]} | {r.get('snippet', '')[:80]}")
            
            scoring_prompt = f"""Rate these search results for query "{query}" (0-10 relevance):
{chr(10).join(result_summaries)}

Respond ONLY with comma-separated scores in order (e.g., 8,6,9,4,7,...)"""
            
            # Collect scores from available mesh agents (parallel)
            agent_scores: Dict[str, List[float]] = {}
            
            async def get_agent_score(agent_id: str) -> Optional[List[float]]:
                try:
                    # Use CLI agents if available
                    from .cli_agents import get_cli_agent_manager
                    manager = get_cli_agent_manager()
                    
                    if agent_id in manager._agents and manager._agents[agent_id].get("status") == "running":
                        # Send scoring request with short timeout
                        response = await asyncio.wait_for(
                            manager.call_agent(agent_id, scoring_prompt),
                            timeout=5.0
                        )
                        # Parse scores from response
                        if response and "output" in response:
                            scores_str = response["output"].strip()
                            # Extract numbers from response
                            import re
                            numbers = re.findall(r'\d+(?:\.\d+)?', scores_str)
                            if numbers:
                                return [min(10.0, float(n)) for n in numbers[:len(top_results)]]
                except Exception as e:
                    logger.debug(f"Mesh scoring from {agent_id} failed: {e}")
                return None
            
            # Try to get scores from agents (with timeout)
            try:
                score_tasks = [get_agent_score(agent) for agent in mesh_agents]
                agent_results = await asyncio.wait_for(
                    asyncio.gather(*score_tasks, return_exceptions=True),
                    timeout=8.0
                )
                
                for agent, scores in zip(mesh_agents, agent_results):
                    if isinstance(scores, list) and scores:
                        agent_scores[agent] = scores
            except asyncio.TimeoutError:
                logger.debug("Mesh scoring timed out, using fallback")
            
            # Calculate consensus scores if we got any agent responses
            if agent_scores:
                for i, r in enumerate(top_results):
                    scores_for_result = []
                    for agent, scores in agent_scores.items():
                        if i < len(scores):
                            scores_for_result.append(scores[i])
                    
                    if scores_for_result:
                        # Average score from responding agents
                        r["mesh_score"] = sum(scores_for_result) / len(scores_for_result)
                        r["mesh_agents_responded"] = len(scores_for_result)
                    else:
                        r["mesh_score"] = r.get("relevance_score", 5.0) / 10.0  # Fallback
                
                # Re-sort by mesh score
                top_results.sort(key=lambda x: x.get("mesh_score", 0), reverse=True)
                
                # Combine re-ranked top with remaining results
                results = top_results + results[20:]
                search_result["mesh_scoring"] = {
                    "agents_queried": mesh_agents,
                    "agents_responded": list(agent_scores.keys()),
                    "results_scored": len(top_results),
                }
            else:
                # Fallback - use existing relevance scores as mesh scores
                for r in results:
                    r["mesh_score"] = r.get("relevance_score", 50.0) / 100.0
                search_result["mesh_scoring"] = {
                    "agents_queried": mesh_agents,
                    "agents_responded": [],
                    "fallback": True,
                }
                
        except ImportError:
            # Fallback if dependencies not available
            for r in results:
                r["mesh_score"] = r.get("relevance_score", 50.0) / 100.0
            search_result["mesh_scoring"] = {"fallback": True, "reason": "dependencies_unavailable"}
        except Exception as e:
            logger.warning(f"Mesh filtering error: {e}")
            for r in results:
                r["mesh_score"] = r.get("relevance_score", 50.0) / 100.0
            search_result["mesh_scoring"] = {"fallback": True, "error": str(e)}
    
    search_result["mesh_filtered"] = True
    search_result["mesh_agents"] = mesh_agents
    search_result["results"] = results[:max_results]
    
    return search_result


# ============================================================
# Convenience Functions (Backwards Compatible)
# ============================================================

async def search_web(
    query: str,
    num_results: int = 50,
    page: int = 1,
    per_page: int = 50,
    lang: str = "de",
    **kwargs
) -> Dict[str, Any]:
    """Hauptfunktion für Websuche (Kompatibilitäts-Wrapper)."""
    if lang == "auto" or not lang:
        lang = "de"
    lang = lang.lower()[:2]
    
    result = await multi_search(query, max(num_results, per_page * page), lang)
    
    # Pagination
    all_results = result["results"]
    total = len(all_results)
    pages = max(1, (total + per_page - 1) // per_page)
    
    start = (page - 1) * per_page
    end = start + per_page
    page_results = all_results[start:end]
    
    return {
        "query": query,
        "lang": lang,
        "results": page_results,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": pages,
        "count": len(page_results),
        "sources": result.get("sources", {}),
        "search_time_ms": result.get("search_time_ms", 0),
    }


async def search_duckduckgo(query: str, num_results: int = 10, lang: str = "de") -> List[Dict[str, Any]]:
    """DuckDuckGo only search."""
    return await _search_ddg(query, num_results, lang)


async def search_searxng(
    query: str, 
    num_results: int = 30, 
    lang: str = "de",
    engines: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """SearXNG only search."""
    return await _search_searxng(query, num_results, lang, engines=engines)


# ============================================================
# Health Check
# ============================================================

async def check_search_health() -> Dict[str, Any]:
    """Prüft alle Such-Provider."""
    health = {
        "searxng": False,
        "duckduckgo": False,
        "wiby": False,
        "wikipedia": False,
    }
    
    # SearXNG
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=3)) as session:
            async with session.get(f"{CONFIG.searxng_url}/healthz") as resp:
                health["searxng"] = resp.status == 200
    except:
        pass
    
    # DDG
    try:
        results = await _search_ddg("test", 1, "en")
        health["duckduckgo"] = len(results) > 0
    except:
        pass
    
    # Wiby
    try:
        results = await _search_wiby("test", 1)
        health["wiby"] = len(results) > 0
    except:
        pass
    
    # Wikipedia
    try:
        results = await _search_wikipedia("test", "en", 1)
        health["wikipedia"] = len(results) > 0
    except:
        pass
    
    health["all_healthy"] = all(health.values())
    return health


# ============================================================
# Additional Search Providers (Grokipedia + AILinux News)
# ============================================================

async def _search_grokipedia(query: str, max_results: int = 10) -> List[Dict[str, Any]]:
    """
    Grokipedia.com - xAI's Wikipedia-inspired knowledge base (885K+ articles).
    Uses direct page search via URL pattern.
    """
    results = []
    
    # Method 1: Try search via page URL pattern
    search_terms = query.replace(" ", "_")
    
    try:
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=8),
            headers={"User-Agent": "AILinux-Search/1.0"}
        ) as session:
            # Try direct page access
            test_url = f"https://grokipedia.com/page/{search_terms}"
            async with session.head(test_url) as resp:
                if resp.status == 200:
                    results.append({
                        "title": f"🤖 {query} (Grokipedia)",
                        "url": test_url,
                        "snippet": f"Grokipedia article about {query}",
                        "source": "grokipedia",
                        "lang": "en",
                        "score": 10,
                    })
            
            # Also try variations
            for variant in [query.title().replace(" ", "_"), query.lower().replace(" ", "_")]:
                if variant != search_terms:
                    variant_url = f"https://grokipedia.com/page/{variant}"
                    async with session.head(variant_url) as resp:
                        if resp.status == 200:
                            results.append({
                                "title": f"🤖 {variant.replace('_', ' ')} (Grokipedia)",
                                "url": variant_url,
                                "snippet": f"Grokipedia article",
                                "source": "grokipedia",
                                "lang": "en",
                                "score": 8,
                            })
                            
    except Exception as e:
        logger.debug(f"Grokipedia error: {e}")
    
    return results[:max_results]


async def _search_ailinux_news(query: str, max_results: int = 15, lang: str = "de") -> List[Dict[str, Any]]:
    """
    AILinux.me News Archive - WordPress REST API Search.
    Searches through the Tech/Media/Games blog.
    """
    results = []
    
    try:
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=10),
            headers={"User-Agent": "AILinux-Search/1.0"}
        ) as session:
            # WordPress REST API
            api_url = "https://ailinux.me/wp-json/wp/v2/posts"
            params = {
                "search": query,
                "per_page": max_results,
                "orderby": "relevance",
                "_fields": "id,title,link,excerpt,date,categories"
            }
            
            async with session.get(api_url, params=params) as resp:
                if resp.status == 200:
                    posts = await resp.json()
                    for post in posts:
                        title = post.get("title", {}).get("rendered", "")
                        excerpt = post.get("excerpt", {}).get("rendered", "")
                        
                        # Clean HTML from excerpt
                        import re
                        excerpt_clean = re.sub(r'<[^>]+>', '', excerpt)[:200]
                        
                        results.append({
                            "title": f"📰 {html.unescape(title)}",
                            "url": post.get("link", ""),
                            "snippet": html.unescape(excerpt_clean),
                            "source": "ailinux_news",
                            "lang": lang,
                            "score": 5,
                            "date": post.get("date", ""),
                        })
                    
                    logger.info(f"AILinux News: {len(results)} results for '{query}'")
                else:
                    logger.warning(f"AILinux News API returned {resp.status}")
                    
    except Exception as e:
        logger.debug(f"AILinux News error: {e}")
    
    return results


# ============================================================
# Extended Multi-Search with ALL providers (always enabled)
# ============================================================

async def multi_search_extended(
    query: str,
    max_results: int = 50,
    lang: str = "de",
    # Legacy parameters - ignored, all providers always active
    use_searxng: bool = True,
    use_ddg: bool = True,
    use_wiby: bool = True,
    use_wikipedia: bool = True,
    use_grokipedia: bool = True,
    use_ailinux_news: bool = True,
    searxng_categories: str = "general",
    searxng_engines: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Extended Multi-API Search with ALL 7 providers (always enabled):
    - Google (googlesearch-python)
    - SearXNG (247 Engines)
    - DuckDuckGo
    - Wiby.me
    - Wikipedia
    - Grokipedia (xAI Knowledge Base)
    - AILinux.me News Archive

    NOTE: All providers are ALWAYS used regardless of parameters.
    The use_* parameters are kept for backwards compatibility but ignored.
    """
    cache_key = _cache_key("multi_ext_all", query, lang)
    cached = _cache_get(cache_key)
    if cached:
        logger.info(f"Cache hit for extended '{query}'")
        return cached

    tasks: List[asyncio.Future] = []
    task_names: List[str] = []

    # ALL 7 providers - always enabled, no conditions
    # 1. Google (primary, high priority)
    tasks.append(google_search_deep(query, 40, lang))
    task_names.append("google")

    # 2. SearXNG (meta-search, 247 engines)
    tasks.append(_search_searxng(query, max_results, lang, searxng_categories, searxng_engines))
    task_names.append("searxng")

    # 3. DuckDuckGo (privacy-focused)
    tasks.append(_search_ddg(query, 30, lang))
    task_names.append("duckduckgo")
    tasks.append(_search_ddg(f"{query} guide tutorial", 15, lang))
    task_names.append("duckduckgo_extra")

    # 4. Wikipedia (knowledge base)
    tasks.append(_search_wikipedia(query, lang, 8))
    task_names.append("wikipedia")

    # 5. Grokipedia (xAI knowledge)
    tasks.append(_search_grokipedia(query, 8))
    task_names.append("grokipedia")

    # 6. AILinux News Archive
    tasks.append(_search_ailinux_news(query, 15, lang))
    task_names.append("ailinux_news")

    # 7. Wiby (indie/classic web)
    tasks.append(_search_wiby(query, 10))
    task_names.append("wiby")

    start_time = time.time()
    all_results = await asyncio.gather(*tasks, return_exceptions=True)
    search_time = time.time() - start_time

    combined: List[Dict[str, Any]] = []
    source_stats: Dict[str, int] = {}
    errors: List[str] = []

    for i, results in enumerate(all_results):
        task_name = task_names[i] if i < len(task_names) else f"task_{i}"

        if isinstance(results, Exception):
            errors.append(f"{task_name}: {str(results)}")
            continue

        for r in results:
            combined.append(r)
            src = r.get("source", "unknown").split(":")[0]
            source_stats[src] = source_stats.get(src, 0) + 1

    unique_results = _deduplicate_results(combined)
    ranked_results = _rank_results(unique_results, query)[:max_results]

    result: Dict[str, Any] = {
        "query": query,
        "lang": lang,
        "results": ranked_results,
        "total": len(ranked_results),
        "total_raw": len(combined),
        "sources": source_stats,
        "search_time_ms": round(search_time * 1000, 2),
        "errors": errors if errors else None,
        "providers": {
            "google": True,
            "searxng": True,
            "duckduckgo": True,
            "wikipedia": True,
            "grokipedia": True,
            "ailinux_news": True,
            "wiby": True,
        },
        "provider_meta": [
            {"id": "google", "label": "Google", "status": "active", "type": "search", "count": source_stats.get("google", 0)},
            {"id": "searxng", "label": "SearXNG", "status": "active", "type": "meta-search", "count": source_stats.get("searxng", 0)},
            {"id": "duckduckgo", "label": "DuckDuckGo", "status": "active", "type": "search", "count": source_stats.get("duckduckgo", 0)},
            {"id": "wikipedia", "label": "Wikipedia", "status": "active", "type": "knowledge", "count": source_stats.get("wikipedia", 0)},
            {"id": "grokipedia", "label": "Grokipedia", "status": "active", "type": "knowledge", "count": source_stats.get("grokipedia", 0)},
            {"id": "ailinux_news", "label": "AILinux News", "status": "active", "type": "news", "count": source_stats.get("ailinux_news", 0)},
            {"id": "wiby", "label": "Wiby", "status": "active", "type": "nostalgic", "count": source_stats.get("wiby", 0)},
        ],
    }

    _cache_set(cache_key, result)
    logger.info(
        f"Extended search '{query}' ({lang}): {len(ranked_results)} results in {search_time:.2f}s from {source_stats}"
    )

    return result


async def search_ailinux(query: str, num_results: int = 20) -> List[Dict[str, Any]]:
    """Convenience: Search AILinux News only."""
    return await _search_ailinux_news(query, num_results)


async def search_grokipedia(query: str, num_results: int = 5) -> List[Dict[str, Any]]:
    """Convenience: Search Grokipedia only."""
    return await _search_grokipedia(query, num_results)


# ============================================================
# Weather API (Open-Meteo - FREE, no key required)
# ============================================================

async def get_weather(lat: float = 52.52, lon: float = 13.41, location: str = "Berlin") -> Dict[str, Any]:
    """Get current weather from Open-Meteo API (free, no API key)."""
    try:
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=5)
        ) as session:
            url = "https://api.open-meteo.com/v1/forecast"
            params = {
                "latitude": lat,
                "longitude": lon,
                "current": "temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m",
                "timezone": "Europe/Berlin"
            }
            async with session.get(url, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    current = data.get("current", {})
                    
                    # Weather code to icon/description
                    weather_codes = {
                        0: ("☀️", "Klar"), 1: ("🌤️", "Überwiegend klar"),
                        2: ("⛅", "Teilweise bewölkt"), 3: ("☁️", "Bewölkt"),
                        45: ("🌫️", "Nebel"), 48: ("🌫️", "Reifnebel"),
                        51: ("🌧️", "Leichter Niesel"), 53: ("🌧️", "Niesel"),
                        55: ("🌧️", "Starker Niesel"), 61: ("🌧️", "Leichter Regen"),
                        63: ("🌧️", "Regen"), 65: ("🌧️", "Starker Regen"),
                        71: ("🌨️", "Leichter Schnee"), 73: ("🌨️", "Schnee"),
                        75: ("🌨️", "Starker Schnee"), 80: ("🌦️", "Regenschauer"),
                        95: ("⛈️", "Gewitter"), 99: ("⛈️", "Gewitter mit Hagel"),
                    }
                    code = current.get("weather_code", 0)
                    icon, desc = weather_codes.get(code, ("❓", "Unbekannt"))
                    
                    return {
                        "location": location,
                        "temperature": current.get("temperature_2m"),
                        "humidity": current.get("relative_humidity_2m"),
                        "wind_speed": current.get("wind_speed_10m"),
                        "weather_code": code,
                        "icon": icon,
                        "description": desc,
                        "unit": "°C"
                    }
    except Exception as e:
        logger.warning(f"Weather API error: {e}")
    return {"error": "Weather unavailable"}


# ============================================================
# Crypto & Stock API (CoinGecko FREE + Yahoo Finance)
# ============================================================

async def get_crypto_prices(coins: List[str] = ["bitcoin", "ethereum"]) -> Dict[str, Any]:
    """Get crypto prices from CoinGecko (free, no API key)."""
    try:
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=8)
        ) as session:
            url = "https://api.coingecko.com/api/v3/simple/price"
            params = {
                "ids": ",".join(coins),
                "vs_currencies": "usd,eur",
                "include_24hr_change": "true"
            }
            async with session.get(url, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    result = {}
                    for coin in coins:
                        if coin in data:
                            d = data[coin]
                            result[coin] = {
                                "usd": d.get("usd"),
                                "eur": d.get("eur"),
                                "change_24h": round(d.get("usd_24h_change", 0), 2)
                            }
                    return {"prices": result, "source": "coingecko"}
    except Exception as e:
        logger.warning(f"Crypto API error: {e}")
    return {"error": "Crypto data unavailable"}


async def get_stock_indices() -> Dict[str, Any]:
    """Get major stock indices (Yahoo Finance scrape fallback)."""
    indices = {
        "DAX": {"symbol": "^GDAXI", "value": None, "change": None},
        "S&P500": {"symbol": "^GSPC", "value": None, "change": None},
        "NASDAQ": {"symbol": "^IXIC", "value": None, "change": None},
    }
    
    try:
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=10),
            headers={"User-Agent": "AILinux-Search/1.0"}
        ) as session:
            for name, data in indices.items():
                try:
                    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{data['symbol']}?interval=1d&range=1d"
                    async with session.get(url) as resp:
                        if resp.status == 200:
                            j = await resp.json()
                            meta = j.get("chart", {}).get("result", [{}])[0].get("meta", {})
                            price = meta.get("regularMarketPrice", 0)
                            prev = meta.get("previousClose", price)
                            change = round(((price - prev) / prev) * 100, 2) if prev else 0
                            indices[name]["value"] = round(price, 2)
                            indices[name]["change"] = change
                except Exception as e:
                    logger.debug(f"Index {name} error: {e}")
    except Exception as e:
        logger.warning(f"Stock indices error: {e}")
    
    return {"indices": indices, "source": "yahoo"}


# ============================================================
# Google Search via HTML scraping with robust anti-bot measures
# ============================================================

async def google_search_deep(query: str, num_results: int = 50, lang: str = "de") -> List[Dict[str, Any]]:
    """
    Google search with multiple fallback methods:
    1. DuckDuckGo HTML with Google-style parsing (most reliable)
    2. SearXNG Google engine (if available)
    3. Direct scraping as last resort

    Returns results with source='google' for consistency.
    """
    results: List[Dict[str, Any]] = []
    max_results = max(1, min(num_results, 100))

    # Method 1: Use DuckDuckGo as Google proxy (most reliable)
    try:
        from ddgs import DDGS
        ddgs = DDGS(verify=False)

        def _search_ddg():
            found = []
            try:
                region = LANG_MAP_DDG.get(lang, "wt-wt")
                for r in ddgs.text(query, region=region, max_results=max_results):
                    found.append({
                        "url": r.get("href", r.get("url", "")),
                        "title": r.get("title", ""),
                        "snippet": r.get("body", r.get("description", "")),
                        "source": "google",  # Mark as google for unified stats
                        "lang": lang,
                    })
            except Exception as e:
                logger.debug(f"DDG-as-Google error: {e}")
            return found

        loop = asyncio.get_running_loop()
        results = await asyncio.wait_for(
            loop.run_in_executor(None, _search_ddg),
            timeout=15.0
        )

        if results:
            logger.info(f"Google (via DDG) '{query}': {len(results)} results")
            return results

    except ImportError:
        logger.debug("ddgs not available for Google fallback")
    except asyncio.TimeoutError:
        logger.debug("DDG-as-Google timed out")
    except Exception as e:
        logger.debug(f"DDG-as-Google failed: {e}")

    # Method 2: Direct Google scraping with rotating headers
    try:
        from bs4 import BeautifulSoup
        import random

        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        ]

        headers = {
            "User-Agent": random.choice(user_agents),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": f"{lang},{lang}-DE;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }

        timeout = aiohttp.ClientTimeout(total=12)
        connector = aiohttp.TCPConnector(ssl=False)

        async with aiohttp.ClientSession(timeout=timeout, connector=connector, headers=headers) as session:
            params = {"q": query, "hl": lang, "num": min(max_results, 50)}

            async with session.get("https://www.google.com/search", params=params) as resp:
                if resp.status == 200:
                    text = await resp.text()
                    soup = BeautifulSoup(text, "html.parser")

                    # Try multiple selector patterns
                    for block in soup.select("div.g, div.rc, div[data-hveid]"):
                        link = block.select_one("a[href^='http']")
                        title_el = block.select_one("h3")

                        if not link or not title_el:
                            continue

                        url = link.get("href", "")
                        if not url.startswith("http") or "google.com" in url:
                            continue

                        snippet_el = block.select_one("div.VwiC3b, span.st, div[data-sncf]")
                        snippet = snippet_el.get_text() if snippet_el else ""

                        results.append({
                            "url": url,
                            "title": title_el.get_text(),
                            "snippet": snippet,
                            "source": "google",
                            "lang": lang,
                        })

                        if len(results) >= max_results:
                            break

    except Exception as e:
        logger.debug(f"Direct Google scraping failed: {e}")

    # Method 3: Try googlesearch-python as final fallback
    if not results:
        try:
            from googlesearch import search as google_search

            def _search_lib():
                found = []
                try:
                    for url in google_search(query, num_results=max_results, lang=lang):
                        if isinstance(url, str):
                            found.append({
                                "url": url,
                                "title": url.split("/")[-1] or url,
                                "snippet": "",
                                "source": "google",
                                "lang": lang,
                            })
                except Exception:
                    pass
                return found

            loop = asyncio.get_running_loop()
            results = await asyncio.wait_for(
                loop.run_in_executor(None, _search_lib),
                timeout=20.0
            )
        except Exception as e:
            logger.debug(f"googlesearch-python fallback failed: {e}")

    logger.info(f"Google deep search '{query}': {len(results)} results")
    return results


# ============================================================
# Market Overview (Combined)
# ============================================================

async def get_market_overview() -> Dict[str, Any]:
    """Get combined market data: crypto + stocks."""
    crypto_task = get_crypto_prices(["bitcoin", "ethereum", "solana"])
    stocks_task = get_stock_indices()
    
    crypto, stocks = await asyncio.gather(crypto_task, stocks_task, return_exceptions=True)
    
    return {
        "crypto": crypto if not isinstance(crypto, Exception) else {"error": str(crypto)},
        "stocks": stocks if not isinstance(stocks, Exception) else {"error": str(stocks)},
        "timestamp": time.time()
    }


# ============================================================
# Time API (WorldTimeAPI - FREE, location-based timezone)
# ============================================================

async def get_current_time(timezone: str = "Europe/Berlin", location: str = None) -> Dict[str, Any]:
    """Get current time with timezone support."""
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
            url = f"http://worldtimeapi.org/api/timezone/{timezone}"
            async with session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    dt_str = data.get("datetime", "")
                    utc_offset = data.get("utc_offset", "+00:00")
                    if dt_str:
                        from datetime import datetime
                        dt_part = dt_str.split(".")[0]
                        dt = datetime.fromisoformat(dt_part)
                        weekdays_de = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]
                        return {
                            "timezone": timezone,
                            "location": location or timezone.split("/")[-1].replace("_", " "),
                            "datetime": dt_str, "date": dt.strftime("%Y-%m-%d"),
                            "time": dt.strftime("%H:%M:%S"), "time_12h": dt.strftime("%I:%M %p"),
                            "weekday": dt.strftime("%A"), "weekday_de": weekdays_de[dt.weekday()],
                            "utc_offset": utc_offset, "unix_timestamp": data.get("unixtime"),
                        }
    except Exception as e:
        logger.warning(f"Time API error: {e}")
    from datetime import datetime
    now = datetime.now()
    weekdays_de = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]
    return {
        "timezone": timezone, "location": location or "Local",
        "datetime": now.isoformat(), "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M:%S"), "time_12h": now.strftime("%I:%M %p"),
        "weekday": now.strftime("%A"), "weekday_de": weekdays_de[now.weekday()],
        "source": "local_fallback"
    }


async def list_timezones(region: str = None) -> Dict[str, Any]:
    """List available timezones."""
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
            url = f"http://worldtimeapi.org/api/timezone/{region}" if region else "http://worldtimeapi.org/api/timezone"
            async with session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return {"timezones": data if isinstance(data, list) else [data], "count": len(data) if isinstance(data, list) else 1}
    except Exception as e:
        logger.warning(f"Timezone list error: {e}")
    return {"timezones": ["Europe/Berlin", "Europe/London", "America/New_York", "Asia/Tokyo"], "count": 4, "source": "fallback"}


# ============================================================
# LLM-POWERED SMART SEARCH (Cerebras/Groq for Speed)
# ============================================================

from dataclasses import dataclass
from enum import Enum
from typing import Callable, Awaitable

class SearchLLMProvider(Enum):
    """Verfügbare LLM Provider für Search Enhancement."""
    CEREBRAS = "cerebras"      # 20x faster than GPU
    GROQ = "groq"              # Ultra-fast inference
    GEMINI_FLASH = "gemini"    # Good balance
    MISTRAL = "mistral"        # European, fast


@dataclass
class SearchLLMConfig:
    """Konfiguration für LLM-gestützte Suche."""
    # Primary model for speed-critical tasks (query expansion, intent)
    fast_model: str = "cerebras/llama-3.3-70b"
    fast_provider: str = "cerebras"
    
    # Secondary model for quality tasks (summarization)
    quality_model: str = "groq/llama-3.3-70b-versatile"
    quality_provider: str = "groq"
    
    # Fallback model
    fallback_model: str = "gemini/gemini-2.5-flash"
    fallback_provider: str = "gemini"
    
    # Context windows (tokens)
    context_windows: dict = None
    
    # Timeouts (ms)
    fast_timeout_ms: int = 5000      # 5s for fast tasks
    quality_timeout_ms: int = 15000  # 15s for summaries
    
    # Feature toggles
    enable_query_expansion: bool = True
    enable_intent_detection: bool = True
    enable_result_summary: bool = True
    enable_smart_ranking: bool = True
    
    def __post_init__(self):
        if self.context_windows is None:
            self.context_windows = {
                "cerebras/llama-3.3-70b": 8192,
                "cerebras/llama3.1-70b": 8192,
                "cerebras/llama3.1-8b": 8192,
                "groq/llama-3.3-70b-versatile": 32768,
                "groq/llama-3.3-70b-specdec": 8192,
                "groq/llama-3.1-8b-instant": 131072,
                "groq/mixtral-8x7b-32768": 32768,
                "gemini/gemini-2.5-flash": 1048576,
                "gemini/gemini-2.5-pro": 2097152,
                "mistral/mistral-small-latest": 32768,
                "mistral/mistral-large-latest": 128000,
            }


# Global config - can be modified at runtime
SEARCH_LLM_CONFIG = SearchLLMConfig()


async def _call_fast_llm(
    prompt: str,
    max_tokens: int = 200,
    temperature: float = 0.3,
) -> str:
    """Call the fast LLM (Cerebras) for speed-critical tasks."""
    from ..config import get_settings
    settings = get_settings()
    
    config = SEARCH_LLM_CONFIG
    model = config.fast_model
    timeout = config.fast_timeout_ms / 1000
    
    # Try Cerebras first
    if settings.cerebras_api_key:
        try:
            import httpx
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    f"{settings.cerebras_base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {settings.cerebras_api_key}"},
                    json={
                        "model": model.replace("cerebras/", ""),
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": max_tokens,
                        "temperature": temperature,
                    }
                )
                if response.status_code == 200:
                    data = response.json()
                    return data["choices"][0]["message"]["content"]
        except Exception as e:
            logger.warning(f"Cerebras fast LLM failed: {e}")
    
    # Fallback to Groq
    if settings.groq_api_key:
        try:
            import httpx
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    f"{settings.groq_base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {settings.groq_api_key}"},
                    json={
                        "model": "llama-3.3-70b-versatile",
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": max_tokens,
                        "temperature": temperature,
                    }
                )
                if response.status_code == 200:
                    data = response.json()
                    return data["choices"][0]["message"]["content"]
        except Exception as e:
            logger.warning(f"Groq fast LLM failed: {e}")
    
    return ""


async def _call_quality_llm(
    prompt: str,
    max_tokens: int = 500,
    temperature: float = 0.5,
) -> str:
    """Call quality LLM (Groq/Gemini) for summarization tasks."""
    from ..config import get_settings
    settings = get_settings()
    
    config = SEARCH_LLM_CONFIG
    timeout = config.quality_timeout_ms / 1000
    
    # Try Groq first (good balance of speed & quality)
    if settings.groq_api_key:
        try:
            import httpx
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    f"{settings.groq_base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {settings.groq_api_key}"},
                    json={
                        "model": "llama-3.3-70b-versatile",
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": max_tokens,
                        "temperature": temperature,
                    }
                )
                if response.status_code == 200:
                    data = response.json()
                    return data["choices"][0]["message"]["content"]
        except Exception as e:
            logger.warning(f"Groq quality LLM failed: {e}")
    
    # Fallback to Gemini
    if settings.gemini_api_key:
        try:
            import google.generativeai as genai
            genai.configure(api_key=settings.gemini_api_key)
            model = genai.GenerativeModel("gemini-2.5-flash")
            response = await model.generate_content_async(prompt)
            return response.text
        except Exception as e:
            logger.warning(f"Gemini quality LLM failed: {e}")
    
    return ""


# ============================================================
# SMART SEARCH FUNCTIONS
# ============================================================

async def expand_query(query: str, lang: str = "de") -> dict:
    """
    Expand search query using fast LLM.
    Returns original + expanded terms + detected intent.
    
    Latency target: <100ms with Cerebras
    """
    if not SEARCH_LLM_CONFIG.enable_query_expansion:
        return {"original": query, "expanded": query, "terms": [], "intent": "general"}
    
    prompt = f"""Analyze this search query and expand it with related terms.
Query: "{query}"
Language: {lang}

Respond in JSON format ONLY:
{{"expanded": "expanded query with synonyms", "terms": ["term1", "term2", "term3"], "intent": "informational|navigational|transactional|technical"}}"""

    start = time.time()
    result = await _call_fast_llm(prompt, max_tokens=150, temperature=0.3)
    latency = (time.time() - start) * 1000
    
    logger.info(f"Query expansion took {latency:.0f}ms")
    
    try:
        import json
        # Clean potential markdown
        result = result.strip()
        if result.startswith("```"):
            result = result.split("```")[1]
            if result.startswith("json"):
                result = result[4:]
        
        data = json.loads(result)
        return {
            "original": query,
            "expanded": data.get("expanded", query),
            "terms": data.get("terms", []),
            "intent": data.get("intent", "general"),
            "latency_ms": round(latency, 1)
        }
    except:
        return {
            "original": query,
            "expanded": query,
            "terms": [],
            "intent": "general",
            "latency_ms": round(latency, 1)
        }


async def detect_search_intent(query: str) -> dict:
    """
    Detect search intent for better result filtering.
    
    Intents:
    - informational: User wants to learn something
    - navigational: User wants a specific website
    - transactional: User wants to buy/download
    - technical: User wants code/documentation
    - local: User wants nearby services
    - news: User wants recent events
    """
    if not SEARCH_LLM_CONFIG.enable_intent_detection:
        return {"intent": "informational", "confidence": 0.5}
    
    prompt = f"""Classify this search query intent.
Query: "{query}"

Categories: informational, navigational, transactional, technical, local, news

Respond with ONLY: category|confidence (0.0-1.0)
Example: technical|0.9"""

    start = time.time()
    result = await _call_fast_llm(prompt, max_tokens=20, temperature=0.1)
    latency = (time.time() - start) * 1000
    
    try:
        parts = result.strip().split("|")
        intent = parts[0].strip().lower()
        confidence = float(parts[1]) if len(parts) > 1 else 0.7
        
        valid_intents = ["informational", "navigational", "transactional", "technical", "local", "news"]
        if intent not in valid_intents:
            intent = "informational"
        
        return {
            "intent": intent,
            "confidence": confidence,
            "latency_ms": round(latency, 1)
        }
    except:
        return {
            "intent": "informational",
            "confidence": 0.5,
            "latency_ms": round(latency, 1)
        }


async def summarize_results(
    query: str,
    results: List[Dict[str, Any]],
    max_results: int = 5,
    lang: str = "de"
) -> dict:
    """
    Generate AI summary of search results.
    
    Latency target: <500ms with Groq
    """
    if not SEARCH_LLM_CONFIG.enable_result_summary or not results:
        return {"summary": "", "key_points": []}
    
    # Prepare context from top results
    context_parts = []
    for i, r in enumerate(results[:max_results], 1):
        title = r.get("title", "")[:100]
        snippet = r.get("snippet", "")[:200]
        source = r.get("source", "unknown")
        context_parts.append(f"{i}. [{source}] {title}\n   {snippet}")
    
    context = "\n".join(context_parts)
    
    prompt = f"""Based on these search results for "{query}", provide a brief summary.

Results:
{context}

Language: {lang}

Respond in JSON:
{{"summary": "2-3 sentence summary", "key_points": ["point1", "point2", "point3"], "best_source": "most relevant source name"}}"""

    start = time.time()
    result = await _call_quality_llm(prompt, max_tokens=300, temperature=0.5)
    latency = (time.time() - start) * 1000
    
    logger.info(f"Result summarization took {latency:.0f}ms")
    
    try:
        import json
        result = result.strip()
        if result.startswith("```"):
            result = result.split("```")[1]
            if result.startswith("json"):
                result = result[4:]
        
        data = json.loads(result)
        return {
            "summary": data.get("summary", ""),
            "key_points": data.get("key_points", []),
            "best_source": data.get("best_source", ""),
            "latency_ms": round(latency, 1)
        }
    except:
        return {
            "summary": "",
            "key_points": [],
            "latency_ms": round(latency, 1)
        }


async def smart_rank_results(
    query: str,
    results: List[Dict[str, Any]],
    intent: str = "informational",
) -> List[Dict[str, Any]]:
    """
    Re-rank results using LLM for relevance scoring.
    Only processes top N results for speed.
    """
    if not SEARCH_LLM_CONFIG.enable_smart_ranking or len(results) < 3:
        return results
    
    # Only re-rank top 10 for speed
    to_rank = results[:10]
    rest = results[10:]
    
    # Build ranking prompt
    items = []
    for i, r in enumerate(to_rank):
        items.append(f"{i}: {r.get('title', '')[:60]} | {r.get('snippet', '')[:100]}")
    
    prompt = f"""Rank these search results by relevance to: "{query}"
Intent: {intent}

Results:
{chr(10).join(items)}

Return ONLY the indices in order of relevance, comma-separated.
Example: 2,0,5,1,3,4,6,7,8,9"""

    start = time.time()
    result = await _call_fast_llm(prompt, max_tokens=50, temperature=0.1)
    latency = (time.time() - start) * 1000
    
    try:
        # Parse ranking
        indices = [int(x.strip()) for x in result.strip().split(",") if x.strip().isdigit()]
        
        # Reorder
        ranked = []
        seen = set()
        for idx in indices:
            if 0 <= idx < len(to_rank) and idx not in seen:
                to_rank[idx]["llm_rank"] = len(ranked) + 1
                ranked.append(to_rank[idx])
                seen.add(idx)
        
        # Add any missed items
        for i, r in enumerate(to_rank):
            if i not in seen:
                r["llm_rank"] = len(ranked) + 1
                ranked.append(r)
        
        logger.info(f"Smart ranking took {latency:.0f}ms")
        return ranked + rest
        
    except Exception as e:
        logger.warning(f"Smart ranking failed: {e}")
        return results


# ============================================================
# MAIN SMART SEARCH FUNCTION
# ============================================================

async def smart_search(
    query: str,
    max_results: int = 30,
    lang: str = "de",
    # Provider toggles
    use_searxng: bool = True,
    use_ddg: bool = True,
    use_wikipedia: bool = True,
    use_grokipedia: bool = True,
    use_ailinux_news: bool = True,
    # LLM feature toggles
    expand_query_enabled: bool = True,
    detect_intent_enabled: bool = True,
    summarize_enabled: bool = True,
    smart_rank_enabled: bool = True,
) -> Dict[str, Any]:
    """
    🚀 AI-Powered Smart Search
    
    Flow:
    1. Query Expansion (Cerebras, ~50ms)
    2. Intent Detection (Cerebras, ~30ms)
    3. Multi-Source Search (parallel)
    4. Smart Ranking (Cerebras, ~80ms)
    5. Result Summarization (Groq, ~300ms)
    
    Total target latency: <1000ms
    """
    start_time = time.time()
    timings = {}
    
    # Step 1 & 2: Query Analysis (parallel)
    t0 = time.time()
    expansion_task = expand_query(query, lang) if expand_query_enabled else None
    intent_task = detect_search_intent(query) if detect_intent_enabled else None
    
    if expansion_task and intent_task:
        expansion, intent = await asyncio.gather(expansion_task, intent_task)
    elif expansion_task:
        expansion = await expansion_task
        intent = {"intent": "informational", "confidence": 0.5}
    elif intent_task:
        expansion = {"original": query, "expanded": query, "terms": []}
        intent = await intent_task
    else:
        expansion = {"original": query, "expanded": query, "terms": []}
        intent = {"intent": "informational", "confidence": 0.5}
    
    timings["query_analysis_ms"] = round((time.time() - t0) * 1000, 1)
    
    # Use expanded query for search
    search_query = expansion.get("expanded", query)
    
    # Step 3: Multi-Source Search
    t0 = time.time()
    search_result = await multi_search_extended(
        search_query,
        max_results=max_results * 2,  # Get more for ranking
        lang=lang,
        use_searxng=use_searxng,
        use_ddg=use_ddg,
        use_wiby=False,  # Skip wiby for speed
        use_wikipedia=use_wikipedia,
        use_grokipedia=use_grokipedia,
        use_ailinux_news=use_ailinux_news,
    )
    timings["search_ms"] = round((time.time() - t0) * 1000, 1)
    
    results = search_result.get("results", [])
    
    # Step 4: Smart Ranking
    if smart_rank_enabled and results:
        t0 = time.time()
        results = await smart_rank_results(
            query,
            results,
            intent=intent.get("intent", "informational")
        )
        timings["ranking_ms"] = round((time.time() - t0) * 1000, 1)
    
    # Limit results
    results = results[:max_results]
    
    # Step 5: Summarization (async, don't block)
    summary = {}
    if summarize_enabled and results:
        t0 = time.time()
        summary = await summarize_results(query, results, max_results=5, lang=lang)
        timings["summary_ms"] = round((time.time() - t0) * 1000, 1)
    
    total_time = time.time() - start_time
    timings["total_ms"] = round(total_time * 1000, 1)
    
    logger.info(f"Smart search '{query}': {len(results)} results in {total_time:.2f}s")
    
    return {
        "query": {
            "original": query,
            "expanded": expansion.get("expanded", query),
            "terms": expansion.get("terms", []),
            "intent": intent.get("intent", "informational"),
            "intent_confidence": intent.get("confidence", 0.5),
        },
        "results": results,
        "total": len(results),
        "summary": summary.get("summary", ""),
        "key_points": summary.get("key_points", []),
        "best_source": summary.get("best_source", ""),
        "sources": search_result.get("sources", {}),
        "timings": timings,
        "llm_config": {
            "fast_model": SEARCH_LLM_CONFIG.fast_model,
            "quality_model": SEARCH_LLM_CONFIG.quality_model,
        }
    }


# ============================================================
# QUICK SMART SEARCH (Speed-optimized)
# ============================================================

async def quick_smart_search(
    query: str,
    max_results: int = 15,
    lang: str = "de",
) -> Dict[str, Any]:
    """
    ⚡ Quick Smart Search - Optimized for <500ms

    - Uses SearXNG + AILinux News + Google (via multi_search_extended)
    - Nur leichte Query-Expansion, kein schweres Summarizing
    - Mesh-Ranking-Interface vorbereitet (mesh_rank_results), aktuell Platzhalter
    """
    cache_key = _cache_key("quick_smart", query, lang)
    cached = _cache_get(cache_key)
    if cached:
        logger.info(f"Cache hit for quick smart '{query}'")
        return cached

    start_time = time.time()

    # Quick expansion (leicht, ohne Aggro)
    expansion = await expand_query(query, lang)
    search_query = expansion.get("expanded", query)

    # Fast extended search: SearXNG + AILinux + Google (mandatory in multi_search_extended)
    multi = await multi_search_extended(
        search_query,
        max_results=max_results,
        lang=lang,
        use_searxng=True,
        use_ddg=False,
        use_wiby=False,
        use_wikipedia=False,
        use_grokipedia=False,
        use_ailinux_news=True,
    )

    base_results = multi.get("results", [])
    ranked_results = await mesh_rank_results(search_query, base_results, max_results=max_results)

    total_time = time.time() - start_time

    result: Dict[str, Any] = {
        "query": {
            "original": query,
            "expanded": expansion.get("expanded", query),
        },
        "results": ranked_results,
        "total": len(ranked_results),
        "sources": multi.get("sources", {}),
        "total_ms": round(total_time * 1000, 1),
    }

    _cache_set(cache_key, result)
    logger.info(f"Quick smart search '{query}' -> {result['total']} results (with Google + mesh placeholder)")
    return result


# ============================================================
# CONFIG HELPERS
# ============================================================

def configure_search_llm(
    fast_model: str = None,
    quality_model: str = None,
    enable_expansion: bool = None,
    enable_summary: bool = None,
    enable_ranking: bool = None,
) -> dict:
    """
    Configure LLM settings for search at runtime.
    
    Returns current config.
    """
    global SEARCH_LLM_CONFIG
    
    if fast_model:
        SEARCH_LLM_CONFIG.fast_model = fast_model
        SEARCH_LLM_CONFIG.fast_provider = fast_model.split("/")[0]
    
    if quality_model:
        SEARCH_LLM_CONFIG.quality_model = quality_model
        SEARCH_LLM_CONFIG.quality_provider = quality_model.split("/")[0]
    
    if enable_expansion is not None:
        SEARCH_LLM_CONFIG.enable_query_expansion = enable_expansion
    
    if enable_summary is not None:
        SEARCH_LLM_CONFIG.enable_result_summary = enable_summary
    
    if enable_ranking is not None:
        SEARCH_LLM_CONFIG.enable_smart_ranking = enable_ranking
    
    return {
        "fast_model": SEARCH_LLM_CONFIG.fast_model,
        "quality_model": SEARCH_LLM_CONFIG.quality_model,
        "enable_query_expansion": SEARCH_LLM_CONFIG.enable_query_expansion,
        "enable_intent_detection": SEARCH_LLM_CONFIG.enable_intent_detection,
        "enable_result_summary": SEARCH_LLM_CONFIG.enable_result_summary,
        "enable_smart_ranking": SEARCH_LLM_CONFIG.enable_smart_ranking,
        "context_windows": SEARCH_LLM_CONFIG.context_windows,
    }


def get_available_search_models() -> dict:
    """List all models available for search with their context windows."""
    return {
        "fast_models": {
            "cerebras/llama-3.3-70b": {"context": 8192, "speed": "20x GPU"},
            "cerebras/llama3.1-8b": {"context": 8192, "speed": "20x GPU"},
            "groq/llama-3.3-70b-versatile": {"context": 32768, "speed": "~100ms"},
            "groq/llama-3.1-8b-instant": {"context": 131072, "speed": "~50ms"},
        },
        "quality_models": {
            "groq/llama-3.3-70b-versatile": {"context": 32768, "quality": "high"},
            "groq/mixtral-8x7b-32768": {"context": 32768, "quality": "medium"},
            "gemini/gemini-2.5-flash": {"context": 1048576, "quality": "high"},
            "gemini/gemini-2.5-pro": {"context": 2097152, "quality": "highest"},
        },
        "current_config": {
            "fast": SEARCH_LLM_CONFIG.fast_model,
            "quality": SEARCH_LLM_CONFIG.quality_model,
        }
    }


async def mesh_rank_results(query: str, results: List[Dict[str, Any]], max_results: int = 30) -> List[Dict[str, Any]]:
    """
    Mesh-AI based ranking interface.

    Contract:
    - Input: raw search results (including Google)
    - Output: same list, but with 'mesh_score' and re-ordered by consensus

    Uses lightweight scoring for speed while supporting full mesh consensus
    when agents are available.
    """
    if not results:
        return []
    
    try:
        # Try to use Mesh system for ranking
        from ..routes.mesh import get_mesh_coordinator
        
        coordinator = get_mesh_coordinator()
        
        # Check if we have active mesh agents
        if coordinator and coordinator._agents:
            # Prepare ranking task for mesh
            top_results = results[:min(15, len(results))]  # Limit for speed
            
            # Build compact representation for scoring
            items_for_scoring = []
            for i, r in enumerate(top_results):
                items_for_scoring.append({
                    "idx": i,
                    "title": r.get("title", "")[:60],
                    "snippet": r.get("snippet", "")[:100],
                    "source": r.get("source", "unknown"),
                })
            
            # Submit quick ranking task
            try:
                import asyncio
                
                # Use fast consensus (2 agents, short timeout)
                ranking_task = {
                    "type": "rank",
                    "query": query,
                    "items": items_for_scoring,
                }
                
                # Try to get quick ranking from lead agent
                lead_agents = [a for a, info in coordinator._agents.items() 
                              if info.get("role") == "lead"]
                
                if lead_agents:
                    lead = lead_agents[0]
                    # Request ranking via mesh queue
                    from .command_queue import enqueue_command
                    
                    ranking_prompt = f"Rank by relevance to '{query}': " + \
                                    ", ".join([f"{i['idx']}:{i['title'][:30]}" for i in items_for_scoring])
                    
                    command_id = await enqueue_command(
                        command=ranking_prompt,
                        command_type="research",
                        target_agent=lead,
                        priority="high",
                    )
                    
                    # Don't wait for result - apply heuristic scoring for now
                    # The mesh result can update async
                    
            except Exception as e:
                logger.debug(f"Mesh ranking task failed: {e}")
        
        # Apply heuristic mesh scoring (fast fallback)
        query_terms = set(query.lower().split())
        
        for r in results:
            if "mesh_score" in r:
                continue
                
            score = 0.0
            title = r.get("title", "").lower()
            snippet = r.get("snippet", "").lower()
            source = r.get("source", "unknown").split(":")[0]
            
            # Title relevance (highest weight)
            title_matches = sum(1 for term in query_terms if term in title)
            score += title_matches * 3.0
            
            # Exact phrase bonus
            if query.lower() in title:
                score += 5.0
            
            # Snippet relevance
            snippet_matches = sum(1 for term in query_terms if term in snippet)
            score += snippet_matches * 1.5
            
            # Source trust scoring
            source_trust = {
                "google": 1.2,
                "wikipedia": 1.3,
                "grokipedia": 1.1,
                "searxng": 1.0,
                "duckduckgo": 0.95,
                "ailinux_news": 0.9,
                "wiby": 0.6,
            }
            score *= source_trust.get(source, 0.8)
            
            # Existing relevance score contribution
            if r.get("relevance_score"):
                score += r["relevance_score"] * 0.1
            
            r["mesh_score"] = round(score, 2)
        
        # Sort by mesh_score
        results.sort(key=lambda x: x.get("mesh_score", 0), reverse=True)
        
    except ImportError:
        # Fallback if mesh not available
        for r in results:
            if "mesh_score" not in r:
                r["mesh_score"] = r.get("relevance_score", r.get("score", 0.0))
    except Exception as e:
        logger.warning(f"mesh_rank_results error: {e}")
        for r in results:
            if "mesh_score" not in r:
                r["mesh_score"] = r.get("relevance_score", r.get("score", 0.0))
    
    return results[:max_results]
