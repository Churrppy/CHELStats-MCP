import httpx
import logging
import os
import sys
from datetime import datetime
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from typing import Optional, List, Dict, Any

# Load environment variables from .env file if it exists
load_dotenv()

# Configure logging to file only to avoid interfering with MCP stdio protocol
LOG_DIR = "/home/bastion/CHELStats-MCP/logs"
os.makedirs(LOG_DIR, exist_ok=True)
log_file = os.path.join(LOG_DIR, f"chelstats_{datetime.now().strftime('%Y%m%d')}.log")

# API Key for authentication (set via CHELSTATS_API_KEY environment variable)
API_KEY = os.environ.get("CHELSTATS_API_KEY", "default_secret_key_change_me")

# Create a logger
logger = logging.getLogger("chelstats-mcp")
logger.setLevel(logging.INFO)

# File handler for persistent logs
file_handler = logging.FileHandler(log_file)
file_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
logger.addHandler(file_handler)

# Optionally add stderr handler for immediate feedback (stderr doesn't break MCP stdio transport)
stderr_handler = logging.StreamHandler(sys.stderr)
stderr_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
logger.addHandler(stderr_handler)

# Initialize FastMCP server with transport security settings to allow remote access
mcp = FastMCP(
    "CHELStats-MCP",
    streamable_http_path="/",
    transport_security=TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=["roguesecurity.ca", "*.roguesecurity.ca", "localhost", "127.0.0.1"]
    )
)

BASE_URL = "https://proclubs.ea.com/api/nhl"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.ea.com/games/nhl/nhl-25/pro-clubs/overview",
    "Origin": "https://www.ea.com",
    "DNT": "1",
    "Connection": "keep-alive",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-site",
}

def validate_api_key(key: str) -> bool:
    """Check if the provided API key is valid."""
    return key == API_KEY

async def fetch_ea_api(endpoint: str, params: Dict[str, Any]) -> Any:
    """Helper to fetch data from the EA Pro Clubs API."""
    logger.info(f"Fetching from EA API: {endpoint} with params: {params}")
    try:
        async with httpx.AsyncClient() as client:
            url = f"{BASE_URL}/{endpoint}"
            response = await client.get(url, params=params, headers=HEADERS, timeout=15.0)
            
            if response.status_code != 200:
                logger.error(f"EA API returned status {response.status_code}: {response.text[:200]}...")
                return {"error": f"EA API returned status {response.status_code}", "detail": response.text[:200]}
            
            data = response.json()
            # If this is members/stats, it returns {"members": [...], ...}
            if endpoint == "members/stats" and isinstance(data, dict) and "members" in data:
                return data["members"]
            
            return data
    except httpx.RequestError as e:
        logger.error(f"HTTP request error: {e}")
        return {"error": "HTTP request error", "detail": str(e)}
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        return {"error": "Unexpected error", "detail": str(e)}

@mcp.tool()
async def search_chel_club(club_name: str, api_key: str, platform: str = "common-gen5") -> List[Dict[str, Any]]:
    """
    Search for an EA Sports NHL CHEL club. Returns a list of matching clubs with their IDs and basic info.
    
    Args:
        club_name: The name of the club to search for.
        api_key: Your secret API key to access this server.
        platform: The platform (e.g., 'common-gen5' for PS5/Xbox Series X|S, 'common-gen4' for PS4/Xbox One).
    """
    if not validate_api_key(api_key):
        logger.warning(f"Unauthorized search attempt for club: {club_name}")
        return [{"error": "Unauthorized", "detail": "Invalid or missing API key."}]
        
    logger.info(f"Searching for club: {club_name} on {platform}")
    params = {
        "platform": platform,
        "clubName": club_name
    }
    raw_data = await fetch_ea_api("clubs/search", params)
    
    if not isinstance(raw_data, dict):
        return raw_data if isinstance(raw_data, list) else [raw_data]
        
    if "error" in raw_data:
        return [raw_data]
        
    clubs = []
    for club_id, info in raw_data.items():
        clubs.append({
            "clubId": club_id,
            "name": info.get("name"),
            "record": info.get("record"),
            "currentDivision": info.get("currentDivision"),
            "platform": platform
        })
    
    # Sort by exact name match first, then by record
    clubs.sort(key=lambda x: (x["name"].lower() != club_name.lower(), x["name"]))
    
    return clubs

@mcp.tool()
async def get_chel_club_stats(club_id: str, api_key: str, platform: str = "common-gen5") -> Dict[str, Any]:
    """
    Get overall team/club statistics for a specific CHEL club.
    
    Args:
        club_id: The unique numeric identifier for the club.
        api_key: Your secret API key to access this server.
        platform: The platform the club is on.
    """
    if not validate_api_key(api_key):
        return {"error": "Unauthorized", "detail": "Invalid or missing API key."}
        
    logger.info(f"Getting stats for club ID: {club_id} on {platform}")
    params = {
        "platform": platform,
        "clubId": club_id
    }
    return await fetch_ea_api("clubs/stats", params)

@mcp.tool()
async def get_chel_club_player_stats(club_id: str, api_key: str, platform: str = "common-gen5") -> Any:
    """
    Get detailed stats for all members in a specific CHEL club.
    
    Args:
        club_id: The unique numeric identifier for the club.
        api_key: Your secret API key to access this server.
        platform: The platform the club is on.
    """
    if not validate_api_key(api_key):
        return {"error": "Unauthorized", "detail": "Invalid or missing API key."}
        
    logger.info(f"Getting player stats for club ID: {club_id} on {platform}")
    params = {
        "platform": platform,
        "clubId": club_id
    }
    return await fetch_ea_api("members/stats", params)

@mcp.tool()
async def get_chel_player_stats(player_name: str, club_id: str, api_key: str, platform: str = "common-gen5") -> Any:
    """
    Get statistics for a specific player within a CHEL club.
    
    Args:
        player_name: The exact name (gamertag/PSN ID) of the player.
        club_id: The unique numeric identifier for the club they belong to.
        api_key: Your secret API key to access this server.
        platform: The platform the club is on.
    """
    if not validate_api_key(api_key):
        return {"error": "Unauthorized", "detail": "Invalid or missing API key."}
        
    logger.info(f"Getting stats for player: {player_name} in club: {club_id} on {platform}")
    params = {
        "platform": platform,
        "clubId": club_id
    }
    result = await fetch_ea_api("members/stats", params)
    
    if isinstance(result, dict) and "error" in result:
        return result

    # Filter for the specific player
    for member in result:
        if member.get("name", "").lower() == player_name.lower():
            logger.info(f"Found stats for player: {player_name}")
            return member
            
    logger.warning(f"Player {player_name} not found in club {club_id}")
    return {"error": f"Player {player_name} not found in club {club_id}"}

@mcp.tool()
async def analyze_player_performance(player_name: str, club_id: str, api_key: str, platform: str = "common-gen5") -> Dict[str, Any]:
    """
    Perform a detailed performance analysis on a specific player's statistics.
    Categorizes the player and calculates advanced metrics.
    
    Args:
        player_name: The exact name (gamertag/PSN ID) of the player.
        club_id: The unique numeric identifier for the club they belong to.
        api_key: Your secret API key to access this server.
        platform: The platform the club is on.
    """
    if not validate_api_key(api_key):
        return {"error": "Unauthorized", "detail": "Invalid or missing API key."}
        
    logger.info(f"Analyzing performance for player: {player_name} in club: {club_id}")
    stats = await get_chel_player_stats(player_name, club_id, api_key, platform)
    
    if isinstance(stats, dict) and "error" in stats:
        return stats
    
    try:
        gp = int(stats.get("gamesplayed", 0))
        if gp == 0:
            return {"player_name": player_name, "error": "No games played to analyze."}
            
        goals = int(stats.get("goals", 0))
        assists = int(stats.get("assists", 0))
        points = int(stats.get("points", 0))
        hits = int(stats.get("hits", 0))
        blocks = int(stats.get("bs", 0))
        pim = int(stats.get("pim", 0))
        shots = int(stats.get("shots", 0))
        plus_minus = int(stats.get("plusmin", 0))
        
        # Derived Metrics
        ppg = points / gp
        gpg = goals / gp
        apg = assists / gp
        hpg = hits / gp
        bpg = blocks / gp
        shot_pct = (goals / shots * 100) if shots > 0 else 0
        discipline = pim / gp
        
        # Archetype Logic
        if hpg > 4.0:
            archetype = "Enforcer / Heavy Hitter"
        elif gpg > 1.2:
            archetype = "Elite Sniper"
        elif apg > 1.5:
            archetype = "Elite Playmaker"
        elif ppg > 2.5:
            archetype = "Offensive Powerhouse"
        elif bpg > 1.5:
            archetype = "Defensive Specialist"
        elif hpg > 2.0 and ppg > 1.0:
            archetype = "Power Forward"
        else:
            archetype = "Two-Way Player"
            
        analysis = {
            "player_name": player_name,
            "archetype": archetype,
            "performance_rating": "Elite" if ppg > 2.0 else "High" if ppg > 1.0 else "Average",
            "advanced_metrics": {
                "points_per_game": round(ppg, 2),
                "goals_per_game": round(gpg, 2),
                "assists_per_game": round(apg, 2),
                "hits_per_game": round(hpg, 2),
                "blocks_per_game": round(bpg, 2),
                "shooting_efficiency": f"{round(shot_pct, 1)}%",
                "discipline_rating (PIM/GP)": round(discipline, 2),
                "plus_minus_per_game": round(plus_minus / gp, 2)
            },
            "description": f"{player_name} is classified as a {archetype}. With {round(ppg, 2)} PPG and {round(hpg, 2)} hits per game, they provide a {'significant' if ppg > 1.5 else 'steady'} contribution to the team's success."
        }
        
        return analysis
    except Exception as e:
        logger.error(f"Error during analysis: {e}")
        return {"error": "Failed to analyze player stats", "detail": str(e)}

if __name__ == "__main__":
    logger.info("Starting CHELStats-MCP server (Streamable HTTP)")
    
    # To support remote Inspector connections and proxying, we add middleware
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.middleware.trustedhost import TrustedHostMiddleware
    
    # Using Streamable HTTP app instead of SSE
    app = mcp.streamable_http_app()
    
    app.add_middleware(
        TrustedHostMiddleware, 
        allowed_hosts=["roguesecurity.ca", "*.roguesecurity.ca", "localhost", "127.0.0.1"]
    )
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, proxy_headers=True, forwarded_allow_ips="*")
