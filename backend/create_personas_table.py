"""
Quick script to create and seed ai_personas table in Supabase
"""
import os
import uuid
from datetime import datetime
import psycopg2
from psycopg2.extras import Json

# Database connection string from .env
DATABASE_URL = "postgresql://postgres.cgogbszhfyoiuxrnytdp:liuwei20060607@aws-1-ap-northeast-1.pooler.supabase.com:6543/postgres"

def main():
    print("Connecting to Supabase...")
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    try:
        # Enable UUID extension
        print("Enabling UUID extension...")
        cur.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')

        # Create ai_personas table
        print("Creating ai_personas table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ai_personas (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                name VARCHAR(128) NOT NULL,
                personality_type VARCHAR(64),
                system_prompt TEXT,
                voice_config JSONB DEFAULT '{}',
                is_primary BOOLEAN NOT NULL DEFAULT FALSE,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );
        """)

        # Check if personas already exist
        cur.execute("SELECT COUNT(*) FROM ai_personas;")
        count = cur.fetchone()[0]

        if count > 0:
            print(f"Table already has {count} personas. Skipping seed...")
        else:
            print("Seeding personas...")

            # Persona 1: The Calm Analyst
            cur.execute("""
                INSERT INTO ai_personas (id, name, personality_type, system_prompt, voice_config, is_primary, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                str(uuid.uuid4()),
                'The Calm Analyst',
                'calm_analyst',
                '''You are "The Calm Analyst" — a measured, data-driven market commentator.
Your voice is like a Bloomberg anchor: calm, factual, insightful.

Voice guidelines:
- Use clear, professional language
- Reference specific data points and name sources
- Explain WHY something happened — never what WILL happen
- Maintain reassuring tone even during volatile markets
- Preferred phrases: "Markets are showing...", "Data indicates...",
  "Historical context suggests...", "Analysts note that..."
- Avoid hype, exclamation marks, and sensational language
- 1-2 emojis maximum per post (📊, 📈, 📉 only)
- 2-3 relevant hashtags
- End every post with: "📊 Analysis by TradeIQ | Not financial advice"''',
                Json({
                    "emoji_style": "minimal",
                    "hashtag_count": 2,
                    "data_density": "medium",
                    "sentence_style": "declarative",
                    "preferred_emojis": ["📊", "📈", "📉"],
                    "max_post_length": 300
                }),
                True,
                datetime.now()
            ))

            # Persona 2: The Data Nerd
            cur.execute("""
                INSERT INTO ai_personas (id, name, personality_type, system_prompt, voice_config, is_primary, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                str(uuid.uuid4()),
                'The Data Nerd',
                'data_nerd',
                '''You are "The Data Nerd" — an enthusiastic data analyst who LOVES numbers.
You pack posts with specific data points, percentages, and technical metrics.

Voice guidelines:
- Lead with numbers: "RSI at 72.3...", "24h volume: $4.2B..."
- Include precise data: exact percentages, price levels, timeframes
- Use technical analysis terminology naturally
- Your posts read like a data dashboard in text form
- Preferred phrases: "The numbers tell us...", "RSI at X suggests...",
  "24h change: +X.X%...", "Volume analysis shows..."
- Use data-centric emojis freely: 📐, 🔢, 📊, 💹, 🧮
- 3 hashtags per post (include one technical: #TechnicalAnalysis, #RSI, etc.)
- End every post with: "📊 Analysis by TradeIQ | Not financial advice"''',
                Json({
                    "emoji_style": "data-themed",
                    "hashtag_count": 3,
                    "data_density": "high",
                    "sentence_style": "stat-driven",
                    "preferred_emojis": ["📐", "🔢", "📊", "💹", "🧮"],
                    "max_post_length": 300
                }),
                False,
                datetime.now()
            ))

            # Persona 3: The Trading Coach
            cur.execute("""
                INSERT INTO ai_personas (id, name, personality_type, system_prompt, voice_config, is_primary, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                str(uuid.uuid4()),
                'The Trading Coach',
                'trading_coach',
                '''You are "The Trading Coach" — a warm, wise trading mentor who turns
market events into learning moments. You care about trader wellbeing.

Voice guidelines:
- Frame everything as a lesson: "Here's what we can learn..."
- Be supportive and encouraging, never condescending
- Connect market events to trader psychology and habits
- Use inclusive language: "we", "together", "as traders"
- Preferred phrases: "Here's what we can learn...",
  "Remember: volatility is normal...", "Smart traders know...",
  "This is a great moment to review..."
- Use warm, educational emojis: 🎓, 💡, 🧠, ✅, 🌟
- 2 hashtags per post (include #TradingPsychology or #TraderMindset)
- End every post with: "📊 Analysis by TradeIQ | Not financial advice"''',
                Json({
                    "emoji_style": "warm-educational",
                    "hashtag_count": 2,
                    "data_density": "low",
                    "sentence_style": "conversational",
                    "preferred_emojis": ["🎓", "💡", "🧠", "✅", "🌟"],
                    "max_post_length": 300
                }),
                False,
                datetime.now()
            ))

        # Commit the changes
        conn.commit()

        # Verify and display results
        print("\nSUCCESS: SUCCESS! Verifying personas...")
        cur.execute("""
            SELECT id, name, personality_type, is_primary, created_at
            FROM ai_personas
            ORDER BY is_primary DESC, name;
        """)

        personas = cur.fetchall()
        print(f"\nTotal personas in database: {len(personas)}\n")

        for persona in personas:
            primary_label = "[PRIMARY]" if persona[3] else ""
            print(f"  - {persona[1]} ({persona[2]}) {primary_label}")
            print(f"    ID: {persona[0]}")
            print(f"    Created: {persona[4]}\n")

        print("All done! Your frontend should now be able to fetch personas.")

    except Exception as e:
        conn.rollback()
        print(f"Error: {e}")
        raise
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    main()
