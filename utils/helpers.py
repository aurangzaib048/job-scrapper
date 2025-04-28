import re

import html2text
from cacheout import Cache

cache = Cache(maxsize=1000)


def is_hacker_news_url(url):
    return "news.ycombinator.com" in url


def html_to_markdown(html):
    """Convert HTML to Markdown"""

    markdown_converter = html2text.HTML2Text()
    markdown_converter.ignore_links = False  # Keep the links in the markdown
    markdown_converter.body_width = 0
    markdown_content = markdown_converter.handle(html)

    return markdown_content


def resolve_email(text):
    """
    Deobfuscate an obfuscated email address
    """

    # Regular expression to match the pattern for obfuscated email addresses like "name dot domain at domain"
    patterns = [
        r"([a-zA-Z0-9_-]+( dot [a-zA-Z0-9_-]+)? at [a-zA-Z0-9_-]+ dot [a-zA-Z0-9_-]+)",
        # similar but [at] instead of " at " and [dot] instead of " dot "
        r"([a-zA-Z0-9_-]+( ?\[dot\] ?[a-zA-Z0-9_-]+)? ?\[at\] ?[a-zA-Z0-9_-]+ ?\[dot\] ?[a-zA-Z0-9_-]+)",
        # Same but just [at] is used
        r"([a-zA-Z0-9_.-]+\s?\[at\]\s?[a-zA-Z0-9_.-]+)",
    ]

    for pattern in patterns:
        # Find the line containing the email using regex
        match = re.search(pattern, text)

        if match:
            # Extract the matched text
            obfuscated_email = match.group(0)
            # Replace " dot " with "." and " at " with "@"
            email = obfuscated_email.replace(" dot ", ".").replace(" at ", "@")
            email = email.replace(" [dot] ", ".").replace(" [at] ", "@")
            email = email.replace("[dot]", ".").replace("[at]", "@")

            # Add lime break and append email
            return text + "\n🪄 *Deobfuscated email:* " + email

    return text


def format_dt(date):
    """Format datetime"""

    if not date:
        return None

    return date.strftime("%m/%d/%Y %I:%M:%S %p")


def get_hn_link_user(hn_user):
    """Get link to user profile"""
    return f"https://news.ycombinator.com/user?id={hn_user}"


def get_hn_link_comment(hn_id):
    """Get link to comment"""
    return f"https://news.ycombinator.com/item?id={hn_id}"
