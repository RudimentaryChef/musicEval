"""
Grading runner for agent patch testing.

Workflow:
1. grade() calls:
   - Copy repo, apply test.patch
   - run_tests() [customize this]
   - Returns score (0.0 or 1.0)
"""

import logging
import os
import subprocess
import uuid

logger = logging.getLogger(__name__)


class GradingRunner:
    """
    Grading runner.
    
    Usage:
        runner = GradingRunner(
            problem_id="my_task",
            test_command="pytest {test_files}",
            test_files=["test_foo.py"],
        )
        score = runner.grade()
    
    To customize, override run_tests():
        
        class MyRunner(GradingRunner):
            def run_tests(self) -> tuple[bool, dict]:
                result = subprocess.run(["make", "test"], cwd=self.working_dir)
                return result.returncode == 0, {}
    """

    def __init__(
        self,
        problem_id: str,
        test_command: str = "",
        test_files: list[str] | None = None,
        patches_dir: str = "/home/root/patches",
        repo_path: str | None = None,
    ):
        self.problem_id = problem_id
        self.test_command = test_command
        self.test_files = test_files or []
        self.patches_dir = patches_dir
        self.repo_path = repo_path or f"/home/ubuntu/{os.environ.get('FOLDER_NAME', 'project')}"
        self.working_dir = f"/tmp/grading_{uuid.uuid4()}"

    @property
    def test_patch(self) -> str:
        return os.path.join(self.patches_dir, self.problem_id, "test.patch")

    def grade(self) -> float:
        """
        Run grading and return score.
        
        Returns:
            1.0 if tests pass, 0.0 otherwise
        """
        # Copy repo to grading workspace
        logger.info(f"Copying repo to {self.working_dir}")
        subprocess.run(["cp", "-rT", self.repo_path, self.working_dir], check=True)

        # Apply test patch (adds test files)
        logger.info(f"Applying test patch: {self.test_patch}")
        with open(self.test_patch) as f:
            subprocess.run(
                ["git", "apply"],
                cwd=self.working_dir,
                input=f.read().encode(),
                check=True,
            )

        # Run tests
        success, metadata = self.run_tests()
        
        return 1.0 if success else 0.0

    # =========================================================================
    # CUSTOMIZE THIS
    # =========================================================================

    def run_tests(self) -> tuple[bool, dict]:
        """
        Run tests and return results. Override this for custom logic.
        
        Returns:
            (success, metadata) - success is True if tests pass
        """
        cmd = self.test_command.format(test_files=" ".join(self.test_files))
        logger.info(f"Running: {cmd}")
        
        result = subprocess.run(
            ["bash", "-lc", cmd],
            cwd=self.working_dir,
            capture_output=True,
            text=True,
        )

        return result.returncode == 0, {
            "exit_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }


class CMakeGradingRunner(GradingRunner):
    """
    Grading runner for CMake/GTest C++ projects.

    Builds the specified target with CMake and runs the test binary.

    Usage:
        runner = CMakeGradingRunner(
            problem_id="my_task",
            build_target="LLMEvalTests",
            cmake_subdir="MediaProcessor",
        )
        score = runner.grade()
    """

    def __init__(
        self,
        problem_id: str,
        build_target: str = "LLMEvalTests",
        cmake_subdir: str = "MediaProcessor",
        patches_dir: str = "/home/root/patches",
        repo_path: str | None = None,
    ):
        super().__init__(
            problem_id=problem_id,
            patches_dir=patches_dir,
            repo_path=repo_path,
        )
        self.build_target = build_target
        self.cmake_subdir = cmake_subdir

    def run_tests(self) -> tuple[bool, dict]:
        """Build with CMake and run the GTest binary."""
        cmake_dir = os.path.join(self.working_dir, self.cmake_subdir)
        cmd = (
            f"cd {cmake_dir} && "
            f"mkdir -p build && cd build && "
            f"cmake .. -DBUILD_TESTING=ON 2>&1 && "
            f"cmake --build . --target {self.build_target} 2>&1 && "
            f"./{self.build_target}"
        )
        logger.info(f"Running: {cmd}")

        result = subprocess.run(
            ["bash", "-lc", cmd],
            cwd=self.working_dir,
            capture_output=True,
            text=True,
        )

        return result.returncode == 0, {
            "exit_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }
