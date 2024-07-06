from django.db import models
import json
from openpyxl import Workbook

class Link(models.Model):
    name = models.CharField(
        max_length=250,
        mull=True,
        verbose_name='Название группы или имя аккаунта'
    )
    link = models.CharField(
        max_length=1000,
        null=True,
        verbose_name='Ссылка на пользователя'
    )

    def __str__(self) -> str:
        return self.name


class Document(models.Model):
    name = models.CharField(
        max_length=250,
        null=True
    )
    file = models.FileField(
        upload_to="uploads/",
        verbose_name="Файл с ссылками"
    )

    def __str__(self):
        return self.name

    def save_links(self, format_type):
        if format_type == 'json':
            self.save_links_to_json()
        elif format_type == 'excel':
            self.save_links_to_excel()
        else:
            raise ValueError("Unsupported format type")

    def save_links_to_json(self):
        links = list(Link.objects.values('name', 'link'))
        file_path = self.file.path
        with open(file_path, 'w') as f:
            json.dump(links, f)

    def save_links_to_excel(self):
        links = Link.objects.all()
        file_path = self.file.path
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = 'Список ссылок'

        sheet.append(['Название группы или имя аккаунта',
                     'Ссылка на пользователя'])
        for link in links:
            sheet.append([link.name, link.link])

        workbook.save(file_path)
