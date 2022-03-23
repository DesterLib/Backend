import re
import time
from enum import Enum
from copy import deepcopy
from fastapi import APIRouter
from app.models import DataType
from typing import Any, Dict, Optional

router = APIRouter(
    # dependencies=[Depends(get_token_header)],
    prefix="/search",
    tags=['internals'],
)


class SortType(str, Enum):
    popularity = "popularity"
    rating = "rating"
    modified_time = "modified_time"
    release_date = "release_date"

unwanted_keys = [
    "cast",
    "seasons",
    "homepage",
    "file_name",
    "subtitles",
    "collection",
    "external_ids",
    "last_episode_to_air",
    "next_episode_to_air",
]

@router.get("", response_model=Dict[str, Any], status_code=200)
def query(
    query: Optional[str] = None,
    type: Optional[DataType] = None,
    sort: Optional[SortType] = None,
    offset: Optional[int] = 0,
    limit: Optional[int] = 10
) -> Dict[str, Any]:
    start = time.perf_counter()
    from main import metadata
    if query:
        query = query.strip('\'\"')
        raw_pattern = r'(\b|[\.\+\-_])' + query + r'(\b|[\.\+\-_])?' if ' ' not in query else query.replace(' ', r'.*[\s\.\+\-_]')
        r = re.compile(raw_pattern, flags=2)
        def match(data: dict) -> bool:
            return r.match(data['title'])
    else:
        match = lambda _: True
    movies_match = []
    series_match = []
    for data_type, data in deepcopy(metadata.sorted).items():
        if data_type == 'movies':
            if type == DataType.movies or type is None:
                movies_match = list(filter(match, data))
        elif data_type == 'series':
            if type == DataType.series or type is None:
                series_match = list(filter(match, data))
    results = {}
    if movies_match:
        results['movies'] = sorted(movies_match, key=lambda k: k[sort.value], reverse=True)[offset:offset+limit] if sort else movies_match[offset:offset+limit]
        for item in results['movies']:
            [item.pop(key, None) for key in unwanted_keys]
    if series_match:
        results['series'] = sorted(series_match, key=lambda k: k[sort.value], reverse=True)[offset:offset+limit] if sort else series_match[offset:offset+limit]
        for item in results['series']:
            [item.pop(key, None) for key in unwanted_keys]
    return {
        'ok': True,
        'message': 'success',
        'results': results,
        "time_taken": time.perf_counter() - start
    }



