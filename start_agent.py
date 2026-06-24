import os
import logging

from eaa_core.api.llm_config import OpenAIConfig, ArgoConfig
from eaa_core.gui.html import launch_html_webui_subprocess
from eaa_core.task_manager.base import BaseTaskManager
from eaa_core.tool.mcp_client import MCPTool
from eaa_imaging.tool.imaging.registration import ImageRegistration

logger = logging.getLogger()
logger.setLevel(logging.INFO)


beamline_control_tool = MCPTool(
    {
        "mcpServers": {
            "beamline_control": {
                "url": "http://localhost:8050/mcp",
                "transport": "http",
            }
        }
    }
)

registration_tool = ImageRegistration(
    name="ncc",
    registration_method="ncc",
    registration_algorithm_kwargs={"max_shift": 7}
    # name="error_minimization"
)

    
llm_config = ArgoConfig(
    model="gpt55",
    base_url="https://apps-dev.inside.anl.gov/argoapi/v1",
    api_key="mingdu",
)

task_manager = BaseTaskManager(
    llm_config=llm_config,
    tools=[beamline_control_tool, registration_tool],
    use_webui=True,
    skill_dirs=[
        "/data/programs/eaa/packages/eaa-imaging/src/eaa_imaging/skills",
        "/data/programs/eaa/packages/eaa-core/src/eaa_core/skills",
    ],
)
task_manager.set_coding_tool_sandbox_type("bubblewrap")
task_manager.set_coding_tool_request_approval(False)

task_manager.start_webui_runtime()
webui_process = launch_html_webui_subprocess(
    runtime_url="http://127.0.0.1:8010",
    host="0.0.0.0",
    port=8008,
)

try:
    task_manager.run_conversation(
        n_first_images_to_keep_in_context=2,
        n_last_images_to_keep_in_context=3
    )
finally:
    webui_process.terminate()
    task_manager.stop_webui_runtime()
