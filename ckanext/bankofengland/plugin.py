import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit

from ckanext.bankofengland import actions

class BankofenglandPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IConfigurable)
    plugins.implements(plugins.IActions)

    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic', 'bankofengland')

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
    
    #IActions
    def get_actions(self):
        return {
            'create_view': actions.create_view
        }

