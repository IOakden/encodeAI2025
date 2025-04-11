from pathlib import Path
import json
from pydantic import BaseModel, Field
from portia.tool import Tool, ToolRunContext


class TextToJsonToolSchema(BaseModel):
    """Schema for TextToJsonTool."""

    article_title: str = Field(..., description="The main Wikipedia article title (acts as the central node)")


class TextToJsonTool(Tool[dict]):
    """Reads a list of Wikipedia articles from a text file and appends them to a JSON graph."""

    id: str = "text_to_json_tool"
    name: str = "Text to JSON Tool"
    description: str = "Creates or updates a JSON graph of Wikipedia articles linked to a main article."
    args_schema: type[BaseModel] = TextToJsonToolSchema
    output_schema: tuple[str, str] = ("dict", "The updated JSON graph structure.")

    def run(self, _: ToolRunContext, article_title: str) -> dict:
        """Run the TextToJsonTool."""
        base_path = Path(__file__).resolve().parent
        data_file = base_path.parent / "data.txt"
        json_file = base_path.parent / "graph.json"

        # Read data.txt
        if not data_file.exists():
            raise FileNotFoundError(f"{data_file} does not exist.")

        with data_file.open("r", encoding="utf-8") as f:
            article_lines = [line.strip() for line in f if line.strip()]

        # Load or create JSON graph
        if json_file.exists():
            with json_file.open("r", encoding="utf-8") as f:
                graph = json.load(f)
        else:
            graph = {"nodes": [], "links": []}

        existing_ids = {node["name"]: node["id"] for node in graph["nodes"]}
        next_id = max(existing_ids.values(), default=0) + 1

        # Add main article node if not present
        if article_title not in existing_ids:
            main_id = next_id
            graph["nodes"].append({"id": main_id, "name": article_title})
            existing_ids[article_title] = main_id
            next_id += 1
        else:
            main_id = existing_ids[article_title]

        # Add article nodes and links
        for article in article_lines:
            if article not in existing_ids:
                graph["nodes"].append({"id": next_id, "name": article})
                existing_ids[article] = next_id
                graph["links"].append({"source": main_id, "target": next_id, "label": ""})
                next_id += 1
            else:
                # Create link if not already present
                existing_link = any(
                    link["source"] == main_id and link["target"] == existing_ids[article]
                    for link in graph["links"]
                )
                if not existing_link:
                    graph["links"].append({"source": main_id, "target": existing_ids[article], "label": ""})

        # Save the updated graph
        with json_file.open("w", encoding="utf-8") as f:
            json.dump(graph, f, indent=2)

        return graph
