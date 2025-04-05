from pydantic import BaseModel
from typing import Set, Optional

# Wikipedia信息的Pydantic模型
class WikipediaInfo(BaseModel):
    title: str
    summary: str
    image: Optional[str]  # 图片链接，可能为空
    wiki_url: str  # 维基百科页面的URL

# 图像分析的响应模型
class ImageAnalysisResponse(BaseModel):
    """
    Response model for image analysis.

    example:
    {
        "id": 1,
        "labels": [
            "American Crow"
        ],
        "wiki_info": {
            "title": "American Crow",
            "summary": "The American crow is a large, all-black bird...",
            "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/...",
            "wiki_url": "https://en.wikipedia.org/wiki/American_Crow"
        }
    }
    """
    id: int  # 图像ID
    labels: Set[str]  # 使用Set保证标签的唯一性
    wiki_info: WikipediaInfo  # 包含的维基百科信息
