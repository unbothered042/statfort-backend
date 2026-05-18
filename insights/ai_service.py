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
        model="llama-3.3-70b-versatile",
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
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4,
    )

    result = response.choices[0].message.content.strip()
    if result.startswith("```"):
        result = result.split("```")[1]
        if result.startswith("json"):
            result = result[4:]

    return json.loads(result.strip())