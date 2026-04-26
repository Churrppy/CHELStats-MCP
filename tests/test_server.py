import pytest
import respx
import httpx
from server import search_chel_club, get_chel_club_stats, get_chel_club_player_stats, get_chel_player_stats, analyze_player_performance

BASE_URL = "https://proclubs.ea.com/api/nhl"
VALID_KEY = "default_secret_key_change_me"

@pytest.mark.asyncio
@respx.mock
async def test_analyze_player_performance_success():
    mock_response = {
        "members": [
            {
                "name": "Player1",
                "gamesplayed": "10",
                "goals": "15",
                "assists": "5",
                "points": "20",
                "hits": "45",
                "bs": "5",
                "pim": "2",
                "shots": "30",
                "plusmin": "10"
            }
        ]
    }
    respx.get(f"{BASE_URL}/members/stats").mock(return_value=httpx.Response(200, json=mock_response))
    
    result = await analyze_player_performance("Player1", "12345", VALID_KEY, "common-gen5")
    assert result["player_name"] == "Player1"
    assert result["archetype"] == "Enforcer / Heavy Hitter"

@pytest.mark.asyncio
@respx.mock
async def test_search_chel_club_success():
    mock_response = {"12345": {"clubId": "12345", "name": "The Great Team", "record": "10-0-0"}}
    respx.get(f"{BASE_URL}/clubs/search").mock(return_value=httpx.Response(200, json=mock_response))
    
    result = await search_chel_club("The Great Team", VALID_KEY, "common-gen5")
    assert isinstance(result, list)
    assert result[0]["clubId"] == "12345"

@pytest.mark.asyncio
@respx.mock
async def test_unauthorized_access():
    result = await search_chel_club("Any Team", "wrong_key", "common-gen5")
    assert "error" in result[0]
    assert result[0]["error"] == "Unauthorized"

@pytest.mark.asyncio
@respx.mock
async def test_get_chel_club_stats_success():
    mock_response = {"wins": 10, "losses": 5}
    respx.get(f"{BASE_URL}/clubs/stats").mock(return_value=httpx.Response(200, json=mock_response))
    
    result = await get_chel_club_stats("12345", VALID_KEY, "common-gen5")
    assert result == mock_response

@pytest.mark.asyncio
@respx.mock
async def test_get_chel_club_player_stats_success():
    mock_response = {"members": [{"name": "Player1", "goals": 10}]}
    respx.get(f"{BASE_URL}/members/stats").mock(return_value=httpx.Response(200, json=mock_response))
    
    result = await get_chel_club_player_stats("12345", VALID_KEY, "common-gen5")
    assert result[0]["name"] == "Player1"

@pytest.mark.asyncio
@respx.mock
async def test_api_error_handling():
    respx.get(f"{BASE_URL}/clubs/stats").mock(return_value=httpx.Response(500, text="Internal Error"))
    
    result = await get_chel_club_stats("12345", VALID_KEY, "common-gen5")
    assert "error" in result
