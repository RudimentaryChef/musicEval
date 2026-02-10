"""Graders for evaluating agent solutions."""

import os

from .runner import CMakeGradingRunner, GradingRunner
from .spec import Grader, ValidateMode


class AgentPatchGrader(Grader):
    """
    Grader that applies test.patch and runs tests.
    
    Usage:
        AgentPatchGrader.grade(
            weight=1.0,
            problem_id="my_task",
            test_files=["test_foo.py"],
        )
    
    Custom test command:
        AgentPatchGrader.grade(
            weight=1.0,
            problem_id="my_task",
            test_files=["test_foo.test.ts"],
            test_command="yarn test {test_files}",
        )
    """

    name = "AgentPatchGrader"
    DEFAULT_TEST_COMMAND = "uv run pytest {test_files}"

    @classmethod
    def compute_score(
        cls,
        test_files: list[str],
        problem_id: str | None = None,
        test_command: str | None = None,
        validate_mode: ValidateMode | None = None,
        **kwargs,
    ) -> tuple[float, dict]:
        """
        Run tests and return score.

        Args:
            test_files: Test files to run
            problem_id: Problem ID for patches (default: PROBLEM_ID env)
            test_command: Test command with {test_files} placeholder
        
        Returns:
            (score, metadata) - score is 1.0 if tests pass, 0.0 otherwise
        """
        pid = problem_id or os.environ.get("PROBLEM_ID")
        if not pid:
            raise ValueError("problem_id required (or set PROBLEM_ID env)")

        runner = GradingRunner(
            problem_id=pid,
            test_command=test_command or cls.DEFAULT_TEST_COMMAND,
            test_files=test_files,
        )

        score = runner.grade()

        # when testing with baseline fail, we want to ensure that the baseline actually fails, so we invert the score
        if validate_mode == "baseline_fail":
            score = 1.0 if score == 0.0 else 0.0

        return (score, {})


class CMakePatchGrader(Grader):
    """
    Grader for CMake/GTest C++ projects.

    Applies test.patch, builds with CMake, and runs the GTest binary.

    Usage:
        CMakePatchGrader.grade(
            weight=1.0,
            problem_id="thread_result_aggregation",
            build_target="LLMEvalTests",
            cmake_subdir="MediaProcessor",
        )
    """

    name = "CMakePatchGrader"

    @classmethod
    def compute_score(
        cls,
        build_target: str = "LLMEvalTests",
        cmake_subdir: str = "MediaProcessor",
        problem_id: str | None = None,
        validate_mode: ValidateMode | None = None,
        **kwargs,
    ) -> tuple[float, dict]:
        pid = problem_id or os.environ.get("PROBLEM_ID")
        if not pid:
            raise ValueError("problem_id required (or set PROBLEM_ID env)")

        runner = CMakeGradingRunner(
            problem_id=pid,
            build_target=build_target,
            cmake_subdir=cmake_subdir,
        )

        score = runner.grade()

        if validate_mode == "baseline_fail":
            score = 1.0 if score == 0.0 else 0.0

        return (score, {})
