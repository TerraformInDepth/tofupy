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
    """Tofu class to interact with Terraform."""

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
        """_summary_

        Args:
            cwd (str | Path, optional): _description_. Defaults to os.getcwd().
            binary (str, optional): _description_. Defaults to "tofu".
            log_level (str, optional): _description_. Defaults to "ERROR".
            env (Dict[str, str], optional): _description_. Defaults to {}.

        Raises:
            FileNotFoundError: _description_
            RuntimeError: _description_
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
        """_summary_

        Args:
            args (List[str]): _description_
            raise_on_error (bool, optional): _description_. Defaults to True.

        Returns:
            CommandResults: _description_
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
        """_summary_

        Args:
            args (List[str]): _description_

        Yields:
            Generator[str, None, None]: _description_
        """
        args = [self.binary_path] + [str(x) for x in args]

        process = subprocess.run(
            args,
            cwd=self.cwd,
            stdout=subprocess.PIPE,
            capture_output=False,
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
        """_summary_

        Args:
            disable_backends (bool, optional): _description_. Defaults to False.
            backend_conf (Path | None, optional): _description_. Defaults to None.
            extra_args (List[str], optional): _description_. Defaults to [].

        Returns:
            bool: _description_
        """
        args = ["init", "-json"] + extra_args
        if disable_backends:
            args += ["-backend=false"]
        elif backend_conf:
            args += ["-backend-config", str(backend_conf)]

        res = self._run(args)
        return res.returncode == 0

    def validate(self) -> Validate:
        """_summary_

        Returns:
            Validate: _description_
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
        """_summary_

        Args:
            variables (Dict[str, str], optional): _description_. Defaults to {}.
            plan_file (Path | None, optional): _description_. Defaults to None.
            event_handlers (Dict[str, Callable[[Dict[str, Any]], bool]], optional): _description_. Defaults to {}.
            extra_args (List[str], optional): _description_. Defaults to [].

        Returns:
            Tuple[PlanLog, Plan | None]: _description_
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
        return self.apply(destroy=True)

    def output(self) -> Dict[str, Output]:
        res = self._run(["output", "-json"])
        ret = {}
        for key, value in res.json().items():
            ret[key] = Output(value)
        return ret
