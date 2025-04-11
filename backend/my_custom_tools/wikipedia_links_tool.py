# my_custom_tools/wikipedia_links_tool.py

import wikipediaapi
from pydantic import BaseModel, Field
from portia.tool import Tool, ToolRunContext

class WikipediaLinksToolSchema(BaseModel):
    """Schema defining the inputs for the WikipediaLinksTool."""

    article_title: str = Field(
        ...,
        description="The title of the Wikipedia article to get links from. For example, 'Birds of Prey'",
    )

class WikipediaLinksTool(Tool[list[str]]):
    """Retrieves all the internal Wikipedia article links from a given article."""

    id: str = "wikipedia_links_tool"
    name: str = "Wikipedia Links Tool"
    description: str = (
        "Retrieves all the internal Wikipedia article links from a given article using wikipedia-api."
    )
    args_schema: type[BaseModel] = WikipediaLinksToolSchema
    output_schema: tuple[str, str] = ("list[str]", "A list of Wikipedia article titles linked from the given article")

    def run(self, _: ToolRunContext, article_title: str) -> list[str]:
        """Run the Wikipedia Links Tool."""

        wiki = wikipediaapi.Wikipedia("izaakbot","en")
        page = wiki.page(article_title)

        if not page.exists():
            return [f"Article '{article_title}' does not exist on Wikipedia."]

        return list(page.links.keys())
