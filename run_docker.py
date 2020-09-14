from pathlib import Path
from subprocess import run as subprocess_run

from docker import from_env as docker_client_from_env, DockerClient
from docker.models.containers import Container
from docker.types import Mount


class BindMount(Mount):
    def __init__(self, source: Path, target: str, read_only: bool = False):
        super().__init__(source=str(source.absolute()), target=target, read_only=read_only, type="bind")


build_image: bool = True

tester_image_name: str = "flask_tester"
exercise_name: str = "login"
result_file_name: str = "result.json"

exercise_path: Path = Path.cwd() / exercise_name
results_path: Path = Path.cwd() / "results"

result_file_path: Path = results_path / result_file_name
tester_logs_file_path: Path = results_path / "tester_logs.txt"
server_logs_file_path: Path = results_path / "server_logs.txt"

# clear result and logs files
for file_path in [result_file_path, tester_logs_file_path, server_logs_file_path]:
    if file_path.exists():
        file_path.unlink()

    file_path.touch()

# running...
client: DockerClient = docker_client_from_env()

# build server and tester image if requested.
if build_image:
    subprocess_run(f"docker build -t {tester_image_name} .", shell=True)
    # client.images.build(tag=tester_image_name, path=".")

    subprocess_run("docker image prune -f", shell=True)
    # client.images.prune()

tester_container: Container = client.containers.run(
    image=tester_image_name,
    mounts=[
        BindMount(source=result_file_path, target=f"/data/{result_file_name}"),
        BindMount(source=server_logs_file_path, target=f"/data/server_logs.txt"),
        BindMount(source=exercise_path / "app", target=f"/data/app", read_only=True),
        BindMount(source=exercise_path / "test_config.json", target="/data/test_config.json", read_only=True),
        BindMount(source=exercise_path / "test_login.py", target="/data/test_login.py", read_only=True),
    ],
    detach=True,
)

run_cmd: str = f"""\
docker run -it --rm \\
    -v {result_file_path}:/data/result.json \\
    -v {server_logs_file_path}:/data/server_logs.txt \\
    -v {exercise_path}/app:/data/app:ro \\
    -v {exercise_path}/test_config.json:/data/test_config.json:ro \\
    -v {exercise_path}/test_login.py:/data/test_login.py:ro \\
    {tester_image_name}
"""

print(run_cmd)

# stop and remove tester container
tester_container.stop()

with tester_logs_file_path.open("w") as tester_logs_file:
    tester_logs_file.write(tester_container.logs().decode())

#if client.containers.get(tester_container.id):
#    tester_container.remove()
