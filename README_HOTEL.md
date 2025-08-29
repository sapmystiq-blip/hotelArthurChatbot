# Hotel Arthur Demo (using your Bakery Flask skeleton)

## Files you’ll add
- `hotel_knowledge_arthur.json`
- `PROMPT.md`
- `app_hotel.py` (non-destructive: your original `app.py` remains)
- `index_hotel.html`
- `.env.example`

## How to run locally
```bash
pip install -r requirements.txt
cp .env.example .env
# add your OPENAI_API_KEY to .env
python app_hotel.py
# open http://localhost:5001/
```

## Railway
- Set env vars from `.env.example` (especially `OPENAI_API_KEY`).
- Use `python app_hotel.py` or a Procfile entry like:
  `web: gunicorn app_hotel:app --preload --workers=2 --threads=4 --timeout=120`
