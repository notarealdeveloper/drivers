import drivers

def test_compat():
    browser = drivers.Chrome()
    browser.get("https://google.com")
