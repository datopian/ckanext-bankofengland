import logging

import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit

from ckanext.bankofengland import actions, validators

log = logging.getLogger(__name__)


class BankofenglandPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IFacets)
    plugins.implements(plugins.IConfigurable)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IValidators)

    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic', 'bankofengland')

    def dataset_facets(self, facets_dict, package_type):
        facets_dict['market_value_by'] = plugins.toolkit._('Market Value By')
        facets_dict['granularity'] = plugins.toolkit._('Granularity')
        return facets_dict

    def group_facets(self, facets_dict, group_type, package_type):
        facets_dict['market_value_by'] = plugins.toolkit._('Market Value By')
        facets_dict['granularity'] = plugins.toolkit._('Granularity')
        return facets_dict

    def organization_facets(self, facets_dict, organization_type, package_type):
        facets_dict['market_value_by'] = plugins.toolkit._('Market Value By')
        facets_dict['granularity'] = plugins.toolkit._('Granularity')
        return facets_dict

    # IConfigurable

    def configure(self, config):
        # Certain config options must exists for the plugin to work. Raise an
        # exception if they're missing.
        missing_config = "{0} is not configured. Please amend your .ini file."
        config_options = (
            'ckanext.bankofengland.hasura_url',
            'ckanext.bankofengland.hasura_admin_key',
            'ckanext.bankofengland.hasura_db',
        )
        for option in config_options:
            if not config.get(option, None):
                raise RuntimeError(missing_config.format(option))

    def get_validators(self):
        return {
            "tag_length_validator": validators.tag_length_validator,
            "tag_name_validator": validators.tag_name_validator
        }

    #IActions
    def get_actions(self):
        return {
            'create_view': actions.create_view,
            'package_create': actions.package_create,
            'package_update': actions.package_update
        }
