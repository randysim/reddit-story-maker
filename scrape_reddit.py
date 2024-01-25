import math
import random
import re
import time
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException

DRIVER_PATH="./geckodriver"
DRIVER = Service(executable_path=DRIVER_PATH)

firefox_options = Options()

# Add user agents to the FirefoxOptions object
user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/89.0",
]
user_agent = random.choice(user_agents)
firefox_options.add_argument(f"user-agent={user_agent}")
firefox_options.add_argument("--headless")

driver = webdriver.Firefox(service=DRIVER, options=firefox_options)

remove_text = ["&nbsp;", "&amp;"]

"""
POST META DATA USED TO GENERATE REDDIT IMAGE
content-href="https://www.reddit.com/r/AskReddit/comments/19egxbn/couples_over_40_and_childless_how_has_life_turned/"
comment-count="2804"
created-timestamp="2024-01-24T13:20:06.945000+0000" 
post-title="Couples over 40 and childless, how has life turned out for you? Do you regret not having children?" 
post-type="text" 
score="4055" 
subreddit-prefixed-name="r/AskReddit" 
author="NetworkOver7742" 
icon="https://preview.redd.it/snoovatar/avatars/bd8699f4-4c5f-421e-8d0a-d678bc41d935-headshot.png?width=64&amp;height=64&amp;crop=smart&amp;auto=webp&amp;s=0afc459d8f6f14b6fad99261cd6d0fbbe3629afd">
"""

# OUTPUT: list of post data
def get_post_data(subreddit, count, comment_count):
    # STEPS:
    # fetch subreddit page
    # get the top posts of the day
    # for each post, get a couple top comments

    if not subreddit:
        print("Error: Missing subreddit")

    subreddit_url = f"https://www.reddit.com/r/{subreddit}/top/?t=day"
    print(f"Fetching posts from {subreddit_url}")
    driver.get(subreddit_url)

    try:
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "shreddit-post")))
    except TimeoutException:
        print("Loading took too much time.")
    
    post_elements = driver.find_elements(By.TAG_NAME, "shreddit-post")[:count]
    count = len(post_elements)

    # time needed to click on a post
    sleep_time = 1 + (random.random() * 3)
    print(f"Site loaded! Waiting {sleep_time}s...")
    time.sleep(sleep_time)

    post_data = []
    c = 0

    for post_element in post_elements:
        post_type = post_element.get_attribute("post-type")
        if post_type != "text":
            continue

        post_meta = {
            "post_title": post_element.get_attribute("post-title"),
            "author": post_element.get_attribute("author"),
            "author_icon": post_element.get_attribute("icon"),
            "subreddit": post_element.get_attribute("subreddit-prefixed-name"),
            "comment_count": post_element.get_attribute("comment-count"),
            "created": post_element.get_attribute("created-timestamp"),
            "score": post_element.get_attribute("score"),
            "content_href": post_element.get_attribute("content-href")
        }

        post_data.append(parse_post(post_meta, comment_count))
        c += 1

        if c >= count:
            # ignore sleep time at last post
            break

        sleep_time = 10 + math.floor(random.random() * 3)
        print(f"Finished! Sleeping for {sleep_time}.")
        time.sleep(sleep_time)

        print(f"Parsed {c}/{count} posts.")
        
    print(f"Finished fetching {count} post{'s' if count > 1 else ''} from {post_meta['subreddit']}.")
    return post_data

"""
comment meta data:
<shreddit comment stuff>
author
score
author_icon (doesn't exist, but just use OP's icon)
</>

comment info:
<p>{comment}</p>
deleted statuses: "Comment removed by moderator", "Comment deleted by user", "[Removed]"

"""
def parse_post(post_meta, comment_count):
    print(f"Fetching post data from {post_meta['content_href']}")
    
    driver.get(post_meta['content_href'])

    try:
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "shreddit-comment")))
    except TimeoutException:
        print("Loading took too much time.")
    
    comments = driver.find_elements(By.TAG_NAME, "shreddit-comment")[:comment_count]
    comment_count = len(comments)

    comment_data = []

    for comment in comments:
        p = comment.find_element(By.TAG_NAME, "p")
        content = filter_text(p.get_attribute("innerHTML"), remove_text)

        if p in ["Comment removed by moderator", "Comment deleted by user", "[Removed]"]:
            continue

        comment_meta = {
            "author": comment.get_attribute("author"),
            "score": comment.get_attribute("score"),
            "author_icon": post_meta["author_icon"], # replace this later with the right one or a random one
            "content": content
        }
        comment_data.append(comment_meta)
    
    pst = post_meta.copy()
    pst["comments"] = comment_data

    return pst

def filter_text(text, blacklist):
    text = text.strip()
    # remove blacklisted words
    text = re.sub('|'.join(blacklist), "", text)
    # remove consecutive spaces
    text = re.sub(' +', ' ', text)
    return text

if __name__ == "__main__":
    print(get_post_data(subreddit="AskReddit", count=1, comment_count=10))