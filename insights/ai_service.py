from groq import Groq
import os
import json

client = Groq(api_key=os.getenv('GROQ_API_KEY'))


def generate_insight(game_name, kills, deaths, assists, wins, matches_played, kd_ratio, win_rate):
    prompt = f"""
    You are a professional gaming coach for {game_name}. Analyze the following player stats and give 3 specific, actionable tips to help them improve. Be direct and encouraging.

    Player Stats:
    - Kills: {kills}
    - Deaths: {deaths}
    - Assists: {assists}
    - Wins: {wins}
    - Matches Played: {matches_played}
    - KD Ratio: {kd_ratio}
    - Win Rate: {win_rate}%

    Return only the 3 tips as plain text, numbered 1 to 3. No extra commentary.
    """

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5,
    )

    return response.choices[0].message.content.strip()


def generate_elite_insights(game_name, kills, deaths, assists, wins, matches_played, kd_ratio, win_rate):
    prompt = f"""
    You are an elite gaming analyst for {game_name}. Analyze the following player stats and generate five advanced analytical reports. Be specific, data-driven and direct. Use the actual numbers provided.

    Player Stats:
    - Kills: {kills}
    - Deaths: {deaths}
    - Assists: {assists}
    - Wins: {wins}
    - Matches Played: {matches_played}
    - KD Ratio: {kd_ratio}
    - Win Rate: {win_rate}%

    Generate exactly this JSON structure with no extra text:
    {{
        "performance_volatility": {{
            "title": "Performance Volatility",
            "rating": "Streaky|Consistent|Reliable",
            "analysis": "2-3 sentence analysis of consistency based on KD vs win rate gap"
        }},
        "skill_gap": {{
            "title": "Skill Gap Analysis",
            "percentile": "estimated percentile 1-100 based on stats",
            "analysis": "2-3 sentences comparing to Nigerian top players and what specific skills to close the gap"
        }},
        "clutch_factor": {{
            "title": "Clutch Factor",
            "score": "score out of 10",
            "analysis": "2-3 sentences on high pressure performance based on win rate vs KD ratio relationship"
        }},
        "weapon_efficiency": {{
            "title": "Loadout Efficiency",
            "rating": "Low|Medium|High|Elite",
            "analysis": "2-3 sentences on efficiency of kills per match and what weapon style to adopt"
        }},
        "growth_projection": {{
            "title": "AI Growth Projection",
            "projected_rank": "estimated rank tier in 30 days if player improves consistently",
            "analysis": "2-3 sentences on projected improvement trajectory and what to focus on"
        }}
    }}

    Return JSON only, no markdown, no extra text.
    """

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4,
    )

    result = response.choices[0].message.content.strip()
    if result.startswith("```"):
        result = result.split("```")[1]
        if result.startswith("json"):
            result = result[4:]

    return json.loads(result.strip())


def generate_efootball_elite_insights(wins, draws, losses, matches_played, win_rate,
                                       gk_type, cb1_type, cb2_type, cdm_type,
                                       lw_type, rw_type, st_type):
    """eFootball has no kills/deaths, so Elite analysis here is built around
    match outcomes plus squad pack-player-type synergy (the core differentiator
    for defensive solidity and tactical balance in eFootball)."""

    squad_list = f"""
    - GK: {gk_type}
    - CB: {cb1_type}
    - CB: {cb2_type}
    - CDM: {cdm_type}
    - LW: {lw_type}
    - RW: {rw_type}
    - ST: {st_type}
    """

    prompt = f"""
    You are an elite eFootball tactical analyst. Analyze this player's match record and squad pack-player-type composition, then generate five advanced reports. Be specific and direct. Use the actual data provided.

    Match Record:
    - Wins: {wins}
    - Draws: {draws}
    - Losses: {losses}
    - Matches Played: {matches_played}
    - Win Rate: {win_rate}%

    Squad Pack Player Types (by position):
    {squad_list}

    Key tactical knowledge to apply:
    - Two "Destroyer" type players in the defensive line (CB/CB/CDM) both aggressively step out of position to tackle, leaving gaps behind the defense at the same time. This is a common and costly pairing mistake.
    - "Anchor Man" and "Extra Frame" types hold position and are strong pairing partners with a Destroyer, since one covers depth while the other presses.
    - Pairing two "Extra Frame" (aerial-focused, positionally disciplined) players together in defense is safe but can be passive and slow to press.
    - "Catalyst" and "Deep-Lying Playmaker" at CDM support buildup play but offer little defensive cover if both CBs are aggressive types too.
    - Wide attackers ("Prolific Winger", "Speedster", "The Incisive Run") pair well when one favors cutting inside and the other stays wide, for width and unpredictability together.
    - A "Target Man" or "Goal Poacher" striker benefits from at least one winger with strong crossing ("Cross Specialist") to supply chances.

    Generate exactly this JSON structure with no extra text:
    {{
        "performance_volatility": {{
            "title": "Performance Volatility",
            "rating": "Streaky|Consistent|Reliable",
            "analysis": "2-3 sentences on consistency based on the ratio of draws to decisive results"
        }},
        "skill_gap": {{
            "title": "Skill Gap Analysis",
            "percentile": "estimated percentile 1-100 based on win rate and match count",
            "analysis": "2-3 sentences comparing to Nigerian top eFootball players and what to work on"
        }},
        "squad_synergy": {{
            "title": "Squad Synergy",
            "rating": "Poor|Average|Good|Elite",
            "analysis": "2-3 sentences identifying any specific pairing conflicts in the listed squad (name the positions and player types involved) and a concrete swap recommendation to fix it. If the squad is well paired, explain exactly why it works."
        }},
        "tactical_efficiency": {{
            "title": "Tactical Efficiency",
            "rating": "Low|Medium|High|Elite",
            "analysis": "2-3 sentences on how well the squad shape supports the win rate, and one tactical adjustment to try"
        }},
        "growth_projection": {{
            "title": "AI Growth Projection",
            "projected_rank": "estimated division/rank tier in 30 days if squad synergy issues are fixed",
            "analysis": "2-3 sentences on projected improvement trajectory and what to focus on first"
        }}
    }}

    Return JSON only, no markdown, no extra text.
    """

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4,
    )

    result = response.choices[0].message.content.strip()
    if result.startswith("```"):
        result = result.split("```")[1]
        if result.startswith("json"):
            result = result[4:]

    return json.loads(result.strip())