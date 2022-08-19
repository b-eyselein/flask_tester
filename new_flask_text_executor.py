from json import load as json_load, dumps as json_dumps
from pathlib import Path

from test_model.project_test import FlaskProjectTest, ProjectTestResult

# arguments

exercise_name: str = 'login'

# constants

results_folder: Path = Path.cwd() / 'results'
result_file_path: Path = results_folder / f'new_{exercise_name}_result.json'

test_spec_file_path: Path = Path.cwd() / 'login' / 'testSpec.json'

# read test config

with open(test_spec_file_path) as test_spec_file:
    test_spec: FlaskProjectTest = FlaskProjectTest.read_from_json(
        json_load(test_spec_file)
    )

print(json_dumps(test_spec.write_json(), indent=2))

# execute tests

result: ProjectTestResult = test_spec.perform()

print(json_dumps(result.write_json(), indent=2))
