#-----------------------------------------------------------------------------
# Copyright (c) 2012 - 2017, Anaconda, Inc. All rights reserved.
#
# Powered by the Bokeh Development Team.
#
# The full license is in the file LICENSE.txt, distributed with this software.
#-----------------------------------------------------------------------------
''' Define a Pytest plugin for a Bokeh-specific testing tools

'''

#-----------------------------------------------------------------------------
# Boilerplate
#-----------------------------------------------------------------------------
from __future__ import absolute_import, division, print_function, unicode_literals

import logging
log = logging.getLogger(__name__)

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

# Standard library imports

# External imports
import pytest
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# Bokeh imports
from bokeh.io import save
from bokeh._testing.util.selenium import INIT, RESULTS, wait_for_canvas_resize

#-----------------------------------------------------------------------------
# Globals and constants
#-----------------------------------------------------------------------------

pytest_plugins = (
    "bokeh._testing.plugins.bokeh",
    "bokeh._testing.plugins.file_server",
    "bokeh._testing.plugins.selenium",
)

#-----------------------------------------------------------------------------
# General API
#-----------------------------------------------------------------------------

@pytest.fixture
def output_file_url(request, file_server):
    from bokeh.io import output_file
    filename = request.function.__name__ + '.html'
    file_obj = request.fspath.dirpath().join(filename)
    file_path = file_obj.strpath
    url = file_path.replace('\\', '/')  # Windows-proof

    output_file(file_path, mode='inline')

    def tear_down():
        if file_obj.isfile():
            file_obj.remove()
    request.addfinalizer(tear_down)

    return file_server.where_is(url)

class _BokehModelPage(object):

    def __init__(self, model, driver, output_file_url, has_no_console_errors):
        self._driver = driver
        self._model = model
        self._has_no_console_errors = has_no_console_errors

        save(self._model)

        self._driver.get(output_file_url)

        self.init_results()

    @property
    def results(self):
        WebDriverWait(self._driver, 10).until(EC.staleness_of(self.test_div))
        self.test_div = self._driver.find_element_by_class_name("bokeh-test-div")
        return self._driver.execute_script(RESULTS)

    @property
    def driver(self):
        return self._driver

    def init_results(self):
        self._driver.execute_script(INIT)
        self.test_div = self._driver.find_element_by_class_name("bokeh-test-div")

    def click_element_at_position(self, element, x, y):
        actions = ActionChains(self._driver)
        actions.move_to_element_with_offset(element, x, y)
        actions.click()
        actions.perform()

    def drag_element_at_position(self, element, x, y, dx, dy, mod=None):
        actions = ActionChains(self._driver)
        if mod:
            actions.key_down(mod)
        actions.move_to_element_with_offset(element, x, y)
        actions.click_and_hold()
        actions.move_by_offset(dx, dy)
        actions.release()
        if mod:
            actions.key_up(mod)
        actions.perform()

    def has_no_console_errors(self):
        return self._has_no_console_errors(self._driver)

@pytest.fixture()
def bokeh_model_page(driver, output_file_url, has_no_console_errors):
    def func(model):
        return _BokehModelPage(model, driver, output_file_url, has_no_console_errors)
    return func

class _SinglePlotPage(_BokehModelPage):

    # model may be a layout, but should only contain a single plot
    def __init__(self, model, driver, output_file_url, has_no_console_errors):
        super(_SinglePlotPage, self).__init__(model, driver, output_file_url, has_no_console_errors)

        self.canvas = self._driver.find_element_by_tag_name('canvas')
        wait_for_canvas_resize(self.canvas, self._driver)

    def click_canvas_at_position(self, x, y):
        self.click_element_at_position(self.canvas, x, y)

    def click_custom_action(self):
        button = self._driver.find_element_by_class_name("bk-toolbar-button-custom-action")
        button.click()

    def drag_canvas_at_position(self, x, y, dx, dy):
        self.drag_element_at_position(self.canvas, x, y, dx, dy)

    def get_toolbar_button(self, name):
        return self.driver.find_element_by_class_name('bk-tool-icon-' + name)


@pytest.fixture()
def single_plot_page(driver, output_file_url, has_no_console_errors):
    def func(model):
        return _SinglePlotPage(model, driver, output_file_url, has_no_console_errors)
    return func

#-----------------------------------------------------------------------------
# Dev API
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Private API
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Code
#-----------------------------------------------------------------------------
