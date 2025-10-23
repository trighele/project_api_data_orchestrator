from project_api_data_orchestrator.db.connection import get_connection
import time

def run():
    conn = get_connection(DB_NAME='nfl_data')
    cursor = conn.cursor()
    try:
        # cursor.execute("UPDATE players SET stats_last_updated = NOW();")  # Example
        cursor.execute(
            """
            SELECT
            p.player_name,
            p.position,
            t.abbreviation,
            ps.tier
            FROM public.players p
            LEFT JOIN public.teams t ON p.team_id = t.team_id
            LEFT JOIN public.player_seasons ps ON ps.player_id = p.player_id
            LEFT JOIN public.seasons s ON ps.season_id = s.season_id
            LIMIT 10;
            """
        )
        conn.commit()
        time.sleep(15)
        return {"status": "success", "message": "Player stats updated"}
    except Exception as e:
        conn.rollback()
        return {"status": "error", "message": str(e)}
    finally:
        cursor.close()
        conn.close()