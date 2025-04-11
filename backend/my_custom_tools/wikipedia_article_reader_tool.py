# my_custom_tools/wikipedia_article_reader_tool.py

import wikipediaapi as wikipedia_api
from pydantic import BaseModel, Field
from portia.tool import Tool, ToolRunContext

class WikipediaArticleReaderSchema(BaseModel):
    """Schema defining the inputs for the WikipediaArticleReaderTool."""

    article_title: str = Field(
        ...,
        description="The title of the Wikipedia article to fetch content from."
    )


class WikipediaArticleReaderTool(Tool[str]):
    """Fetches the entire content of a Wikipedia article."""

    id: str = "wikipedia_article_reader_tool"
    name: str = "Wikipedia Article Reader Tool"
    description: str = (
        "Fetches the entire content of a Wikipedia article based on the title provided. "
        "The tool will return the full text of the article, including sections and subsections."
    )
    args_schema: type[BaseModel] = WikipediaArticleReaderSchema
    output_schema: tuple[str, str] = ("str", "str: full content of the Wikipedia article")

    def run(self, _: ToolRunContext, article_title: str) -> str:
        """Run the Wikipedia Article Reader Tool."""
        # Initialize the Wikipedia API
        wiki = wikipedia_api.Wikipedia('izaakbot', 'en')

        try:
            # Fetch the article
            page = wiki.page(article_title)
            if page.exists():
                return page.text
            else:
                raise Exception(f"Article '{article_title}' not found.")
        except Exception as e:
            raise Exception(f"An error occurred while fetching the article: {str(e)}")
