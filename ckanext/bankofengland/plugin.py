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
        facets_dict['metrics'] = plugins.toolkit._('Metrics')
        facets_dict['eba_dim_bas_base'] = plugins.toolkit._('eba_dim:BAS (Base)')
        facets_dict['eba_dim_tri_type_of_risk'] = plugins.toolkit._('eba_dim:TRI (Type of risk)')
        facets_dict['eba_dim_cud_currency_of_denomination_of_the_reported_position'] = plugins.toolkit._('boe_dim:CUD (Currency of denomination of the reported position )')
        facets_dict['eba_dim_mcy_main_category'] = plugins.toolkit._('eba_dim:MCY (Main category)')
        facets_dict['eba_dim_mcb_instrument'] = plugins.toolkit._('eba_dim:MCB (Instrument)')
        facets_dict['boe_dim_counterparty_sector_of_reporter'] = plugins.toolkit._('boe_dim:Counterparty sector of reporter')
        facets_dict['eba_dim_cps_counterparty_sector'] = plugins.toolkit._('eba_dim:CPS (Counterparty sector)')
        facets_dict['eba_dim_rcp_residence_of_counterparty'] = plugins.toolkit._('eba_dim:RCP (Residence of counterparty)')
        return facets_dict

    def group_facets(self, facets_dict, group_type, package_type):
        facets_dict['market_value_by'] = plugins.toolkit._('Market Value By')
        facets_dict['granularity'] = plugins.toolkit._('Granularity')
        facets_dict['metrics'] = plugins.toolkit._('Metrics')
        facets_dict['eba_dim_bas_base'] = plugins.toolkit._('eba_dim:BAS (Base)')
        facets_dict['eba_dim_tri_type_of_risk'] = plugins.toolkit._('eba_dim:TRI (Type of risk)')
        facets_dict['eba_dim_cud_currency_of_denomination_of_the_reported_position'] = plugins.toolkit._('boe_dim:CUD (Currency of denomination of the reported position )')
        facets_dict['eba_dim_mcy_main_category'] = plugins.toolkit._('eba_dim:MCY (Main category)')
        facets_dict['eba_dim_mcb_instrument'] = plugins.toolkit._('eba_dim:MCB (Instrument)')
        facets_dict['boe_dim_counterparty_sector_of_reporter'] = plugins.toolkit._('boe_dim:Counterparty sector of reporter')
        facets_dict['eba_dim_cps_counterparty_sector'] = plugins.toolkit._('eba_dim:CPS (Counterparty sector)')
        facets_dict['eba_dim_rcp_residence_of_counterparty'] = plugins.toolkit._('eba_dim:RCP (Residence of counterparty)')
        return facets_dict

    def organization_facets(self, facets_dict, organization_type, package_type):
        facets_dict['market_value_by'] = plugins.toolkit._('Market Value By')
        facets_dict['granularity'] = plugins.toolkit._('Granularity')
        facets_dict['metrics'] = plugins.toolkit._('Metrics')
        facets_dict['eba_dim_bas_base'] = plugins.toolkit._('eba_dim:BAS (Base)')
        facets_dict['eba_dim_tri_type_of_risk'] = plugins.toolkit._('eba_dim:TRI (Type of risk)')
        facets_dict['eba_dim_cud_currency_of_denomination_of_the_reported_position'] = plugins.toolkit._('boe_dim:CUD (Currency of denomination of the reported position )')
        facets_dict['eba_dim_mcy_main_category'] = plugins.toolkit._('eba_dim:MCY (Main category)')
        facets_dict['eba_dim_mcb_instrument'] = plugins.toolkit._('eba_dim:MCB (Instrument)')
        facets_dict['boe_dim_counterparty_sector_of_reporter'] = plugins.toolkit._('boe_dim:Counterparty sector of reporter')
        facets_dict['eba_dim_cps_counterparty_sector'] = plugins.toolkit._('eba_dim:CPS (Counterparty sector)')
        facets_dict['eba_dim_rcp_residence_of_counterparty'] = plugins.toolkit._('eba_dim:RCP (Residence of counterparty)')
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
            'get_history': actions.get_history,
            'package_create': actions.package_create,
            'package_update': actions.package_update,
            'search_package_list': actions.search_package_list
        }

