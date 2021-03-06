import typing as tp

from selene.core.entity import Element
from selenium.webdriver.common.keys import Keys
from selene.api import s, ss, by, be
from selene.core import query


class BaseComponent:
    element: Element

    def __getattr__(self, item):
        return getattr(self.element, item)


class Button(BaseComponent):
    def __init__(
        self,
        title: tp.Optional[str] = None,
        icon: tp.Optional[str] = None,
        ticon: tp.Optional[str] = None,
        qtip: tp.Optional[str] = None,
        xpath: tp.Optional[str] = None,
        parent: tp.Optional[Element] = None,
    ):
        if title:
            selector = f'//span[text()="{title}"]//ancestor::a'
        elif icon:
            selector = f'//span[contains(@class, "x-btn-icon-{icon}")]//ancestor::a'
        elif ticon:
            selector = f'//a[contains(@class, "x-grid-action-button-{ticon}")]'
        elif qtip:
            selector = f'//a[@data-qtip="{qtip}"]'
        elif xpath:
            selector = xpath
        else:
            raise AssertionError("You must set one of input parameters")
        if parent:
            self.element = parent.ss(by.xpath(f".{selector}")).element_by(be.visible)
        else:
            self.element = ss(by.xpath(selector)).element_by(be.visible)

    def is_disabled(self):
        return "x-btn-disabled" in self.element.get(query.attribute("class"))


button = Button


class LoadingModal(BaseComponent):
    def __init__(self, title: str, parent: tp.Optional[Element] = None):
        self.element = s(by.xpath(f'//div[text()="{title}" and contains(@class, "x-title-text")]'))
        if parent:
            self.element = parent.s(
                by.xpath(f'.//div[text()="{title}" and contains(@class, "x-title-text")]')
            )


loading_modal = LoadingModal
loading_page = loading_modal("Loading page...")

# TODO: Add complete component for Loading page modal


class Tooltip(BaseComponent):
    def __init__(self, message: str, parent: tp.Optional[Element] = None):
        self.element = s(
            by.xpath(
                f"//div[contains(text(), '{message}')]/ancestor::div[contains(@class, 'x-tip-message')]"
            )
        )
        if parent:
            self.element = parent.s(
                by.xpath(
                    f".//div[contains(text(), '{message}')]/ancestor::div[contains(@class, 'x-tip-message')]"
                )
            )

    def close(self):
        self.element.s(".x-tool-close-white").click()


tooltip = Tooltip


class Input(BaseComponent):
    def __init__(self, label: str, parent: tp.Optional[Element] = None):
        self.element = ss(
            by.xpath(
                f"//span[contains(@class, 'x-form-item-label-text') and text()='{label}']/following::div/input"
            )
        ).element_by(be.visible)
        if parent:
            self.element = parent.ss(
                by.xpath(
                    f".//span[contains(@class, 'x-form-item-label-text') and text()='{label}']/following::div/input"
                )
            ).element_by(be.visible)

    def has_error(self):
        return "x-form-invalid-field" in self.element.get(query.attribute("class"))

    @property
    def error(self):
        return self.element.s(by.xpath("parent::div/following-sibling::div//li")).get(
            query.attribute("textContent")
        )


input = Input


class Combobox(BaseComponent):
    def __init__(self, label: str, parent: tp.Optional[Element] = None):
        self.element = ss(
            by.xpath(
                f'//span[contains(@class, "x-form-item-label-text") and text()="{label}"]/following::div[1]/div'
            )
        ).element_by(be.visible)
        if parent:
            self.element = parent.ss(
                by.xpath(
                    f'.//span[contains(@class, "x-form-item-label-text") and text()="{label}"]/following::div[1]/div'
                )
            ).element_by(be.visible)
        self._bound_id = None

    @property
    def bound_id(self):
        if self._bound_id is None:
            self.open()
            self._bound_id = "{}-picker".format(
                self.element.get(query.attribute("id")).rsplit("-", 1)[0]
            )
            self.close()
        return self._bound_id

    def open(self):
        self.element.s("div").click()
        self.element.s("div.x-form-field-loading").should(be.not_.visible, timeout=30)

    def close(self):
        self.element.s("div").click()

    def get_values(self) -> [str]:
        elems = s(f"#{self.bound_id}").s("ul").ss('.x-boundlist-item[role="option"]')
        values = [e.get_attribute("textContent").strip() for e in elems]
        return list(filter(lambda x: x, values))

    def set_value(self, value: str):
        values = self.get_values()
        if value not in values:
            raise AssertionError(f"Value {value} not exist in combobox: {values}")
        self.open()
        for _ in range(len(values) + 1):
            if self.get_active_item() == value:
                self.element.s("input").type(Keys.ENTER)
                return
            self.element.s("input").type(Keys.ARROW_DOWN)

    def get_active_item(self) -> str:
        return s(f'#{self.bound_id} .x-boundlist-item-over[role="option"]').get(query.text).strip()

    def reload(self):
        self.element.s("div.x-form-field-clear-cache").click()

    def has_error(self):
        return "x-form-invalid-field" in self.element.s("input").get(query.attribute("class"))

    @property
    def error(self):
        return self.element.s('div[role="alert"]').s("li").get(query.attribute("textContent"))


combobox = Combobox


class Toggle(BaseComponent):
    def __init__(self, label: str, parent: tp.Optional[Element] = None):
        self.element = ss(
            by.xpath(
                f'//span[contains(@class, "x-form-item-label-text") and text()="'
                f'{label}"]/following::div[1]'
            )
        ).element_by(be.visible)
        if parent:
            self.element = parent.ss(
                by.xpath(
                    f'//span[contains(@class, "x-form-item-label-text") and text()="'
                    f'{label}"]/following::div[1]'
                )
            ).element_by(be.visible)

    def toggle(self):
        self.element.s("input").click()

    def is_checked(self):
        # return 'x-form-cb-checked' in self.element.get(query.attribute('class'))
        return self.element.s("input").get(query.attribute("checked"))


toggle = Toggle


class SearchField(BaseComponent):
    def __init__(self, parent: tp.Optional[Element] = None):
        self.element = ss(by.xpath("//div[text()='Search']")).element_by(be.visible)
        if parent:
            self.element = parent.ss(by.xpath("//div[text()='Search']")).element_by(be.visible)

    def set_value(self, value):
        self.element.click()
        # s(by.xpath("//div[text()='Search']/following-sibling::input")).set_value(value)
        self.element.s(by.xpath("following-sibling::input")).set_value(value)


search = SearchField
