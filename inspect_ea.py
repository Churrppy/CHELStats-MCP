import httpx
import asyncio
import json

async def inspect_ea():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.ea.com/games/nhl/nhl-25/pro-clubs/overview',
        'Origin': 'https://www.ea.com',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-site',
    }
    params = {'platform': 'common-gen5', 'clubId': '20227'}
    url = 'https://proclubs.ea.com/api/nhl/members/stats'
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params, headers=headers, timeout=10.0)
            print(f"Status Code: {response.status_code}")
            print(f"Raw response (first 1000 chars): {response.text[:1000]}")
            data = response.json()
            print(f"Type of data: {type(data)}")
            if isinstance(data, dict):
                print(f"Keys in dict: {list(data.keys())}")
                for k, v in data.items():
                    print(f"Type of value for key {k}: {type(v)}")
                    if isinstance(v, list) and len(v) > 0:
                        print(f"First item in list under {k}: {json.dumps(v[0], indent=2)[:500]}")
            elif isinstance(data, list):
                print(f"Length of list: {len(data)}")
                if len(data) > 0:
                    print(f"First item in list: {json.dumps(data[0], indent=2)[:500]}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(inspect_ea())
