from flask import Flask
app=Flask(__name__)

@app.route('/')
def hello_world():
    import time
    from selenium import webdriver

    driver = webdriver.Chrome(r'chromedriver')  # Optional argument, if not specified will search path.
    driver.execute_script("window.open('https://www.gamivo.com/');")
    time.sleep(5) # Let the user actually see something!
    driver.find_element_by_class_name('btn-block').click()
    time.sleep(25) 
    token = driver.execute_script("var ts = window.localStorage.getItem('token'); return ts;")
    print(token)

    driver.execute_script("window.open('https://www.gamivo.com/');")
    time.sleep(3)
    # Switch to the new window
    driver.switch_to.window(driver.window_handles[1])
    token = driver.execute_script("var ts = window.localStorage.getItem('token'); return ts;")
    print(token)

    f = open("token.txt", "w")
    f.write(token)
    f.close()
    return token

if __name__ == "__main__" :
    app.run()    