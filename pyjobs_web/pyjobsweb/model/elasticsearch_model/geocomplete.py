# -*- coding: utf-8 -*-
import elasticsearch_dsl as es


class Geocomplete(es.DocType):
    class Meta:
        index = 'geocomplete'
        doc_type = 'geoloc-entry'

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

    geocompletion_ngram_filter = es.token_filter(
        'geocompletion_ngram',
        type='edgeNGram',
        min_gram=1,
        max_gram=50,
        side='front'
    )

    geocompletion_index_analyzer = es.analyzer(
        'geocompletion_index_analyzer',
        type='custom',
        tokenizer='standard',
        filter=[
            'lowercase',
            'asciifolding',
            'word_delimiter',
            french_elision,
            geocompletion_ngram_filter
        ]
    )

    geocompletion_search_analyzer = es.analyzer(
        'geocompletion_search_analyzer',
        type='custom',
        tokenizer='standard',
        filter=[
            'lowercase',
            'asciifolding'
        ]
    )

    name = es.String(
        index='analyzed',
        analyzer=geocompletion_index_analyzer,
        search_analyzer=geocompletion_search_analyzer,
        fields=dict(raw=es.String(index='not_analyzed'))
    )

    complement = es.String(index='not_analyzed')

    postal_code_ngram_filter = es.token_filter(
        'postal_code_ngram',
        type='edgeNGram',
        min_gram=1,
        max_gram=5,
        side='front'
    )

    postal_code_index_analyzer = es.analyzer(
        'postal_code_index_analyzer',
        type='custom',
        tokenizer='standard',
        filter=[
            postal_code_ngram_filter
        ]
    )

    postal_code_search_analyzer = es.analyzer(
        'postal_code_search_analyzer',
        type='custom',
        tokenizer='standard'
    )

    postal_code = es.String(
        index='analyzed',
        analyzer=postal_code_index_analyzer,
        search_analyzer=postal_code_search_analyzer
    )

    geolocation = es.GeoPoint()

    weight = es.Float()

    def __init__(self, meta=None, **kwargs):
        super(Geocomplete, self).__init__(meta, **kwargs)

    @property
    def index(self):
        return self._doc_type.index

    @property
    def doc_type(self):
        return self._doc_type.name
