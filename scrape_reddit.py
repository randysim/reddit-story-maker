import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException

os.chmod("./chromedriver.exe", 755)
DRIVER = Service(executable_path="./chromedriver.exe")

options = Options()
options.headless = False
userAgent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.56 Safari/537.36"
options.add_argument(f'user-agent={userAgent}')
driver = webdriver.Chrome(options=options, service=DRIVER)

def parse_post(url):
    print(f"Fetching post data from {url}")
    return {}

# OUTPUT: list of post data
def get_post_data(subreddit=None, post_url=None):
    # STEPS:
    # fetch subreddit page
    # get the top posts of the day
    # for each post, get a couple top comments

    if not subreddit and not post_url:
        print("Error: Missing subreddit or post_url")
    
    if post_url:
        return [parse_post(post_url)]

    subreddit_url = f"https://www.reddit.com/r/{subreddit}/top/?t=day"
    print(f"Fetching posts from {subreddit_url}")
    driver.get(subreddit_url)

    

if __name__ == "__main__":
    print(get_post_data("AskReddit"))