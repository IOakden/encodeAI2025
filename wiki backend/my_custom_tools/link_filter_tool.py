from pathlib import Path
from typing import List
import re
from pydantic import BaseModel, Field
from portia.tool import Tool, ToolRunContext


class LinkFilterToolSchema(BaseModel):
    """Schema for LinkFilterTool."""
    
    article_title: str = Field(..., description="The name of the main article to avoid linking to itself.")
    input_file: str = Field(..., description="The path to the .txt file containing the links to filter.")


class LinkFilterTool(Tool[List[str]]):
    """Filters out irrelevant or self-referencing links from a .txt file."""

    id: str = "link_filter_tool"
    name: str = "Link Filter Tool"
    description: str = "Filters out links that contain the article title, numbers, or colons."
    args_schema: type[BaseModel] = LinkFilterToolSchema
    output_schema: tuple[str, str] = ("list[str]", "List of cleaned, filtered links.")

    def run(self, _: ToolRunContext, article_title: str, input_file: str) -> List[str]:
        """Run the LinkFilterTool."""
        file_path = Path(input_file)

        if not file_path.exists():
            raise FileNotFoundError(f"{file_path} not found.")

        article_title_lower = article_title.lower()

        with file_path.open("r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]

        # Define filters
        def is_valid(link: str) -> bool:
            link_lower = link.lower()
            return (
                article_title_lower not in link_lower and
                not re.search(r"\d", link) and
                ":" not in link
            )

        filtered_links = [link for link in lines if is_valid(link)]

        return filtered_links
