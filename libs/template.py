"""
    template.py     A few simple tools to make templating messages
                    in this app a bit less terrible. 
"""

def load_template(template_name, template_config):
    """
    Loads a given template, and performs text subsitutios based
    on the provided configuration. 

    Requires that the subsitutions are already expressed in the 
    /template/file.json file.
    """

    with open(f'templates/{template_name}.json', 'r', encoding="utf-8") as file_data:

        file_content = file_data.read()

        # Look through the subsitution config and make changes
        for k, v in template_config.items():

            file_content = file_content.replace(k, v, 1)

        return file_content
