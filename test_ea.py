import httpx
import asyncio

async def test_ea():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.ea.com/games/nhl/nhl-24/pro-clubs/overview',
        'Origin': 'https://www.ea.com',
        'Connection': 'keep-alive',
    }
    params = {
        'platform': 'common-gen5',
        'clubName': 'Boys II Men'
    }
    url = 'https://proclubs.ea.com/api/nhl/clubs/search'
    
    async with httpx.AsyncClient(follow_redirects=True) as client:
        try:
            print(f"Testing {url}...")
            response = await client.get(url, params=params, headers=headers, timeout=10.0)
            print(f"Status Code: {response.status_code}")
            print(f"Response (first 500 chars): {response.text[:500]}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_ea())
