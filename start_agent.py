import os
import logging

import tifffile
import matplotlib.pyplot as plt

from eaa_core.api.llm_config import OpenAIConfig, ArgoConfig
from eaa_core.gui.html import launch_html_webui_subprocess
from eaa_core.task_manager.base import BaseTaskManager
from eaa_imaging.tool.imaging.acquisition import SimulatedAcquireImage
from eaa_imaging.tool.imaging.param_tuning import SimulatedSetParameters
from eaa_imaging.tool.imaging.registration import ImageRegistration

logger = logging.getLogger()
logger.setLevel(logging.INFO)


acquisition_tool = SimulatedAcquireImage(
    whole_image=image,
    add_axis_ticks=True,
    add_grid_lines=False,
    invert_yaxis=False,
    add_line_scan_candidates_to_image=False,
    plot_image_in_log_scale=False,
    poisson_noise_scale=100,
    scan_jitter=0,
    gaussian_psf_sigma=1,
)
param_setting_tool = SimulatedSetParameters(
    acquisition_tool=acquisition_tool, 
    parameter_names=["z"],
    true_parameters=[3.0],
    parameter_ranges=[
        (0.0,),
        (10.0,)
    ],
    drift_factor=30,
    blur_factor=5
)
param_setting_tool.set_parameters([8.0])

registration_tool = ImageRegistration(
    name="ncc",
    registration_method="ncc",
    registration_algorithm_kwargs={"max_shift": 7}
    # name="error_minimization"
)


if False:
    llm_config=OpenAIConfig(
        # model="gpt-5",
        model="gpt-4o-2024-11-20",
        # model="gpt-4o-mini",
        base_url="https://api.openai.com/v1",
        api_key=os.environ["OPENAI_API_KEY"],
    )

if False:
    llm_config=OpenAIConfig(
        model="google/gemini-2.5-pro",
        base_url="https://openrouter.ai/api/v1",
        api_key=os.environ["OPENROUTER_API_KEY"],
    )
    
if True:
    llm_config = ArgoConfig(
        model="gpt55",
        base_url="https://apps-dev.inside.anl.gov/argoapi/v1",
        api_key="mingdu",
    )

task_manager = BaseTaskManager(
    llm_config=llm_config,
    tools=[acquisition_tool, param_setting_tool, registration_tool],
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
