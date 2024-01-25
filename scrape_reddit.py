import os
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options

DRIVER_PATH="./geckodriver"
DRIVER = Service(executable_path=DRIVER_PATH)

firefox_options = Options()

driver = webdriver.Firefox(service=DRIVER, options=firefox_options)

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