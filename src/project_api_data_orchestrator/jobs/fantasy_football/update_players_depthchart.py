import requests
from bs4 import BeautifulSoup
import time
import pandas as pd
import re

from project_api_data_orchestrator.db.connection import get_connection


## Scrape Depth Chart Config
BASE_URL = "https://www.ourlads.com"
DEPTHCHARTS_INDEX = BASE_URL + "/nfldepthcharts/depthcharts.aspx"
TARGET_POS = {"QB", "WR", "RB", "TE", "LWR", "RWR", "SWR"} # Target positions (including variants for WR)

# === DB FUNC CONFIG ===
SEASON_ID = 1
DELETE_MISSING_PLAYERS = True  # set to False if you only want to remove from player_seasons

# === Scrape Depth Chart Functions ===

def get_team_links():
    resp = requests.get(DEPTHCHARTS_INDEX, headers={"User-Agent": "Mozilla/5.0"})
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.startswith("/nfldepthcharts/depthchart/"):
            full = BASE_URL + href
            if full not in links:
                links.append(full)
    return links

def parse_team_depthchart(team_url):
    resp = requests.get(team_url, headers={"User-Agent": "Mozilla/5.0"})
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    # Derive team abbreviation
    team_abbrev = None
    depwrapper = soup.find("div", id="ctl00_phContent_DepWrapper")
    if depwrapper:
        for c in depwrapper.get("class", []):
            if c.startswith("dt-"):
                team_abbrev = c[3:]
                break
    if not team_abbrev:
        team_abbrev = team_url.rstrip("/").split("/")[-1].upper()

    records = []
    # Locate the table
    table = depwrapper.find("table", class_="table-bordered") if depwrapper else None
    if table is None:
        table = soup.find("table", class_="table-bordered")
    if table is None:
        return records

    tbody = table.find("tbody") or table.find("tbody", id="ctl00_phContent_dcTBody")
    if tbody is None:
        return records

    for tr in tbody.find_all("tr"):
        tds = tr.find_all("td")
        if len(tds) < 2:
            continue

        pos_raw = tds[0].get_text(strip=True)
        pos = pos_raw.strip()
        pos_norm = "WR" if pos in ("LWR", "RWR", "SWR") else pos

        if pos_norm not in TARGET_POS:
            continue

        tier = 1
        for num_idx in range(1, len(tds), 2):
            player_idx = num_idx + 1
            if player_idx >= len(tds):
                break
            a = tds[player_idx].find("a")
            if a and a.get_text(strip=True):
                player_text = a.get_text(strip=True)
                player_text = re.sub(
                    r"\s+(?:[A-Z]{2}\d{2}|\d{2}/\d|[A-Z]{1,2}/[A-Za-z]{2,3})$",
                    "",
                    player_text,
                    flags=re.IGNORECASE,
                )
                player_clean = player_text.title().strip()
                records.append((player_clean, team_abbrev, pos_norm, tier))
            tier += 1

    return records

def scrape_all_to_dataframe():
    team_links = get_team_links()
    print(f"Found {len(team_links)} team pages.")
    all_records = []
    for link in team_links:
        try:
            recs = parse_team_depthchart(link)
            all_records.extend(recs)
        except Exception as e:
            print(f"Error parsing {link}: {e}")
        time.sleep(1)

    # Deduplicate
    seen = set()
    deduped = []
    for rec in all_records:
        if rec not in seen:
            seen.add(rec)
            deduped.append(rec)

    df = pd.DataFrame(deduped, columns=["Player", "Team", "Position", "Tier"])
    print(f"Scraped {len(df)} unique player-position records.")
    return df

# === DB Helper functions ===

def get_team_id(team_code, cur):
    cur.execute("SELECT team_id FROM public.teams WHERE abbreviation = %s", (team_code,))
    res = cur.fetchone()
    if res:
        return res[0]

def get_or_create_player(player_name, position, team_code, cur, conn):
    team_id = get_team_id(team_code, cur)
    cur.execute("""
        SELECT player_id FROM public.players 
        WHERE player_name = %s AND team_id = %s
    """, (player_name, team_id))
    res = cur.fetchone()
    if res:
        return res[0]
    cur.execute("""
        INSERT INTO public.players (player_name, position, team_id)
        VALUES (%s, %s, %s)
        RETURNING player_id
    """, (player_name, position, team_id))
    player_id = cur.fetchone()[0]
    conn.commit()
    return player_id

def upsert_player_season(player_id, season_id, tier, cur, conn):
    cur.execute("""
        SELECT player_season_id FROM public.player_seasons
        WHERE player_id = %s AND season_id = %s
    """, (player_id, season_id))
    res = cur.fetchone()
    if res:
        cur.execute("""
            UPDATE public.player_seasons
            SET tier = %s
            WHERE player_season_id = %s
        """, (tier, res[0]))
    else:
        cur.execute("""
            INSERT INTO public.player_seasons (player_id, season_id, tier)
            VALUES (%s, %s, %s)
        """, (player_id, season_id, tier))
    conn.commit()

def run():
    conn = get_connection(DB_NAME='nfl_data')
    cur = conn.cursor()
    try:
        df_new = scrape_all_to_dataframe()

        # === Step 1: Insert or update new data ===
        new_player_ids = []
        for _, row in df_new.iterrows():
            player_name = row['Player']
            team_code = row['Team']
            position = row['Position']
            tier = row['Tier']

            player_id = get_or_create_player(player_name, position, team_code, cur, conn)
            upsert_player_season(player_id, SEASON_ID, tier, cur, conn)
            new_player_ids.append(player_id)

        print("Upserts complete")        

        # === Step 2: Remove players no longer in list ===
        cur.execute("SELECT player_id FROM public.player_seasons WHERE season_id = %s", (SEASON_ID,))
        existing_player_ids = [row[0] for row in cur.fetchall()]

        players_to_remove = list(set(existing_player_ids) - set(new_player_ids))

        if players_to_remove:
            print(f"Removing {len(players_to_remove)} players from player_seasons...")

            # Remove from player_seasons
            cur.execute("""
                DELETE FROM public.player_seasons
                WHERE season_id = %s AND player_id = ANY(%s)
            """, (SEASON_ID, players_to_remove))
            conn.commit()

            if DELETE_MISSING_PLAYERS:
                # Remove from players if no longer in any season
                cur.execute("""
                    DELETE FROM public.players
                    WHERE player_id IN (
                        SELECT p.player_id FROM public.players p
                        LEFT JOIN player_seasons ps ON ps.player_id = p.player_id
                        WHERE ps.player_id IS NULL
                    )
                """)
                conn.commit()
        else:
            print("No players to remove")

        print("Database synchronization complete")
       
        return {"status": "success", "message": "Players table updated"}
    except Exception as e:
        conn.rollback()
        return {"status": "error", "message": str(e)}
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    run()
