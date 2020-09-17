from dataclasses import dataclass, field
from enum import Enum
from json import load as json_load, dump as json_dump
from pathlib import Path
from random import shuffle
from subprocess import run as subprocess_run, CompletedProcess
from sys import stderr
from typing import List, TypedDict, Tuple, Optional, Dict

test_config_file_path: Path = Path.cwd() / "testConfig.json"
result_file_path: Path = Path.cwd() / "result.json"


class WebTestConfigJson(TypedDict):
    id: int
    testName: str
    dependencies: Optional[List[str]]


class TestConfigJson(TypedDict):
    testFileName: str
    testClassName: str
    tests: List[WebTestConfigJson]


class TestStatus(Enum):
    Ready = "Ready"
    Success = "Successful"
    Failure = "Failure"
    Skipped = "Skipped"


@dataclass()
class WebTestConfig:
    id: int
    test_name: str
    status: TestStatus = TestStatus.Ready

    dependencies: List["WebTestConfig"] = field(default_factory=list)

    dependents: List["WebTestConfig"] = field(default_factory=list)

    def __post_init__(self):
        for dependency in self.dependencies:
            dependency.dependents.append(self)

    def depends_on_test(self, other_test: "WebTestConfig") -> bool:
        return other_test in self.dependencies

    def needs_to_be_skipped(self):
        self.status = TestStatus.Skipped

        for dependent in self.dependents:
            dependent.needs_to_be_skipped()

    def can_be_run(self) -> bool:
        return self.status != TestStatus.Skipped and all(d.status == TestStatus.Success for d in self.dependencies)


@dataclass()
class WebTestResult:
    test_id: int
    test_name: str
    successful: bool
    stdout: List[str]
    stderr: List[str]

    def to_json(self) -> Dict:
        return {
            "testId": self.test_id,
            "testName": self.test_name,
            "successful": self.successful,
            "stdout": self.stdout,
            "stderr": self.stderr,
        }


def execute_tests(test_file_name: str, test_class_name: str, tests: List[WebTestConfig]) -> List[WebTestResult]:
    runnable_tests: List[WebTestConfig] = [t0 for t0 in tests if len(t0.dependencies) == 0]

    results: List[WebTestResult] = []

    while len(runnable_tests) > 0:
        current_test: WebTestConfig = runnable_tests.pop()

        # execute tests
        current_result = execute_test(current_test, test_class_name, test_file_name)

        # update dependents
        for other_test in current_test.dependents:
            if not current_result.successful:
                other_test.needs_to_be_skipped()
            elif other_test.can_be_run():
                runnable_tests.append(other_test)

        results.append(current_result)

    return results


def execute_test(current_test: WebTestConfig, test_class_name: str, test_file_name: str) -> WebTestResult:
    result: CompletedProcess = subprocess_run(
        [f"python3 -m unittest {test_file_name}.{test_class_name}.{current_test.test_name}"],
        shell=True,
        capture_output=True,
    )

    successful: bool = result.returncode == 0

    # set result
    current_test.status = TestStatus.Success if successful else TestStatus.Failure

    return WebTestResult(
        test_id=current_test.id,
        test_name=current_test.test_name,
        successful=successful,
        stdout=result.stdout.decode().split("\n"),
        stderr=result.stderr.decode().split("\n"),
    )


def load_tests() -> Tuple[str, str, List[WebTestConfig]]:
    with test_config_file_path.open("r") as test_config_file:
        json: TestConfigJson = json_load(test_config_file)

        web_test_configs: List[WebTestConfig] = []

        for test_config_json in json["tests"]:
            web_test_configs.append(
                WebTestConfig(
                    id=test_config_json["id"],
                    test_name=test_config_json["testName"],
                    dependencies=[
                        t_x for t_x in web_test_configs if t_x.test_name in test_config_json.get("dependencies", [])
                    ],
                )
            )

        return json["testFileName"], json["testClassName"], web_test_configs


if __name__ == "__main__":

    if not test_config_file_path.exists():
        print(f"Test config file {test_config_file_path} does not exist!", file=stderr)
        exit(1)

    the_test_file_name, the_test_class_name, web_tests = load_tests()

    shuffle(web_tests)

    all_results = execute_tests(the_test_file_name, the_test_class_name, web_tests)

    with result_file_path.open("w") as result_file:
        json_dump({"results": [r.to_json() for r in all_results]}, result_file, indent=2)
