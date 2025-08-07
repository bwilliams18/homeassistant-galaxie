#!/usr/bin/env python3
"""Test script to verify Galaxie API endpoints."""

import asyncio
import aiohttp
import json

BASE_URL = "https://galaxie.app"
API_ENDPOINTS = {
    "previous_race": "/api/previous_race/",
    "next_race": "/api/next_race/",
    "live": "/api/live/",
}


async def test_endpoint(session, endpoint_name, endpoint_path):
    """Test a single API endpoint."""
    url = f"{BASE_URL}{endpoint_path}"
    print(f"Testing {endpoint_name}: {url}")

    try:
        async with session.get(url) as response:
            print(f"  Status: {response.status}")
            if response.status == 200:
                data = await response.json()
                print(f"  Data: {json.dumps(data, indent=2)}")
                return True
            else:
                print(f"  Error: HTTP {response.status}")
                return False
    except Exception as e:
        print(f"  Exception: {e}")
        return False


async def main():
    """Test all API endpoints."""
    print("Testing Galaxie API endpoints...")
    print("=" * 50)

    async with aiohttp.ClientSession() as session:
        results = {}
        for name, path in API_ENDPOINTS.items():
            results[name] = await test_endpoint(session, name, path)
            print()

    print("=" * 50)
    print("Results:")
    for name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {name}: {status}")


if __name__ == "__main__":
    asyncio.run(main())
