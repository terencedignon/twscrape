#!/usr/bin/env python3
"""Crawl tweets from @eurofounder"""
import asyncio
import json
from twscrape import API, gather

async def main():
    api = API()

    # Get user info
    print("Getting user info for @eurofounder...")
    user = await api.user_by_login("eurofounder")

    if not user:
        print("Error: Could not find user @eurofounder")
        return

    print(f"Found user: {user.displayname} (@{user.username})")
    print(f"User ID: {user.id}")
    print(f"Followers: {user.followersCount}")
    print()

    # Crawl tweets
    print("Crawling tweets...")
    tweets = []
    async for tweet in api.user_tweets(user.id, limit=100):
        tweets.append(tweet)
        print(f"Tweet {len(tweets)}: {tweet.date} - {tweet.rawContent[:100]}...")

    # Save to file
    output_file = "eurofounder_tweets.json"
    with open(output_file, "w") as f:
        json.dump([tweet.dict() for tweet in tweets], f, indent=2, default=str)

    print(f"\nCrawled {len(tweets)} tweets and saved to {output_file}")

if __name__ == "__main__":
    asyncio.run(main())
