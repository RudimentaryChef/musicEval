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

        # Apply test patch (adds test files). Use --3way to handle cases
        # where the agent modified the same files the patch touches.
        logger.info(f"Applying test patch: {self.test_patch}")
        with open(self.test_patch) as f:
            patch_content = f.read().encode()
        result = subprocess.run(
            ["git", "apply", "--3way"],
            cwd=self.working_dir,
            input=patch_content,
            capture_output=True,
        )
        if result.returncode != 0:
            logger.warning(f"git apply --3way failed (rc={result.returncode}): {result.stderr.decode()}")
            # Fallback 1: git apply --reject (applies what it can, creates .rej for rest)
            result2 = subprocess.run(
                ["git", "apply", "--reject", "--whitespace=fix"],
                cwd=self.working_dir,
                input=patch_content,
                capture_output=True,
            )
            logger.info(f"git apply --reject rc={result2.returncode}")
            if result2.returncode != 0:
                logger.warning(f"git apply --reject stderr: {result2.stderr.decode()}")
                # Check for .rej files to understand what failed
                rej_result = subprocess.run(
                    ["find", ".", "-name", "*.rej", "-type", "f"],
                    cwd=self.working_dir,
                    capture_output=True,
                    text=True,
                )
                if rej_result.stdout.strip():
                    logger.warning(f"Rejected patch hunks: {rej_result.stdout.strip()}")

                # Fallback 2: use patch command which is more forgiving with fuzz
                logger.info("Trying patch -p1 --force as final fallback")
                result3 = subprocess.run(
                    ["patch", "-p1", "--force", "--no-backup-if-mismatch"],
                    cwd=self.working_dir,
                    input=patch_content,
                    capture_output=True,
                )
                logger.info(f"patch -p1 --force rc={result3.returncode}")
                if result3.returncode != 0:
                    logger.warning(f"patch fallback stderr: {result3.stderr.decode()}")
                    logger.info(f"patch fallback stdout: {result3.stdout.decode()}")

        # Run tests
        success, metadata = self.run_tests()

        if not success:
            logger.error(f"Tests FAILED for {self.problem_id}")
            if metadata.get("stderr"):
                logger.error(f"Test stderr (last 2000 chars): {metadata['stderr'][-2000:]}")
            if metadata.get("stdout"):
                logger.info(f"Test stdout (last 2000 chars): {metadata['stdout'][-2000:]}")

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
        import shutil

        cmake_dir = os.path.join(self.working_dir, self.cmake_subdir)
        # Remove any pre-existing build directory to avoid stale cmake cache
        # paths from the Docker image. FetchContent will re-fetch deps.
        build_dir = os.path.join(cmake_dir, "build")
        if os.path.isdir(build_dir):
            shutil.rmtree(build_dir)
            logger.info(f"Removed stale build directory: {build_dir}")

        # Verify test infrastructure files exist before building
        test_cmake = os.path.join(cmake_dir, "cmake", "test.cmake")
        test_cpp = os.path.join(cmake_dir, "tests", "LLMEvalTests.cpp")
        cmakelists = os.path.join(cmake_dir, "CMakeLists.txt")
        for fpath, label in [(test_cmake, "test.cmake"), (test_cpp, "LLMEvalTests.cpp")]:
            if os.path.exists(fpath):
                logger.info(f"Test file present: {label}")
            else:
                logger.error(f"Test file MISSING: {label} ({fpath})")

        # Check that CMakeLists.txt includes the test cmake file
        if os.path.exists(cmakelists):
            with open(cmakelists) as f:
                content = f.read()
            if "test.cmake" in content:
                logger.info("CMakeLists.txt includes test.cmake")
            else:
                logger.error("CMakeLists.txt does NOT include test.cmake — test target will be missing")

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
