import logging

import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit


log = logging.getLogger(__name__)


class BankofenglandPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IFacets)

    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic', 'bankofengland')

    def dataset_facets(self, facets_dict, package_type):
        facets_dict['market_value_by'] = plugins.toolkit._('Market Value By')
        return facets_dict

    def group_facets(self, facets_dict, group_type, package_type):
        return facets_dict

    def organization_facets(self, facets_dict, organization_type, package_type):
        return facets_dict
