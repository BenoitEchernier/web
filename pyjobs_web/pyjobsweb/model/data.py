# -*- coding: utf-8 -*-
import elasticsearch_dsl
import elasticsearch_dsl.serializer
import sqlalchemy
from pyjobs_crawlers.tools import get_sources, condition_tags

from pyjobsweb.model import DeclarativeBase
from datetime import datetime
from babel.dates import format_date, format_timedelta


class Status(object):
    INITIAL_CRAWL_OK = 'initial-crawl-ok'
    PUBLISHED = 'published'


class Source(object):
    AFPY_JOBS = 'afpy-jobs'
    REMIXJOBS_PYTHON = 'remixjobs-python'


SOURCES = get_sources()


class Tag2(object):
    def __init__(self, tag, weight=1, css=''):
        self.tag = tag
        self.weight = weight
        self.css = css

    @classmethod
    def get_css(cls, tagname):
        css = {
            u'cdd': 'job-cdd',
            u'cdi': 'job-cdi',
            u'freelance': 'job-freelance',
            u'stage': 'job-stage',
            u'télétravail': 'job-remote',
            u'télé-travail': 'job-remote',
        }
        return css[tagname]


class Tags(elasticsearch_dsl.InnerObjectWrapper):
    pass


class Tag(elasticsearch_dsl.InnerObjectWrapper):
    pass


class JobOfferElasticsearch(elasticsearch_dsl.DocType):
    class Meta:
        index = 'jobs'
        doc_type = 'job-offer'

    french_elision = elasticsearch_dsl.token_filter(
            'french_elision',
            type='elision',
            articles_case=True,
            articles=[
                'l', 'm', 't', 'qu', 'n', 's',
                'j', 'd', 'c', 'jusqu', 'quoiqu',
                'lorsqu', 'puisqu'
            ]
    )
    french_stopwords = elasticsearch_dsl.token_filter(
            'french_stopwords', type='stop', stopwords='_french_'
    )
    # Do not include this filter if keywords is empty
    french_keywords = elasticsearch_dsl.token_filter(
            'french_keywords', type='keyword_maker', keywords=[]
    )
    french_stemmer = elasticsearch_dsl.token_filter(
            'french_stemmer', type='stemmer', language='light_french'
    )

    french_analyzer = elasticsearch_dsl.analyzer(
            'french_analyzer',
            tokenizer='standard',
            filter=[
                'lowercase',
                french_elision,
                french_stopwords,
                # french_keywords,
                french_stemmer
            ]
    )
    french_description_analyzer = elasticsearch_dsl.analyzer(
            'french_description_analyzer',
            tokenizer='standard',
            filter=[
                'lowercase',
                french_elision,
                french_stopwords,
                # french_keywords,
                french_stemmer
            ],
            char_filter=['html_strip']
    )

    id = elasticsearch_dsl.Integer()

    url = elasticsearch_dsl.String(
            index='not_analyzed'
    )

    source = elasticsearch_dsl.String(
            index='not_analyzed'
    )

    title = elasticsearch_dsl.String(
            analyzer=french_analyzer
    )

    description = elasticsearch_dsl.String(
            analyzer=french_description_analyzer
    )

    company = elasticsearch_dsl.String(
            index='not_analyzed'
    )

    company_url = elasticsearch_dsl.String(
            index='not_analyzed'
    )

    address = elasticsearch_dsl.String(
            index='not_analyzed'
    )

    tags = elasticsearch_dsl.Nested(
            doc_class=Tag,
            properties={
                'tag': elasticsearch_dsl.String(
                        index='not_analyzed'
                ),
                'weight': elasticsearch_dsl.Integer()
            }
    )

    publication_datetime = elasticsearch_dsl.Date()
    publication_datetime_is_fake = elasticsearch_dsl.Boolean()
    crawl_datetime = elasticsearch_dsl.Date()
    geolocation_error = elasticsearch_dsl.Boolean()
    geolocation = elasticsearch_dsl.GeoPoint()

    @property
    def published(self):
        return format_date(self.publication_datetime, locale='FR_fr')

    @property
    def published_in_days(self):
        delta = datetime.now() - self.publication_datetime
        return format_timedelta(delta, granularity='day', locale='en_US')

    @property
    def alltags(self):
        tags = []
        if self.tags:
            for tag in self.tags:
                if tag['tag'] not in condition_tags:
                    tags.append(Tag2(tag['tag'], tag['weight']))
        return tags

    @property
    def condition_tags(self):
        tags = []
        if self.tags:
            for tag in self.tags:
                if tag['tag'] in condition_tags:
                    tag = Tag2(tag['tag'], tag['weight'], Tag2.get_css(tag['tag']))
                    tags.append(tag)
        return tags


class JobOfferSQLAlchemy(DeclarativeBase):

    __tablename__ = 'jobs'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)

    url = sqlalchemy.Column(sqlalchemy.String(1024))
    source = sqlalchemy.Column(sqlalchemy.String(64))

    title = sqlalchemy.Column(
        sqlalchemy.String(1024), nullable=False, default=''
    )
    description = sqlalchemy.Column(
        sqlalchemy.Text(), nullable=False, default=''
    )
    company = sqlalchemy.Column(
        sqlalchemy.String(1024), nullable=False, default=''
    )
    company_url = sqlalchemy.Column(
        sqlalchemy.String(1024), nullable=True, default=''
    )

    address = sqlalchemy.Column(
        sqlalchemy.String(2048), nullable=False, default=''
    )
    tags = sqlalchemy.Column(
        sqlalchemy.Text(), nullable=False, default=''
    )  # JSON

    publication_datetime = sqlalchemy.Column(sqlalchemy.DateTime)
    publication_datetime_is_fake = sqlalchemy.Column(sqlalchemy.Boolean)

    crawl_datetime = sqlalchemy.Column(sqlalchemy.DateTime)

    already_in_elasticsearch = sqlalchemy.Column(
        sqlalchemy.Boolean, default=False
    )

    def __init__(self):
        pass

    def __repr__(self):
        return "<Job: id='%d'>" % self.id

    @property
    def published(self):
        return format_date(self.publication_datetime, locale='FR_fr')

    @property
    def published_in_days(self):
        delta = datetime.now() - self.publication_datetime
        return format_timedelta(delta, granularity='day', locale='en_US')

    @property
    def alltags(self):
        import json
        tags = []
        if self.tags:
            for tag in json.loads(self.tags):
                if tag['tag'] not in condition_tags:
                    tags.append(Tag2(tag['tag'], tag['weight']))
        return tags

    @property
    def condition_tags(self):
        import json
        tags = []
        if self.tags:
            for tag in json.loads(self.tags):
                if tag['tag'] in condition_tags:
                    tag = Tag2(tag['tag'], tag['weight'], Tag2.get_css(tag['tag']))
                    tags.append(tag)
        return tags

    def to_elasticsearch_job_offer(self):
        deserialize = elasticsearch_dsl.serializer.serializer.loads
        job_tags = deserialize(self.tags)
        tags = []

        for tag in job_tags:
            tags.append(tag)

        return JobOfferElasticsearch(
            id=self.id,
            url=self.url,
            source=self.source,
            title=self.title,
            description=self.description,
            company=self.company,
            company_url=self.company_url,
            address=self.address,
            tags=tags,
            publication_datetime=self.publication_datetime,
            publication_datetime_is_fake=self.publication_datetime_is_fake,
            crawl_datetime=self.publication_datetime
        )
