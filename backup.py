"""Automated database backup script.
Run via Windows Task Scheduler every 30 minutes or as needed.
Usage:  python backup.py
"""
import os, shutil
from datetime import datetime

BASE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE, 'data', 'supplypulse.db')
BACKUP_DIR = os.path.join(BASE, 'backups')

os.makedirs(BACKUP_DIR, exist_ok=True)

if not os.path.exists(DB_PATH):
    print(f'[ERROR] Database not found: {DB_PATH}')
    exit(1)

ts = datetime.now().strftime('%Y%m%d_%H%M%S')
dest = os.path.join(BACKUP_DIR, f'supplypulse_{ts}.db')
shutil.copy2(DB_PATH, dest)

# Keep only the 48 most recent backups (~24 hours at 30min intervals)
all_backups = sorted(
    [f for f in os.listdir(BACKUP_DIR) if f.startswith('supplypulse_') and f.endswith('.db')],
    reverse=True
)
for old in all_backups[48:]:
    os.remove(os.path.join(BACKUP_DIR, old))

print(f'[OK] Backup saved: {dest}')
