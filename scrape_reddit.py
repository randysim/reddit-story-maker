import asyncio
import math
import os
from PIL import Image
import random
import re
import time
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import StaleElementReferenceException
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
# firefox_options.add_argument("--headless")

driver = webdriver.Firefox(service=DRIVER, options=firefox_options)
driver.maximize_window()
WINDOW_HEIGHT = driver.execute_script("return document.body.scrollHeight")

remove_text = ["&nbsp;", "&amp;", "<br>", "</br>"]

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

# TODO:
# Have a system where once all the metadata is generated, mark down in a log file so duplicate posts aren't used
# Then, in subsequent runs, fetch for more posts if theres a duplicate post
# for comments, if a comment gets bypassed, fetch more to compensate

# OUTPUT: list of post data
def get_post_meta():
    main_elem = driver.find_element(By.TAG_NAME, "main")
    post_element = main_elem.find_element(By.TAG_NAME, "shreddit-post")

    post_type = post_element.get_attribute("post-type")
    if post_type != "text":
        print("ERROR: post is not of type text")
        return
    
    
    post_meta = {
        "post_title": filter_text(post_element.get_attribute("post-title"), remove_text),
        "author": post_element.get_attribute("author"),
        "author_icon": post_element.get_attribute("icon"),
        "subreddit": post_element.get_attribute("subreddit-prefixed-name"),
        "comment_count": int(post_element.get_attribute("comment-count")),
        "created": post_element.get_attribute("created-timestamp"),
        "score": post_element.get_attribute("score"),
        "content_href": post_element.get_attribute("content-href")
    }

    subreddit = post_meta["subreddit"].split("/")[1]

    # take a screenshot
    ss_path = f"{subreddit}-{post_meta['author']}"
    screenshot(post_element, f"{subreddit}-{post_meta['author']}", "post.png")
    post_meta["img_path"] = f"assets/{ss_path}/post.png"
    post_meta["img_dir"] = ss_path

    return post_meta

def get_post_data(subreddit, count=3, comment_count=10, post_url=None):
    # STEPS:
    # fetch subreddit page
    # get the top posts of the day
    # for each post, get a couple top comments

    if post_url:
        driver.get(post_url)

        try:
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "shreddit-post")))
        except TimeoutException:
            print("Loading took too much time.")
        
        meta = get_post_meta()
        # if post has less comments than requested
        if meta["comment_count"] < comment_count:
            comment_count = meta["comment_count"]

        pd = parse_post(meta, comment_count)

        return [pd]

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
            "post_title": filter_text(post_element.get_attribute("post-title"), remove_text),
            "author": post_element.get_attribute("author"),
            "author_icon": post_element.get_attribute("icon"),
            "subreddit": post_element.get_attribute("subreddit-prefixed-name"),
            "comment_count": int(post_element.get_attribute("comment-count")),
            "created": post_element.get_attribute("created-timestamp"),
            "score": post_element.get_attribute("score"),
            "content_href": post_element.get_attribute("content-href")
        }

        # if post has less comments than requested
        if post_meta["comment_count"] < comment_count:
            comment_count = post_meta["comment_count"]

        # take a screenshot
        ss_path = f"{subreddit}-{post_meta['author']}"
        screenshot(post_element, f"{subreddit}-{post_meta['author']}", "post.png")
        post_meta["img_path"] = f"assets/{ss_path}/post.png"
        post_meta["img_dir"] = ss_path

        try:

            post_data.append(parse_post(post_meta, comment_count))
        except StaleElementReferenceException:
            print("StaleElementReferenceException!")

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
    
    comment_data = []
    comments = driver.find_elements(By.TAG_NAME, "shreddit-comment")
    removed_replies = remove_replies(comments)
    post_meta["comment_count"] -= removed_replies
    comment_count = min(post_meta["comment_count"], comment_count)
    last_y = 0
    for comment in comments:
        if len(comment_data) >= comment_count:
                break
        add_comment_data(comment_data, comment, post_meta)
        last_y = comment.location['y']
        # driver.execute_script("arguments[0].parentNode.removeChild(arguments[0]);", comment)
    comments.clear()

    while len(comment_data) < comment_count:
        comments = driver.find_elements(By.TAG_NAME, "shreddit-comment")[len(comment_data):]
        if len(comments) == 0:
            # look for load more button and wait
            status = click_load_button()
            if not status:
                print("No more comments! Ending loop.")
                break

        removed_replies = remove_replies(comments)
        for comment in comments:
            if len(comment_data) >= comment_count:
                break
            add_comment_data(comment_data, comment, post_meta)
            last_y = comment.location['y']
            # driver.execute_script("arguments[0].parentNode.removeChild(arguments[0]);", comment)
        comments.clear()

        post_meta["comment_count"] -= removed_replies
        comment_count = min(post_meta["comment_count"], comment_count)

    pst = post_meta.copy()
    pst["comments"] = comment_data

    return pst

def add_comment_data(comment_data, comment, post_meta):
    p = comment.find_element(By.TAG_NAME, "p")
    content = filter_text(p.get_attribute("innerHTML"), remove_text)

    if p in ["Comment removed by moderator", "Comment deleted by user", "[Removed]"]:
        return False
    
    c = len(comment_data)

    comment_meta = {
        "author": comment.get_attribute("author"),
        "score": comment.get_attribute("score"),
        "author_icon": post_meta["author_icon"], # replace this later with the right one or a random one
        "content": content
    }

    # take a screenshot
    ss_path = f"{post_meta['img_dir']}/comment{c}.png"
    screenshot(comment, post_meta["img_dir"], f"comment{c}.png")
    comment_meta["img_path"] = f"assets/{ss_path}/comment{c}.png"

    comment_data.append(comment_meta)
    return True

def filter_text(text, blacklist):
    text = text.strip()
    # remove blacklisted words
    text = re.sub('|'.join(blacklist), "", text)
    # remove consecutive spaces
    text = re.sub(' +', ' ', text)
    return text

def screenshot(element, folder, file_name):
    if not os.path.isdir("temp"):
        os.mkdir("temp")
    if not os.path.isdir("assets"):
        os.mkdir("assets")
    if not os.path.isdir(f"temp/{folder}"):
        os.mkdir(f"temp/{folder}")
    if not os.path.isdir(f"assets/{folder}"):
        os.mkdir(f"assets/{folder}")
    
    max_y_coordinate = driver.execute_script("return Math.max( document.body.scrollHeight, document.body.offsetHeight, document.documentElement.clientHeight, document.documentElement.scrollHeight, document.documentElement.offsetHeight ) - window.innerHeight;")

    # scroll + wait a bit
    location = element.location
    size = element.size
    scroll_offset = 20
    scroll_to = location['y']-int(size['height']/2)-scroll_offset
    if scroll_to > max_y_coordinate:
        scroll_to = max_y_coordinate
    if scroll_to < 0:
        scroll_to = 0
    driver.execute_script(f"window.scrollTo(0, {scroll_to})")

    driver.save_screenshot(f"temp/{folder}/{file_name}")

    w = size['width']
    h = size['height']
    x = location['x']
    y = location['y'] - scroll_to
    width = x + w
    height = y + h

    im = Image.open(f'temp/{folder}/{file_name}')
    im = im.crop((int(x), int(y), int(width), int(height)))
    im.save(f"assets/{folder}/{file_name}")

    os.remove(f"temp/{folder}/{file_name}")
    os.rmdir(f"temp/{folder}")

def remove_replies(comments):
    c = len(comments)-1
    removed = 0
    while c >= 0:
        comment = comments[c]
        replies = comment.find_elements(By.TAG_NAME, "shreddit-comment")

        for reply in replies:
            driver.execute_script("arguments[0].parentNode.removeChild(arguments[0]);", reply)
            comments.pop(c+1)
            removed += 1
        c -= 1
    
    print(f"Removed {removed} replies from {len(comments)} comments!")
    return removed

def click_load_button():
    try:
        print("Loading more comments...")
        comment_tree = driver.find_element(By.TAG_NAME, "shreddit-comment-tree")
        button = comment_tree.find_element(By.CLASS_NAME, "button-brand")
        button.click()
        print("Waiting 5s to load more comments...")
        time.sleep(5)
        return True
    except:
        return False
    

if __name__ == "__main__":
    print(get_post_data(subreddit="AskReddit", count=1, comment_count=30, post_url="https://www.reddit.com/r/ApplyingToCollege/comments/19f9fv1/college_admissions_is_toxic/"))