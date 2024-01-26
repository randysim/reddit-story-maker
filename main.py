from scrape_reddit import get_post_data

"""
EXAMPLE POST_DATA
post_data: [
    {
        post_title: String,
        author: String,
        author_icon: String,
        subreddit: String,
        comment_count: Int,
        created: String,
        score: Int,
        content_href: String,
        img_path: String,
        comments: [
            {
                author: String,
                score: Int,
                author_icon: String,
                content: String,
                img_path: String
            }
        ]
    },
    ...
]
"""


def main():
    # post data
    post_data = get_post_data(
        subreddit="AskReddit", count=5, comment_count=15
    )

if __name__ == "__main__":
    main()