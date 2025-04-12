# my_custom_tools/registry.py
import sys
import os
from portia import InMemoryToolRegistry
sys.path.append(os.path.join(os.path.dirname(__file__), 'my_custom_tools'))
from my_custom_tools.wikipedia_article_reader_tool import WikipediaArticleReaderTool
from my_custom_tools.file_writer_tool import FileWriterTool
from my_custom_tools.file_reader_tool import FileReaderTool
from my_custom_tools.wikipedia_links_tool import WikipediaLinksTool
from my_custom_tools.text_to_json_tool import TextToJsonTool
from my_custom_tools.link_filter_tool import LinkFilterTool


# Register the custom tool
custom_tool_registry = InMemoryToolRegistry.from_local_tools(
    [
        WikipediaArticleReaderTool(),
        FileWriterTool(),
        FileReaderTool(),
        WikipediaLinksTool(),
        TextToJsonTool(),
        LinkFilterTool()
    ],
)
