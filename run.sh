#!/bin/bash
export GOOGLE_MAPS_API_KEY="AIzaSyA71540fEoWUBblV4Ts3ON1gw1n-KOtFo8"
cd /Users/alexho/ClaudeCodeSpace/map-marker
python3 map_marker.py --title "台北餐酒咖啡地圖" --file places.txt --serve
