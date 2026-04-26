# CHELStats-MCP

An MCP server that provides player and club statistics for EA Sports NHL CHEL (EASHL) by querying EA's Pro Clubs API. This server is optimized for remote deployment and includes support for Streamable HTTP transport and API key authentication.

## Features

- **Club Search**: Find matching clubs with sorted prioritization for exact matches.
- **Club Statistics**: Retrieve overall team performance, records, and statistics.
- **Member Statistics**: Get detailed stats for all players within a specific club.
- **Player Search**: Filter and retrieve statistics for a specific player by their name.
- **Advanced Analysis**: Calculate advanced performance metrics and assign player archetypes.
- **Secure**: Built-in API key authentication and DNS rebinding protection.
- **Remote Ready**: Built-in CORS and Trusted Host support for proxied deployments.

## Supported Platforms

- `common-gen5`: PlayStation 5, Xbox Series X|S
- `common-gen4`: PlayStation 4, Xbox One

---

## 1. Server Setup (Debian/Ubuntu)

### Prerequisites
- Python 3.10 or higher
- Nginx (if proxying)

### Installation
1. Clone or SCP the project to your server:
   ```bash
   cd /opt/CHELStats-MCP
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install "mcp[cli]" httpx uvicorn pytest pytest-asyncio respx fastapi python-dotenv
   ```

3. Configure your API Key:
   Create a `.env` file in the project root:
   ```bash
   echo "CHELSTATS_API_KEY=your_secret_key_here" > .env
   ```

### Set Up Systemd Service
Create a service file to keep the server running in the background:
`sudo nano /etc/systemd/system/chelstats.service`

Paste the following configuration:
```ini
[Unit]
Description=CHELStats MCP SSE Server
After=network.target

[Service]
User=bastion
WorkingDirectory=/opt/CHELStats-MCP
Environment="PYTHONPATH=/opt/CHELStats-MCP"
# Optional: Override .env key here
# Environment="CHELSTATS_API_KEY=your_secret_key_here"
ExecStart=/opt/CHELStats-MCP/.venv/bin/python3 /opt/CHELStats-MCP/server.py
Restart=always

[Install]
WantedBy=multi-user.target
```

**Start the service:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable chelstats
sudo systemctl start chelstats
```

---

## 2. Nginx Configuration (Subpath Proxy)

To make your MCP server accessible through your existing site (e.g., `roguesecurity.ca/mcp/`), add the following to your site's Nginx configuration file:

```nginx
server {
    ...
    server_name yourdomain.com;

    # CHELStats MCP Proxy
    location /mcp/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_http_version 1.1;
        
        # Required for Streamable HTTP / SSE
        proxy_set_header Connection '';
        chunked_transfer_encoding off;
        proxy_buffering off;
        proxy_cache off;

        # Standard Proxy Headers
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

**Reload Nginx:**
```bash
sudo nginx -t && sudo systemctl restart nginx
```

---

## 3. Remote Connection

### Using MCP Inspector
You can connect to your remote server using the official Inspector. Use the base proxy path:

**URL:** `https://yourdomain.com/mcp/`

### Local Claude Desktop Config
Add this to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "chelstats": {
      "url": "https://yourdomain.com/mcp/",
      "env": {
        "CHELSTATS_API_KEY": "your_secret_key_here"
      }
    }
  }
}
```

---

## Tools Provided

- `search_chel_club(club_name, api_key, platform)`
- `get_chel_club_stats(club_id, api_key, platform)`
- `get_chel_club_player_stats(club_id, api_key, platform)`
- `get_chel_player_stats(player_name, club_id, api_key, platform)`
- `analyze_player_performance(player_name, club_id, api_key, platform)`

## Disclaimer

This project uses an undocumented internal API from EA Sports. Endpoints and data structures are subject to change. Not affiliated with Electronic Arts.
