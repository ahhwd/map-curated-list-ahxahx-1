#!/usr/bin/env python3
"""
地點標記地圖產生器

用法：
  python3 map_marker.py --title "地圖標題" --file places.txt
  python3 map_marker.py --title "地圖標題" "地點1" "地點2" "地點3"
  python3 map_marker.py "地點1" "地點2" "地點3"
"""

import sys
import json
import os
import argparse
import webbrowser
import threading
import signal
import requests
from http.server import HTTPServer, SimpleHTTPRequestHandler

API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY", "")


def search_place(query, api_key):
    """用 Google Places API Text Search 查詢地點"""
    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    params = {
        "query": query,
        "key": api_key,
    }
    resp = requests.get(url, params=params)
    data = resp.json()

    if data.get("status") != "OK" or not data.get("results"):
        print(f"  ✗ 找不到：{query}（{data.get('status', 'UNKNOWN')}）")
        return None

    result = data["results"][0]
    place = {
        "name": result["name"],
        "query": query,
        "address": result.get("formatted_address", ""),
        "lat": result["geometry"]["location"]["lat"],
        "lng": result["geometry"]["location"]["lng"],
        "place_id": result["place_id"],
    }
    print(f"  ✓ {query} → {place['name']}（{place['address']}）")
    return place


def generate_html(places, api_key, title="地點標記地圖"):
    """生成包含所有標記的 Google Maps HTML"""
    places_json = json.dumps(places, ensure_ascii=False)
    title_json = json.dumps(title, ensure_ascii=False)

    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }}
        #container {{ display: flex; height: 100vh; }}
        #sidebar {{
            width: 320px;
            overflow-y: auto;
            background: #fff;
            border-right: 1px solid #e0e0e0;
            flex-shrink: 0;
        }}
        #sidebar h2 {{
            padding: 16px;
            font-size: 18px;
            border-bottom: 1px solid #e0e0e0;
            position: sticky;
            top: 0;
            background: #fff;
            z-index: 1;
        }}
        .place-item {{
            display: flex;
            align-items: flex-start;
            gap: 12px;
            padding: 12px 16px;
            border-bottom: 1px solid #f0f0f0;
            cursor: pointer;
            transition: background 0.15s;
        }}
        .place-item:hover {{ background: #f5f5f5; }}
        .place-number {{
            background: #ea4335;
            color: white;
            width: 24px;
            height: 24px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 12px;
            font-weight: bold;
            flex-shrink: 0;
            margin-top: 2px;
        }}
        .place-name {{ font-weight: 600; font-size: 14px; }}
        .place-address {{ font-size: 12px; color: #666; margin-top: 2px; }}
        #map {{ flex: 1; height: 100%; }}
        @media (max-width: 768px) {{
            #container {{ flex-direction: column; }}
            #sidebar {{ width: 100%; height: 200px; order: 2; }}
            #map {{ order: 1; }}
        }}
    </style>
</head>
<body>
    <div id="container">
        <div id="sidebar">
            <h2 id="sidebar-title"></h2>
            <div id="sidebar-list"></div>
        </div>
        <div id="map"></div>
    </div>
    <script>
        var PLACES = {places_json};
        var TITLE = {title_json};

        function initMap() {{
            var map = new google.maps.Map(document.getElementById('map'), {{
                zoom: 13,
                mapTypeControl: true,
                streetViewControl: false,
            }});
            var bounds = new google.maps.LatLngBounds();
            var markers = [];
            var infoWindows = [];

            PLACES.forEach(function(p, i) {{
                var marker = new google.maps.Marker({{
                    position: {{ lat: p.lat, lng: p.lng }},
                    map: map,
                    title: p.name,
                    label: {{ text: String(i + 1), color: "white", fontWeight: "bold" }}
                }});

                var infoContent = document.createElement('div');
                infoContent.style.fontSize = '14px';
                var strong = document.createElement('strong');
                strong.textContent = (i + 1) + '. ' + p.name;
                infoContent.appendChild(strong);
                infoContent.appendChild(document.createElement('br'));
                infoContent.appendChild(document.createTextNode(p.address));
                infoContent.appendChild(document.createElement('br'));
                var link = document.createElement('a');
                link.href = 'https://www.google.com/maps/place/?q=place_id:' + p.place_id;
                link.target = '_blank';
                link.textContent = '在 Google Maps 開啟';
                infoContent.appendChild(link);

                var infoWindow = new google.maps.InfoWindow({{ content: infoContent }});

                marker.addListener('click', function() {{
                    infoWindows.forEach(function(iw) {{ iw.close(); }});
                    infoWindow.open(map, marker);
                }});

                markers.push(marker);
                infoWindows.push(infoWindow);
                bounds.extend(marker.getPosition());
            }});

            map.fitBounds(bounds, {{ padding: 50 }});

            // Build sidebar
            document.getElementById('sidebar-title').textContent = TITLE + ' (' + PLACES.length + ')';
            var list = document.getElementById('sidebar-list');
            PLACES.forEach(function(p, i) {{
                var item = document.createElement('div');
                item.className = 'place-item';
                item.onclick = function() {{
                    google.maps.event.trigger(markers[i], 'click');
                    map.panTo(markers[i].getPosition());
                }};
                var num = document.createElement('span');
                num.className = 'place-number';
                num.textContent = i + 1;
                var info = document.createElement('div');
                var name = document.createElement('div');
                name.className = 'place-name';
                name.textContent = p.name;
                var addr = document.createElement('div');
                addr.className = 'place-address';
                addr.textContent = p.address;
                info.appendChild(name);
                info.appendChild(addr);
                item.appendChild(num);
                item.appendChild(info);
                list.appendChild(item);
            }});
        }}
    </script>
    <script async defer src="https://maps.googleapis.com/maps/api/js?key={api_key}&callback=initMap"></script>
</body>
</html>"""
    return html


def main():
    parser = argparse.ArgumentParser(description="地點標記地圖產生器")
    parser.add_argument("places", nargs="*", help="地點名稱")
    parser.add_argument("--title", "-t", default="地點標記地圖", help="地圖標題")
    parser.add_argument("--file", "-f", help="從文字檔讀取地點（一行一個）")
    parser.add_argument("--output", "-o", default="index.html", help="輸出檔名（預設 index.html）")
    parser.add_argument("--serve", "-s", action="store_true", help="生成後啟動本地伺服器預覽")
    args = parser.parse_args()

    api_key = API_KEY
    if not api_key:
        print("錯誤：請設定環境變數 GOOGLE_MAPS_API_KEY")
        print("  export GOOGLE_MAPS_API_KEY='你的API金鑰'")
        sys.exit(1)

    # 收集地點清單
    queries = list(args.places)
    if args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    queries.append(line)

    if not queries:
        print("錯誤：請提供地點名稱（直接輸入或用 --file 指定檔案）")
        parser.print_help()
        sys.exit(1)

    print(f"\n🔍 查詢 {len(queries)} 個地點...\n")

    places = []
    for q in queries:
        place = search_place(q, api_key)
        if place:
            places.append(place)

    if not places:
        print("\n沒有找到任何地點。")
        sys.exit(1)

    print(f"\n✅ 找到 {len(places)}/{len(queries)} 個地點，正在生成地圖...\n")

    html = generate_html(places, api_key, args.title)

    output_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(output_dir, args.output)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"📄 地圖已儲存：{output_path}")

    if args.serve:
        port = 8397
        os.chdir(output_dir)

        import subprocess
        subprocess.run(
            f"lsof -ti:{port} | xargs kill -9",
            shell=True, capture_output=True,
        )

        server = HTTPServer(("localhost", port), SimpleHTTPRequestHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()

        url = f"http://localhost:{port}/{args.output}"
        webbrowser.open(url)
        print(f"🌐 已在瀏覽器開啟：{url}")
        print("按 Ctrl+C 結束伺服器...")

        try:
            signal.pause()
        except KeyboardInterrupt:
            print("\n伺服器已停止。")
            server.shutdown()
    else:
        print("💡 加上 --serve 可啟動本地預覽")


if __name__ == "__main__":
    main()
