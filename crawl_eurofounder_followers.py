#!/usr/bin/env python3
"""Crawl followers of @eurofounder"""
import asyncio
import json
from twscrape import API

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

    # Crawl followers
    print("Crawling followers...")
    followers = []
    async for follower in api.followers(user.id, limit=10000):
        followers.append(follower)
        if len(followers) % 100 == 0:
            print(f"Crawled {len(followers)} followers...")

    # Save to file
    output_file = "eurofounder_followers.json"
    with open(output_file, "w") as f:
        json.dump([follower.dict() for follower in followers], f, indent=2, default=str)

    print(f"\nCrawled {len(followers)} followers and saved to {output_file}")

if __name__ == "__main__":
    asyncio.run(main())
