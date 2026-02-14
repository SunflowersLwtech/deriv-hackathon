# Supabase Setup Instructions

## Quick Setup: Create AI Personas Table

### Option 1: Using Supabase SQL Editor (Recommended)

1. **Open Supabase SQL Editor:**
   - Go to: https://cgogbszhfyoiuxrnytdp.supabase.co
   - Navigate to: **SQL Editor** (left sidebar)

2. **Run the Setup Script:**
   - Click **"New Query"**
   - Copy the entire contents of `setup_personas_supabase.sql`
   - Paste into the SQL editor
   - Click **"Run"** or press `Ctrl+Enter`

3. **Verify Success:**
   - You should see a table with 3 rows showing:
     - The Calm Analyst (primary)
     - The Data Nerd
     - The Trading Coach

### Option 2: Using PostgreSQL Client

```bash
# Connect to Supabase PostgreSQL
psql "postgresql://postgres.cgogbszhfyoiuxrnytdp:liuwei20060607@aws-1-ap-northeast-1.pooler.supabase.com:6543/postgres"

# Run the setup script
\i backend/setup_personas_supabase.sql
```

## What This Creates

### Table: `ai_personas`

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key (auto-generated) |
| name | VARCHAR(128) | Persona display name |
| personality_type | VARCHAR(64) | Unique identifier (calm_analyst, data_nerd, trading_coach) |
| system_prompt | TEXT | AI behavior instructions |
| voice_config | JSONB | Configuration (emojis, hashtags, style) |
| is_primary | BOOLEAN | Whether this is the default persona |
| created_at | TIMESTAMPTZ | Creation timestamp |

### Initial Data (3 Personas)

1. **The Calm Analyst** (Primary)
   - Measured, data-driven market commentator
   - Bloomberg anchor style: calm, factual, insightful

2. **The Data Nerd**
   - Enthusiastic analyst who loves numbers
   - Packed with stats, percentages, technical metrics

3. **The Trading Coach**
   - Warm, supportive trading mentor
   - Focuses on psychology and learning moments

## Troubleshooting

### Error: "relation 'ai_personas' already exists"
- The table is already created! Just check if it has data:
```sql
SELECT COUNT(*) FROM ai_personas;
```
- If count is 0, run just the INSERT statements from the script

### Error: "permission denied"
- Make sure you're using the correct database credentials
- Check that you're connected to the right Supabase project

### Frontend Still Shows "No personas found"
1. Verify data exists in Supabase:
```sql
SELECT * FROM ai_personas;
```

2. Check that your frontend is using the correct Supabase URL/keys from `.env`:
```
NEXT_PUBLIC_SUPABASE_URL=https://cgogbszhfyoiuxrnytdp.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=<your-anon-key>
```

3. Restart your frontend development server:
```bash
cd frontend
npm run dev
```

## Complete Database Schema

To set up ALL TradeIQ tables (users, trades, behavioral_metrics, social_posts, etc.):
- Run the complete schema: `backend/supabase_schema.sql`

## Need Help?

Check the main project documentation or open an issue on GitHub.
