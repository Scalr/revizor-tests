from ui.pages.base import BasePage


class TfBasePage(BasePage):
    _menu = None

    @property
    def menu(self):
        if self._menu is None:
            from .topmenu import TfTopMenu  #FIXME: Think about more clearly method
            self._menu = TfTopMenu()
        return self._menu
