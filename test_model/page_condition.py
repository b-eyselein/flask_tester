from enum import Enum
from typing import Optional, Union, TypedDict, Literal

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

SearchContext = Union[WebDriver, WebElement]


class TextSpecModifier(Enum):
    Contains = 'Contains'
    StartsWith = 'StartsWith'
    EndsWith = 'EndsWith'
    Url = 'Url'


# Result

class TextContentResult(TypedDict):
    awaited: str
    gotten: str


def text_content_result_correct(result: TextContentResult) -> bool:
    return result['awaited'] == result['gotten']


class UrlSpecResult(TypedDict):
    _type: Literal['UrlSpecResult']
    awaited: str
    gotten: str


def url_spec_result_is_correct(url_spec_result: UrlSpecResult) -> bool:
    return url_spec_result['gotten'].endswith(url_spec_result['awaited'])


class FlaskElementSpecResult(TypedDict):
    foundElementsCount: int
    class_name_results: dict[str, bool]
    text_content_result: Optional[TextContentResult]
    attribute_results: dict[str, TextContentResult]
    child_results: list["FlaskElementSpecResult"]


def __element_spec_result_class_names_result_correct__(self: FlaskElementSpecResult) -> bool:
    return len(self['class_name_results']) == 0 or all(self['class_name_results'].values())


def __element_spec_result_text_content_result_correct__(self: FlaskElementSpecResult) -> bool:
    return self['text_content_result'] is None or text_content_result_correct(self['text_content_result'])


def __element_spec_result_attribute_results_correct__(self: FlaskElementSpecResult) -> bool:
    return len(self['attribute_results']) == 0 or all(
        text_content_result_correct(a) for a in self['attribute_results'].values())


def element_spec_result_is_correct(self: FlaskElementSpecResult) -> bool:
    return (
            self['foundElementsCount'] == 1
            and __element_spec_result_class_names_result_correct__(self)
            and __element_spec_result_text_content_result_correct__(self)
            and __element_spec_result_attribute_results_correct__(self)
    )


PageConditionResult = Union[UrlSpecResult, FlaskElementSpecResult]


# Test data

class TextSpec(TypedDict):
    awaitedText: str
    textSpecModifier: Optional[TextSpecModifier]


def evaluate_text_spec(spec: TextSpec, gotten: str) -> TextContentResult:
    return TextContentResult(awaited=spec['awaitedText'], gotten=gotten)


class UrlSpec(TypedDict):
    _type: Literal['UrlSpec']
    awaitedUrl: str


def evaluate_url_spec(url_spec: UrlSpec, driver: WebDriver) -> PageConditionResult:
    return {'awaited': url_spec['awaitedUrl'], 'gotten': driver.current_url}


class ElementSpec(TypedDict):
    _type: Literal['FlaskElementSpec']
    xpathQuery: str
    classNames: list[str]
    textContent: Optional[TextSpec]
    attributes: dict[str, TextSpec]
    children: list["ElementSpec"]


def __evaluate_class_names__(self: ElementSpec, element: WebElement) -> dict[str, bool]:
    class_name = element.get_attribute("class")

    return {value: value in class_name for value in self['classNames']}


def __evaluate_attributes__(self: ElementSpec, element: WebElement) -> dict[str, TextContentResult]:
    return {key: evaluate_text_spec(value, element.get_attribute(key)) for (key, value) in self['attributes'].items()}


def __evaluate_text_content__(self: ElementSpec, element: WebElement) -> Optional[TextContentResult]:
    if 'textContent' in self and self['textContent'] is not None:
        return evaluate_text_spec(self['textContent'], element.text)


def __real_evaluate__(self: ElementSpec, search_context: SearchContext) -> FlaskElementSpecResult:
    found_elements: list[WebElement] = search_context.find_elements_by_xpath(self['xpathQuery'])

    if len(found_elements) != 1:
        return {
            'found_elements_count': len(found_elements),
            'class_name_result': {},
            'text_content_result': None,
            'attribute_results': {},
            'child_results': []
        }

    element = found_elements[0]

    return {
        'foundElementsCount': 1,
        'class_name_results': __evaluate_class_names__(self, element),
        'text_content_result': __evaluate_text_content__(self, element),
        'attribute_results': __evaluate_attributes__(self, element),
        'child_results': [__real_evaluate__(child, element) for child in self['children']],
    }


def evaluate_element_spec(element_spec: ElementSpec, driver: WebDriver) -> PageConditionResult:
    return __real_evaluate__(element_spec, driver)


NewPageCondition = Union[UrlSpec, ElementSpec]


def evaluate_page_condition(page_condition: NewPageCondition, driver: WebDriver) -> PageConditionResult:
    if 'awaitedUrl' in page_condition:
        return evaluate_url_spec(page_condition, driver)
    else:
        return evaluate_element_spec(page_condition, driver)
