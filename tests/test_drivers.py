import drivers

def test_compat():
    browser = drivers.web()
    browser.get("https://google.com")
