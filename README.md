# radarrtrim

## Description
A python script written to help automate removal of watched movies from both Radarr and Plex

## Installation

### Requirements
Simply install the requirements from the `requirements.txt` file using the following command:
```
python3 -m pip install -r requirements.txt
```

### Config
Ensure your configuration file is filled out:
- plex:
  - base_url: your plex.direct url
  - token: your plex auth token. See [this article](https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/)
- radarr:
  - api_key: your radarr api key
  - api_path: /api/v3
  - ip: 192.168.1.1
  - port: 7878

### systemd (optional)
If you want to run this on a daily schedule, you'll need to:
1. Edit `radarrtrim.service` in the `systemd` directory and change `ExecStart` to point to the location of the script and the `User` and `Group` to the user and group you want to run the script with.
2. Copy the `radarrtrim.timer` and `radarrtrim.service` files from the `systemd` directory to `/etc/systemd/system/`
3. Reload the systemd daemons with:
   ```
   sudo systemctl daemon-reload
   ```
4. Enable the service:
   ```
   sudo systemctl enable radarrtrim
   ```
5. Run the service:
   ```
   sudo systemctl start radarrtrim
   ```

## Usage
Run it with the following command:
```
python3 run.py
```
