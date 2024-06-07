import os
import csv

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from recipes.models import Ingredient


User = get_user_model()

DATA_ROOT = os.path.join(settings.BASE_DIR, 'data')


FILE_MODEL_TABLE_FIELDS = [
    ('ingredients.csv',
     Ingredient,
     False,
     ['name', 'measurement_unit']),
]


def populate_model(reader, model, fields):
    items = []
    for row in reader:
        items.append(model(**dict(zip(fields, row))))
    model.objects.bulk_create(items)


def populate_table(reader, table, fields):
    con = sqlite3.connect('db.sqlite3')
    cur = con.cursor()
    values = ', '.join(['?' for i in range(len(fields))])
    fields = ', '.join(fields)
    cur.executemany(
        f'INSERT INTO {table}({fields}) VALUES({values});',
        [row for row in reader]
    )
    con.commit()
    con.close()


class Command(BaseCommand):
    help = 'Имортировать CSV-файлы из папки ./data/ в базу данных.'

    def handle(self, *args, **options):
        for file, name, is_table, fields in FILE_MODEL_TABLE_FIELDS:
            path = os.path.join(DATA_ROOT, options['filename']).format(file)
            reader = csv.reader(open(path, 'r', encoding='utf-8'))
            next(reader)
            if is_table:
                populate_table(reader, name, fields)
            else:
                populate_model(reader, name, fields)
