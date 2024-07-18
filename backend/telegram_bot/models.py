from django.db import models


class UserProfile(models.Model):
    first_name = models.CharField(
        max_length=100,
        verbose_name="Имя"
        )
    last_name = models.CharField(
        max_length=100,
        verbose_name="Фамилия"
        )
    bdate = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="Дата рождения"
        )
    profile_url = models.URLField(
        blank=True,
        null=True,
        verbose_name="Ссылка на профиль"
        )
    education = models.JSONField(
        blank=True,
        null=True,
        verbose_name="Высшее учебное заведение"
        )
    schools = models.JSONField(
        blank=True,
        null=True,
        verbose_name="Школа"
        )
    military = models.JSONField(
        blank=True,
        null=True,
        verbose_name="Военская часть"
        )
    career = models.JSONField(
        blank=True,
        null=True,
        verbose_name="Место работы")
    city = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Город")
    country = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Страна")
    hometown = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Название родного города")
    university_country = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Название города в котором окончен университет"
        )
    university = models.CharField(max_length=100, blank=True, null=True)
    university_year = models.CharField(max_length=100, blank=True, null=True)
    university_faculty = models.CharField(
        max_length=100, blank=True, null=True)
    university_chair = models.CharField(max_length=100, blank=True, null=True)
    sex = models.IntegerField(blank=True, null=True)
    status = models.CharField(max_length=100, blank=True, null=True)
    age_from = models.IntegerField(blank=True, null=True)
    age_to = models.IntegerField(blank=True, null=True)
    birth_day = models.IntegerField(blank=True, null=True)
    birth_month = models.IntegerField(blank=True, null=True)
    birth_year = models.IntegerField(blank=True, null=True)
    online = models.IntegerField(blank=True, null=True)
    has_photo = models.IntegerField(blank=True, null=True)
    school_country = models.CharField(max_length=100, blank=True, null=True)
    school_city = models.CharField(max_length=100, blank=True, null=True)
    school_class = models.IntegerField(blank=True, null=True)
    school = models.CharField(max_length=100, blank=True, null=True)
    school_year = models.IntegerField(blank=True, null=True)
    religion = models.CharField(max_length=100, blank=True, null=True)
    interests = models.CharField(max_length=255, blank=True, null=True)
    company = models.CharField(max_length=100, blank=True, null=True)
    position = models.CharField(max_length=100, blank=True, null=True)
    group_id = models.IntegerField(blank=True, null=True)
    from_list = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"
