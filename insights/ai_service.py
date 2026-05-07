from groq import Groq
import os
from django.conf import settings

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