import json
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Generator, List, Tuple

from .schema import ApplyLog, Output, Plan, PlanLog, State, Validate


@dataclass
class CommandResults:
    command: str
    stdout: str
    stderr: str
    returncode: int

    def json(self) -> Dict[str, Any]:
        return json.loads(self.stdout)

    def raise_error(self) -> None:
        raise RuntimeError(f"Terraform command '{self.command}' failed: {self.stdout}.")


class Tofu:
    """A Python interface for interacting with OpenTofu (Terraform).

    This class provides a high-level interface to interact with OpenTofu/Terraform
    commands, handling JSON output parsing and providing structured data objects.

    Attributes:
        cwd (str | Path): Current working directory for OpenTofu operations.
        binary_path (str): Path to the OpenTofu/Terraform binary.
        log_level (str): Logging level for OpenTofu operations.
        env (Dict[str, str]): Environment variables to pass to OpenTofu.
        version (str): Version of OpenTofu/Terraform being used.
        platform (str): Platform identifier for the OpenTofu binary.

    Raises:
        FileNotFoundError: If the specified OpenTofu/Terraform binary cannot be found.
        RuntimeError: If an incompatible version of OpenTofu/Terraform is detected.
    """

    cwd: str | Path
    """Current working directory."""

    binary_path: str
    log_level: str
    env: Dict[str, str]
    version: str
    platform: str

    def __init__(
        self,
        cwd: str | Path = os.getcwd(),
        binary: str = "tofu",
        log_level: str = "ERROR",
        env: Dict[str, str] = {},
    ):
        """Initialize the Tofu interface.

        Args:
            cwd (str | Path, optional): Working directory for OpenTofu operations. Defaults to current directory.
            binary (str, optional): Name or path of the OpenTofu/Terraform binary. Defaults to "tofu".
            log_level (str, optional): Logging level for OpenTofu operations. Defaults to "ERROR".
            env (Dict[str, str], optional): Additional environment variables to pass to OpenTofu. Defaults to empty dict.

        Raises:
            FileNotFoundError: If the specified binary cannot be found in PATH.
            RuntimeError: If an incompatible version of OpenTofu/Terraform is detected.
        """
        self.cwd = str(cwd)
        self.log_level = log_level
        self.env = env
        self.binary_path = shutil.which(binary)  # type: ignore
        if self.binary_path is None:
            raise FileNotFoundError(
                f"Could not find {binary}, please make sure it is installed."
            )

        results = self._run(["version", "-json"])
        version = results.json()
        self.version = version["terraform_version"]
        self.platform = version["platform"]

        ver_split = self.version.split(".")
        ver_major = int(ver_split[0])

        if ver_major != 1:
            raise RuntimeError(
                f"TofuPy only works with major version 1, found {self.version}."
            )

    def _run(
        self,
        args: List[str],
        raise_on_error: bool = True,
    ) -> CommandResults:
        """Execute an OpenTofu command and capture its output.

        Args:
            args (List[str]): Command arguments to pass to OpenTofu.
            raise_on_error (bool, optional): Whether to raise an exception on command failure. Defaults to True.

        Returns:
            CommandResults: Object containing command execution results.

        Raises:
            RuntimeError: If the command fails and raise_on_error is True.
        """
        args = [self.binary_path] + [str(x) for x in args]

        results = subprocess.run(
            args,
            cwd=self.cwd,
            capture_output=True,
            encoding="utf-8",
            env={
                **os.environ,
                "TF_IN_AUTOMATION": "1",
                "TF_LOG": self.log_level,
                **self.env,
            },
            timeout=None,
        )

        ret_results = CommandResults(
            command=" ".join(args),
            stdout=results.stdout,
            stderr=results.stderr,
            returncode=results.returncode,
        )

        if raise_on_error and ret_results.returncode != 0:
            ret_results.raise_error()

        return ret_results

    def _run_stream(
        self,
        args: List[str],
    ) -> Generator[Dict[str, Any], None, None]:
        """Execute an OpenTofu command and stream its JSON output.

        Args:
            args (List[str]): Command arguments to pass to OpenTofu.

        Yields:
            Generator[Dict[str, Any], None, None]: JSON events from the command output.
        """
        args = [self.binary_path] + [str(x) for x in args]

        process = subprocess.run(
            args,
            cwd=self.cwd,
            stdout=subprocess.PIPE,
            capture_output=False,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            encoding="utf-8",
            bufsize=1,
            env={
                **os.environ,
                "TF_IN_AUTOMATION": "1",
                "TF_LOG": self.log_level,
                **self.env,
            },
            timeout=None,
        )

        event_line = ""
        for buffer in process.stdout:
            if buffer == "\n":
                yield json.loads(event_line)
                event_line = ""
            else:
                event_line += buffer

    def init(
        self,
        disable_backends: bool = False,
        backend_conf: Path | None = None,
        extra_args: List[str] = [],
    ) -> bool:
        """Initialize a new OpenTofu working directory.

        Args:
            disable_backends (bool, optional): Whether to disable backend initialization. Defaults to False.
            backend_conf (Path | None, optional): Path to backend configuration file. Defaults to None.
            extra_args (List[str], optional): Additional arguments to pass to init command. Defaults to empty list.

        Returns:
            bool: True if initialization was successful, False otherwise.
        """
        args = ["init", "-json"] + extra_args
        if disable_backends:
            args += ["-backend=false"]
        elif backend_conf:
            args += ["-backend-config", str(backend_conf)]

        res = self._run(args)
        return res.returncode == 0

    def validate(self) -> Validate:
        """Validate the current OpenTofu configuration.

        Returns:
            Validate: Object containing validation results and diagnostics.
        """
        res = self._run(["validate", "-json"], raise_on_error=False)
        return Validate(res.json())

    def plan(
        self,
        variables: Dict[str, str] = {},
        plan_file: Path | None = None,
        event_handlers: Dict[str, Callable[[Dict[str, Any]], bool]] = {},
        extra_args: List[str] = [],
    ) -> Tuple[PlanLog, Plan | None]:
        """Generate an execution plan for the current configuration.

        Args:
            variables (Dict[str, str], optional): Variables to pass to the plan command. Defaults to empty dict.
            plan_file (Path | None, optional): Path to save the plan file. If None, uses a temporary file. Defaults to None.
            event_handlers (Dict[str, Callable[[Dict[str, Any]], bool]], optional): Event handlers for plan output. Defaults to empty dict.
            extra_args (List[str], optional): Additional arguments to pass to plan command. Defaults to empty list.

        Returns:
            Tuple[PlanLog, Plan | None]: Tuple containing the plan log and the parsed plan object (if available).
        """
        try:
            temp_dir = None
            if not plan_file:
                temp_dir = tempfile.TemporaryDirectory()
                plan_file = Path(temp_dir.name) / "plan.tfplan"

            args = ["plan", "-json", "-out", str(plan_file)] + extra_args

            for key, value in variables.items():
                args += ["-var", f"{key}={value}"]

            output = []
            for event in self._run_stream(args):
                output.append(event)
                if event["type"] in event_handlers:
                    event_handlers[event["type"]](event)
                if "all" in event_handlers:
                    event_handlers["all"](event)

            plan_log = PlanLog(output)

            if plan_file.exists():
                show_res = self._run(["show", "-json", str(plan_file)])
                return plan_log, Plan(show_res.json())

            return plan_log, None

        finally:
            if temp_dir:
                temp_dir.cleanup()

    def apply(
        self,
        plan_file: Path | None = None,
        variables: Dict[str, str] = {},
        destroy=False,
        event_handlers: Dict[str, Callable[[Dict[str, Any]], bool]] = {},
        extra_args: List[str] = [],
    ) -> ApplyLog:
        """Apply the current configuration or a saved plan.

        Args:
            plan_file (Path | None, optional): Path to a saved plan file to apply. Defaults to None.
            variables (Dict[str, str], optional): Variables to pass to the apply command. Defaults to empty dict.
            destroy (bool, optional): Whether to destroy all resources. Defaults to False.
            event_handlers (Dict[str, Callable[[Dict[str, Any]], bool]], optional): Event handlers for apply output. Defaults to empty dict.
            extra_args (List[str], optional): Additional arguments to pass to apply command. Defaults to empty list.

        Returns:
            ApplyLog: Object containing the apply operation results.
        """
        args = ["apply", "-auto-approve", "-json"] + extra_args
        if plan_file:
            args += [str(plan_file)]

        for key, value in variables.items():
            args += ["-var", f"{key}={value}"]

        if destroy:
            args += ["-destroy"]

        output = []
        for event in self._run_stream(args):
            output.append(event)
            if event["type"] in event_handlers:
                event_handlers[event["type"]](event)
            if "all" in event_handlers:
                event_handlers["all"](event)

        return ApplyLog(output)

    def state(self) -> State:
        """Retrieve the current state of the OpenTofu configuration.

        Returns:
            State: Object containing the current state information.
        """
        pull_res = self._run(["state", "pull"])
        state_pull = pull_res.json()

        with tempfile.NamedTemporaryFile(suffix=".tfstate") as tmp:
            tmp.write(pull_res.stdout.encode())
            tmp.seek(0)
            show_res = self._run(["show", "-json", tmp.name])

        return State(
            data=show_res.json(),
            serial=state_pull["serial"],
            lineage=state_pull["lineage"],
        )

    def destroy(self) -> ApplyLog:
        """Destroy all resources managed by the current configuration.

        Returns:
            ApplyLog: Object containing the destroy operation results.
        """
        return self.apply(destroy=True)

    def output(self) -> Dict[str, Output]:
        """Retrieve the outputs from the current configuration.

        Returns:
            Dict[str, Output]: Dictionary mapping output names to their values.
        """
        res = self._run(["output", "-json"])
        ret = {}
        for key, value in res.json().items():
            ret[key] = Output(value)
        return ret
