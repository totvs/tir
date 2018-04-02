from selenium import webdriver

def inject_jquery(driver):
    driver.execute_script("""var jq = document.createElement('script');
                                      jq.src = 'https://ajax.googleapis.com/ajax/libs/jquery/3.3.1/jquery.min.js';
                                      document.getElementsByTagName('head')[0].appendChild(jq);""")
    
def set_value(driver, selector, value):       
    script = "window.focus(); jQuery(\"" + selector  + "\").val(\"" + value + "\")"
    driver.execute_script(script)

def set_text(driver, selector, text):  
    script = "window.focus(); jQuery(\"" + selector  + "\").text(\"" + text + "\")"
    driver.execute_script(script)

def get_value(driver, selector):  
    script = "window.focus(); return jQuery(\"" + selector  + "\").val()"
    return driver.execute_script(script)

def get_text(driver, selector):  
    script = "window.focus(); return jQuery(\"" + selector  + "\").text()"
    return driver.execute_script(script)

def set_focus(driver, selector):
    script = "window.focus(); jQuery(\"" + selector  + "\").focus();"
    driver.execute_script(script)

def click(driver, selector):
    script = "jQuery(\"" + selector  + "\").click();"
    driver.execute_script(script)