import requests
from pydantic import BaseModel, ValidationError
from typing import Optional

# Wikipedia信息的Pydantic模型
class WikipediaInfo(BaseModel):
    title: str
    summary: str
    image: Optional[str]  # 图片链接，可能为空
    wiki_url: str  # 维基百科页面的URL


def get_wikipedia_summary(bird_name):
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{bird_name.replace(' ', '_')}"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        return {
            "title": data.get("title", "未知"),
            "summary": data.get("extract", "暂无介绍"),
            "image": data.get("thumbnail", {}).get("source", "无图片"),
            # 这里明确提取字符串
            "wiki_url": data.get("content_urls", {}).get("desktop", {}).get("page", "#")
        }
    return {
        "title": "Unknown Bird",
        "summary": "Sorry, no information available.",
        "image": None,
        # 更改默认链接为搜索页面，避免指向错误的维基百科页面
        "wiki_url": f"https://en.wikipedia.org/wiki/Special:Search?search={bird_name.replace(' ', '+')}"
    }

