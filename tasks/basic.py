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

    prompt = make_prompt("""The LLMEvalTests test suite is failing.

The test verifies that AudioProcessor::filterChunks() correctly
aggregates results from parallel thread execution. When audio chunks
are processed in parallel via a ThreadPool, the method must detect
if ANY chunk fails — not just the last one.

Run the failing test to see the error, find the bug in the source
code, and fix it.

To build and run the test:
  cd MediaProcessor/build
  cmake .. -DBUILD_TESTING=ON
  cmake --build . --target LLMEvalTests
  ./LLMEvalTests
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
