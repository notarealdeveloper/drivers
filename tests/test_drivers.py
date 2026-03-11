import drivers

def test_compat():
    browser = drivers.web(headless=True)
    browser.get("https://google.com")
