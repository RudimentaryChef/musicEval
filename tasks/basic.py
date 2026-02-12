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
@env.scenario("thread-result-aggregation-v2")
async def thread_result_aggregation_v2(hints_enabled: bool = False, validate_mode: ValidateMode | None = None):
      """Fix the thread result aggregation bug (variant 2)."""

      setup_task(
          task_id="thread_result_aggregation_v2",
          base="baseline",          # git branch names in your MusicRemover repo
          test="test",
          golden="golden",
          validate_mode=validate_mode,
      )

      prompt = make_prompt("""There is a bug somewhere in the media processing pipeline.

A function runs work across multiple items in parallel using a thread pool. Each worker returns a bool for success or failure. The top level function is supposed to return false if any worker fails.

Symptom:
The top level function sometimes returns true even when one or more workers fail. This is nondeterministic and depends on thread scheduling and timing.

Your task: locate and fix the bug so the top level result is always false if any worker fails.

Constraints:

Do not modify any build files or tests. You are not given access to the real tests, that check if it works, but feel free to make your own 
(just don't add them to the github.) You do not need to verify the project/build or fighting the stale cmake build directory the agent sees.
      """)

      _ = yield prompt

      grade = Grade.from_subscores([
          CMakePatchGrader.grade(
              weight=1.0,
              problem_id="thread_result_aggregation_v2",
              build_target="LLMEvalTests",
              cmake_subdir="MediaProcessor",
              validate_mode=validate_mode,
          )
      ])

      yield grade.score
@env.scenario("thread-result-aggregation-v3")
async def thread_result_aggregation_v3(hints_enabled: bool = False, validate_mode: ValidateMode | None = None):
      """Fix the thread result aggregation bug (variant 3)."""

      setup_task(
          task_id="thread_result_aggregation_v3",
          base="baseline",          # git branch names in your MusicRemover repo
          test="test",
          golden="golden",
          validate_mode=validate_mode,
      )

      prompt = make_prompt("""There is a bug somewhere in the MediaProcessor pipeline.

Symptom:
A reliability regression was introduced. A test that used to pass now fails intermittently.

Your task:
Find the root cause and fix it.

Constraints:
Do not modify any build files or tests. You are not given access to the real tests. You may create local tests for yourself but do not commit them. 
    """)

      _ = yield prompt

      grade = Grade.from_subscores([
          CMakePatchGrader.grade(
              weight=1.0,
              problem_id="thread_result_aggregation_v3",
              build_target="LLMEvalTests",
              cmake_subdir="MediaProcessor",
              validate_mode=validate_mode,
          )
      ])

      yield grade.score
