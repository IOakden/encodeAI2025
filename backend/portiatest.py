from dotenv import load_dotenv
import os
import json
from portia import (
    Config,
    LogLevel,
    Portia,
    StorageClass,
    LLMModel,
)
from my_custom_tools.registry import custom_tool_registry

from portia.open_source_tools.search_tool import SearchTool

load_dotenv()

# Check if the API key is loaded
api_key = os.getenv('OPENAI_API_KEY')

my_config = Config.from_default(
    llm_provider= "OPENAI",
    llm_model_name=LLMModel.GPT_4_O,
    storage_class=StorageClass.DISK, 
    storage_dir='demo_runs', # Amend this based on where you'd like your plans and plan runs saved!
    default_log_level=LogLevel.DEBUG
)


# Instantiate a Portia instance. Load it with the default config and with some example tools
portia = Portia(config=my_config, tools=custom_tool_registry)

# Generate the plan from the user query
plan = portia.plan('Get all the links from the wikipedia page for Analytic Philosophy. Write them all on a new line to a new file called data.txt. Then transform this into a json using your text to json tool.')


# [OPTIONAL] INSERT CODE WHERE YOU SERVE THE PLAN TO THE USER OR ITERATE ON IT IN ANY WAY

# Run the generated plan
plan_run = portia.run_plan(plan)

def write_json_to_file(data, filename):
    # Check if the file exists, create it if not
    if not os.path.exists(filename):
        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)
            print(f"File '{filename}' created and data written.")
    else:
        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)
            print(f"Data written to existing file '{filename}'.")


# Serialise into JSON and print the output
json_plan = (plan_run.model_dump_json(indent=2))

print(json_plan.outputs.final_output)