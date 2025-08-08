# Simple Twitter/X poster using tweepy (OAuth 1.1)
import os
import tweepy

class TwitterPoster:
    def __init__(self, api):
        self.api = api

    @classmethod
    def from_env(cls):
        key = os.environ.get("TWITTER_API_KEY")
        secret = os.environ.get("TWITTER_API_SECRET")
        token = os.environ.get("TWITTER_ACCESS_TOKEN")
        token_secret = os.environ.get("TWITTER_ACCESS_SECRET")
        if not all([key, secret, token, token_secret]):
            raise EnvironmentError("Twitter credentials not fully set in environment variables.")
        auth = tweepy.OAuth1UserHandler(key, secret, token, token_secret)
        api = tweepy.API(auth)
        return cls(api)

    def post(self, text):
        # basic safety: 280 chars
        if len(text) > 280:
            text = text[:275] + "…"
        self.api.update_status(status=text)
