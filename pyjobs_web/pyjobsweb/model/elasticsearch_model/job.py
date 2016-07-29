# -*- coding: utf-8 -*-
import elasticsearch_dsl as es
from datetime import datetime
from babel.dates import format_date, format_timedelta

from pyjobs_crawlers.tools import condition_tags
from pyjobsweb.model.data import Tag2


class Tag(es.InnerObjectWrapper):
    def __init__(self, mapping, **kwargs):
        super(Tag, self).__init__(mapping, **kwargs)


class Job(es.DocType):
    class Meta:
        index = 'jobs'
        doc_type = 'job-offer'

    french_elision = es.token_filter(
        'french_elision',
        type='elision',
        articles_case=True,
        articles=[
            'l', 'm', 't', 'qu', 'n', 's',
            'j', 'd', 'c', 'jusqu', 'quoiqu',
            'lorsqu', 'puisqu'
        ]
    )

    french_stopwords = es.token_filter('french_stopwords',
                                       type='stop', stopwords='_french_')

    # Do not include this filter if keywords is empty
    french_keywords = es.token_filter('french_keywords',
                                      type='keyword_maker', keywords=[])

    french_stemmer = es.token_filter('french_stemmer',
                                     type='stemmer', language='light_french')

    french_analyzer = es.analyzer(
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

    french_description_analyzer = es.analyzer(
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

    id = es.Integer()

    url = es.String(index='no')
    source = es.String(index='not_analyzed')

    title = es.String(analyzer=french_analyzer)
    description = es.String(analyzer=french_description_analyzer)
    company = es.String(index='analyzed')
    company_url = es.String(index='no')

    address = es.String(index='no')
    is_valid_address = es.Boolean()

    tags = es.Nested(doc_class=Tag,
                     properties=dict(tag=es.String(index='not_analyzed'),
                                     weight=es.Integer()))

    publication_datetime = es.Date()
    publication_datetime_is_fake = es.Boolean()

    crawl_datetime = es.Date()

    is_valid_geolocation = es.Boolean()
    geolocation = es.GeoPoint()

    def __init__(self, meta=None, **kwargs):
        super(Job, self).__init__(meta, **kwargs)

    @property
    def published(self):
        return format_date(self.publication_datetime, locale='FR_fr')

    @property
    def published_in_days(self):
        delta = datetime.now() - self.publication_datetime  # TODO: bugfix
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
                    tag = Tag2(tag['tag'],
                               tag['weight'], Tag2.get_css(tag['tag']))
                    tags.append(tag)
        return tags
