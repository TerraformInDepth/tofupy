import os
from pathlib import Path

import typer

from tofupy import Tofu

app = typer.Typer()


@app.command()
def scan(
    working_dir: Path = typer.Argument(help="Working directory", default=os.getcwd()),
):
    typer.echo(f"Scanning {working_dir}")
    tofu = Tofu(cwd=working_dir)
    log, plan = tofu.plan()
    if not plan or plan.errored:
        typer.echo("Plan failed")
        return

    for address, change_container in plan.resource_changes.items():
        if change_container.type == "aws_vpc_security_group_ingress_rule":
            typer.echo(f"Found security group: {address}")
            change = change_container.change
            if "cidr_ipv4" in change.after:
                if change.after["cidr_ipv4"] == "0.0.0.0/0":
                    typer.echo(
                        f"Security group {address} allows all traffic from the internet"
                    )


if __name__ == "__main__":
    app()
