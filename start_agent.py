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
task_manager.tool_manager.set_coding_tool_sandbox_type("bubblewrap")
task_manager.tool_manager.set_coding_tool_request_approval(False)

task_manager.start_webui_runtime()
webui_process = launch_html_webui_subprocess(
    runtime_url="http://127.0.0.1:8010",
    host="0.0.0.0",
    port=8008,
)

# Optional: create an analytical focusing task manager and register it with the main task manager
if False:
    import botorch.acquisition

    from eaa_core.tool.optimization import BayesianOptimizationTool
    from eaa_imaging.task_manager.tuning.analytical_focusing import (
        AnalyticalScanningMicroscopeFocusingTaskManager,
    )
    from eaa_imaging.tool.imaging.param_tuning import SimulatedSetParameters
    from eaa_imaging.tool.imaging.registration import ImageRegistration
    

    optimization_tool = BayesianOptimizationTool(
        bounds=[
            (-180.0),
            (-200.0)
        ],
        acquisition_function_class=botorch.acquisition.LogExpectedImprovement,
        acquisition_function_kwargs={
            "best_f": 15
        },
        noise_std=1
    )

    analytical_focusing_task_manager = AnalyticalScanningMicroscopeFocusingTaskManager(
        llm_config=llm_config,
        param_setting_tool=beamline_control_tool,
        acquisition_tool=beamline_control_tool,
        optimization_tool=optimization_tool,
        initial_parameters={"z": -190.0},
        parameter_ranges=[
            (-180.0,),
            (-200.0,)
        ],
        run_line_scan_checker=False,
        run_offset_calibration=True,
        registration_target="previous",
        registration_tools=[registration_tool],
        primary_registration_tool_index=0,
        registration_selection_priming_iterations=5,
        line_scan_tool_x_coordinate_args=("sample_x",),
        line_scan_tool_y_coordinate_args=("sample_y",),
        image_acquisition_tool_x_coordinate_args=("x_center",),
        image_acquisition_tool_y_coordinate_args=("y_center",),
    )

    task_manager.tool_manager.subagent_tool.add_task_managers([analytical_focusing_task_manager])
    
    # Reference `run` method arguments:
    # initial_2d_scan_kwargs={"width": 25, "height": 10, "x_center": 1000, "y_center": 1000, "stepsize_x": 1, "stepsize_y": 1},
    # initial_line_scan_kwargs={"positioner_name": "x", "length": 5, "sample_x": 1000, "sample_y": 1000},
    # n_initial_points=3,
    # initial_sampling_window_size=(2.0,),
    # n_max_iterations=20,
    # parameter_change_step_limit=1,

try:
    task_manager.run_conversation(
        n_first_images_to_keep_in_context=2,
        n_last_images_to_keep_in_context=3
    )
finally:
    webui_process.terminate()
    task_manager.stop_webui_runtime()
