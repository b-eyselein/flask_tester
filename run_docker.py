from argparse import ArgumentParser
from pathlib import Path
from subprocess import run as subprocess_run
from sys import stderr

from docker import from_env as docker_client_from_env, DockerClient
from docker.models.containers import Container
from docker.types import Mount
from termcolor import colored


class BindMount(Mount):
    def __init__(self, source: Path, target: str, read_only: bool = False):
        super().__init__(source=str(source.absolute()), target=target, read_only=read_only, type="bind")


# cli args

parser = ArgumentParser()
parser.add_argument("-b", "--build", action="store_true", help="build docker image")
parser.add_argument("exercise_name", nargs='?', help="directory of exercise", default="login")

args = parser.parse_args()

build_image: bool = args.build
exercise_name = args.exercise_name

# other consts

max_runtime_seconds: int = 30

tester_image_name: str = "flask_tester"
result_file_name: str = "result.json"

results_directory = Path.cwd() / "results"
exercise_path: Path = Path.cwd() / "examples" / exercise_name
result_file_path: Path = results_directory / result_file_name

# check if results path exists

if not results_directory.exists():
    results_directory.mkdir()
elif not results_directory.is_dir():
    print(colored(f"{results_directory} must be a directory!", 'red'), file=stderr)
    exit(2)

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

print(colored("Running tester container!", 'green'))
tester_container: Container = client.containers.run(
    image=tester_image_name,
    mounts=[
        BindMount(source=result_file_path, target=f"/data/{result_file_name}"),
        BindMount(source=exercise_path / "app", target=f"/data/app", read_only=True),
        BindMount(source=exercise_path / "testConfig.json", target="/data/testConfig.json", read_only=True),
        BindMount(source=exercise_path / "test_login.py", target="/data/test_login.py", read_only=True),
    ],
    detach=True,
)

# stop and remove tester container
tester_container.wait(timeout=max_runtime_seconds)

# if client.containers.get(tester_container.id):
#    tester_container.remove()
