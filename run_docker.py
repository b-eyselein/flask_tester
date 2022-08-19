from argparse import ArgumentParser
from pathlib import Path
from subprocess import run as subprocess_run

from docker import from_env as docker_client_from_env, DockerClient
from docker.models.containers import Container
from docker.types import Mount

# constants

tester_image_name: str = "new_flask_tester"
intern_result_file_name: str = "result.json"


class BindMount(Mount):
    def __init__(self, source: Path, target: str, read_only: bool = False):
        super().__init__(source=str(source.absolute()), target=target, read_only=read_only, type="bind")


# cli args

argument_parser: ArgumentParser = ArgumentParser()
argument_parser.add_argument("exercise_name")
argument_parser.add_argument("--max_runtime", type=int, default=30)
argument_parser.add_argument("--build", action="store_true")
argument_parser.add_argument("--rm", action="store_true")
args = argument_parser.parse_args()

max_runtime_seconds: int = args.max_runtime
build_image: bool = args.build
exercise_name: str = args.exercise_name

# file names and paths

extern_result_file_name: str = f"{exercise_name}_result.json"

exercise_path: Path = Path.cwd() / exercise_name
results_directory: Path = Path.cwd() / "results"
result_file_path: Path = results_directory / extern_result_file_name

if not results_directory.exists():
    results_directory.mkdir()

# clear result and logs files
if result_file_path.exists():
    result_file_path.unlink()

result_file_path.touch()

# running...
client: DockerClient = docker_client_from_env()

# build server and tester image if requested.
if build_image:
    subprocess_run(f"docker build -t {tester_image_name} .", shell=True)
    # client.images.build(tag=tester_image_name, path=".")

    subprocess_run("docker image prune -f", shell=True)
    # client.images.prune()

print("Running tester container!")
tester_container: Container = client.containers.run(
    image=tester_image_name,
    entrypoint='/bin/bash',
    mounts=[
        BindMount(source=result_file_path, target=f"/data/{intern_result_file_name}"),
        BindMount(source=exercise_path / "app", target=f"/data/app", read_only=True),
        BindMount(source=exercise_path / "testConfig.json", target="/data/testConfig.json", read_only=True),
        BindMount(source=exercise_path / "test_login.py", target="/data/test_login.py", read_only=True),
    ],
    detach=True,
)

print(tester_container.logs())

# stop and remove tester container
tester_container.wait(timeout=max_runtime_seconds)

# if client.containers.get(tester_container.id):
#    tester_container.remove()
