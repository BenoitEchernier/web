# -*- coding: utf-8 -*-
from tg.decorators import expose, redirect

from pyjobsweb.lib.base import BaseController


class AddCompanyController(BaseController):
    @expose('pyjobsweb.templates.companies.new')
    def index(self):
        raise NotImplementedError('TODO')

    @expose()
    def submit(self):
        raise NotImplementedError('TODO')


class SearchCompanyController(BaseController):
    @expose('pyjobsweb.templates.companies.search')
    def index(self):
        raise NotImplementedError('TODO')

    @expose()
    def submit(self):
        raise NotImplementedError('TODO')


class CompanyController(BaseController):
    new = AddCompanyController()
    search = SearchCompanyController()

    @expose()
    def index(self):
        redirect('/company/list')

    @expose('pyjobsweb.templates.companies.list')
    def list(self):
        raise NotImplementedError('TODO')

    @expose('pyjobsweb.templates.companies.details')
    def details(self, company_id, *args, **kwargs):
        raise NotImplementedError('TODO')

