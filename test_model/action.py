from dataclasses import dataclass, field
from typing import Any, TypedDict, Optional, Literal

from selenium.webdriver.remote.webdriver import WebDriver

from test_model.json_helpers import HasJsonFormat
from test_model.page_condition import PageConditionResult, NewPageCondition, evaluate_page_condition


# Result

class ActionStepResult(TypedDict):
    actionPerformed: bool
    postConditionResults: list[PageConditionResult]


# Tests

class FlaskAction(TypedDict):
    _type: Literal['FlaskClickAction', 'FlaskSendKeysAction']
    xpathQuery: str
    keysToSend: Optional[str]


def perform_flask_action(action: FlaskAction, driver: WebDriver) -> bool:
    elements = driver.find_elements_by_xpath(action['xpathQuery'])

    if len(elements) != 0:
        return False

    element = elements[0]

    if action['_type'] == 'FlaskClickAction':
        element.click()
    else:
        element.send_keys(action['keysToSend'])

    return True


@dataclass()
class FlaskActionStep(HasJsonFormat["FlaskActionStep"]):
    action: FlaskAction
    post_conditions: list[NewPageCondition] = field(default_factory=list)

    def evaluate(self, driver: WebDriver) -> ActionStepResult:
        return {
            "actionPerformed": perform_flask_action(self.action, driver),
            "postConditionResults": [
                evaluate_page_condition(post_condition, driver) for post_condition in self.post_conditions
            ]
        }

    @staticmethod
    def read_from_json(json: dict[str, Any]) -> "FlaskActionStep":
        return FlaskActionStep(
            action=json["action"],
            post_conditions=json["postConditions"],
        )

    def write_json(self) -> dict[str, Any]:
        return {
            "action": self.action,
            "postConditions": self.post_conditions,
        }
