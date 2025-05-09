from config import DB_URL
from database.db_interfaces.campaigns import CampaignsDBInterface


'''Модуль чтобы избавиться от цикличных импортов'''
db = CampaignsDBInterface(db_url=DB_URL)