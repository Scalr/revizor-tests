from selene.api import s, by


def button(title=None, icon=None):
    if title:
        return s(by.xpath(f'//span[text()="{title}"]//ancestor::a'))
    elif icon:
        return s(by.xpath(f'//span[contains(@class, "x-btn-icon-{icon}")]//ancestor::a'))


class Tooltip:
    def __init__(self, message):
        self.element = s(by.xpath(f'//div[text()="{message}"]/ancestor::div[contains(@class, "x-tip-message")]'))

    def close(self):
        self.element.s('img').click()


tooltip = Tooltip
