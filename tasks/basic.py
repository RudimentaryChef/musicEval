"""Basic difficulty tasks.

Each task is a scenario that handles its own setup and grading.
"""

from env import env, setup_task, make_prompt
from grading import CMakePatchGrader, Grade, ValidateMode


@env.scenario("thread-result-aggregation")
async def thread_result_aggregation(hints_enabled: bool = False, validate_mode: ValidateMode | None = None):
    """Fix the thread result aggregation bug in AudioProcessor::filterChunks()."""

    setup_task(
        task_id="thread_result_aggregation",
        base="baseline",
        test="test",
        golden="golden",
        validate_mode=validate_mode,
    )

    prompt = make_prompt("""There is a bug in AudioProcessor::filterChunks() in
MediaProcessor/src/AudioProcessor.cpp.

The filterChunks() method processes audio chunks in parallel via a ThreadPool.
Each thread returns a bool indicating success or failure. After all threads
complete, the results must be aggregated such that if ANY chunk fails, the
overall result should be false.

However, there is a bug in how the results are combined — the current code
silently discards earlier thread failures. Find and fix this bug.

IMPORTANT: Only modify MediaProcessor/src/AudioProcessor.cpp. Do not modify
any cmake files or test files.
""")


    _ = yield prompt

    grade = Grade.from_subscores([
        CMakePatchGrader.grade(
            weight=1.0,
            problem_id="thread_result_aggregation",
            build_target="LLMEvalTests",
            cmake_subdir="MediaProcessor",
            validate_mode=validate_mode,
        )
    ])

    yield grade.score
