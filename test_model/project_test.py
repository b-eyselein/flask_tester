from dataclasses import dataclass, field
from json import load as json_load, dump as json_dump
from typing import Any

from selenium.webdriver import Chrome, ChromeOptions
from selenium.webdriver.remote.webdriver import WebDriver

from test_model.action import FlaskAction, FlaskActionStep, ActionStepResult, perform_flask_action
from test_model.json_helpers import HasJsonFormat, HasJsonWrites
from test_model.page_condition import PageConditionResult, NewPageCondition, evaluate_page_condition

default_driver_options: ChromeOptions = ChromeOptions()
default_driver_options.headless = True
default_driver_options.add_argument("--no-sandbox")


def __get_driver__() -> WebDriver:
    return Chrome(options=default_driver_options)


# Results


@dataclass()
class PageTestResult(HasJsonWrites):
    saved_actions_performed: bool
    initial_page_results: list[PageConditionResult]
    action_results: list[ActionStepResult] = field(default_factory=list)

    def write_json(self) -> dict[str, Any]:
        return {
            "savedActionsPerformed": self.saved_actions_performed,
            "initialPageResults": self.initial_page_results,
            "actionResults": self.action_results
        }


@dataclass()
class ProjectTestResult(HasJsonWrites):
    page_test_results: dict[str, PageTestResult]

    def write_json(self) -> dict[str, Any]:
        return {
            "pageTestResults": {key: value.write_json() for (key, value) in self.page_test_results.items()}
        }


# Tests

@dataclass()
class FlaskSavedAction(HasJsonFormat["FlaskSavedAction"]):
    start_url: str
    actions: list[FlaskAction]
    depends_on: list[str] = field(default_factory=list)

    def perform(self, driver: WebDriver) -> bool:
        return all(perform_flask_action(action, driver) for action in self.actions)

    @staticmethod
    def read_from_json(json: dict[str, Any]) -> "FlaskSavedAction":
        return FlaskSavedAction(
            start_url=json["startUrl"],
            actions=json["actions"],
            depends_on=json["dependsOn"],
        )

    def write_json(self) -> dict[str, Any]:
        return {
            "startUrl": self.start_url,
            "actions": self.actions,
            "dependsOn": self.depends_on,
        }


@dataclass()
class FlaskPageTest(HasJsonFormat["FlaskPageTest"]):
    url: str
    depends_on: list[str] = field(default_factory=list)
    depends_on_saved_actions: list[str] = field(default_factory=list)
    initial_page_conditions: list[NewPageCondition] = field(default_factory=list)
    actions: list[FlaskActionStep] = field(default_factory=list)

    def perform(self, base_url: str, saved_actions: dict[str, FlaskSavedAction]) -> PageTestResult:
        driver: WebDriver = __get_driver__()

        driver.get(base_url + self.url)

        return PageTestResult(
            saved_actions_performed=all(saved_actions[name].perform(driver) for name in self.depends_on_saved_actions),
            initial_page_results=[evaluate_page_condition(condition, driver) for condition in
                                  self.initial_page_conditions],
            action_results=[action.evaluate(driver) for action in self.actions],
        )

    @staticmethod
    def read_from_json(json: dict[str, Any]) -> "FlaskPageTest":
        return FlaskPageTest(
            url=json["url"],
            depends_on=json["dependsOn"],
            depends_on_saved_actions=json["dependsOnSavedActions"],
            initial_page_conditions=json["initialPageSpec"],
            actions=[FlaskActionStep.read_from_json(value) for value in json["actions"]],
        )

    def write_json(self) -> dict[str, Any]:
        return {
            "url": self.url,
            "dependsOnSavedActions": self.depends_on_saved_actions,
            "dependsOn": self.depends_on,
            "initialPageSpec": self.initial_page_conditions,
            "actions": [action_step.write_json() for action_step in self.actions],
        }


@dataclass()
class FlaskProjectTest(HasJsonFormat["FlaskProjectTest"]):
    base_url: str
    tests: dict[str, FlaskPageTest]
    saved_actions: dict[str, FlaskSavedAction] = field(default_factory=dict)

    def perform(self) -> ProjectTestResult:
        return ProjectTestResult(
            page_test_results={
                test_name: page_test.perform(self.base_url, self.saved_actions) for (test_name, page_test) in
                self.tests.items()
            }
        )

    @staticmethod
    def read_from_json(json: dict[str, Any]) -> "FlaskProjectTest":
        return FlaskProjectTest(
            base_url=json["baseUrl"],
            tests={key: FlaskPageTest.read_from_json(value) for (key, value) in json["tests"].items()},
            saved_actions={
                key: FlaskSavedAction.read_from_json(value) for (key, value) in json["savedActions"].items()
            },
        )

    def write_json(self) -> dict[str, Any]:
        return {
            "baseUrl": self.base_url,
            "tests": {key: value.write_json() for (key, value) in self.tests.items()},
            "savedAction": {key: value.write_json() for (key, value) in self.saved_actions.items()},
        }


if __name__ == "__main__":
    with open("../login/testSpec.json") as test_spec_file, open("../results/new_login_result.json", "w") as result_file:
        project_test: FlaskProjectTest = FlaskProjectTest.read_from_json(json_load(test_spec_file))

        results: ProjectTestResult = project_test.perform()

        json_dump(results.write_json(), result_file, indent=2)
