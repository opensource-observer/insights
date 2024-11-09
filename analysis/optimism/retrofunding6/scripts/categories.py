import json


CATEGORY_MAPPINGS = {
    'ETHEREUM_CORE_CONTRIBUTIONS': 'Ethereum Core Contributions',
    'OP_STACK_TOOLING': 'OP Stack Tooling',
    'OP_STACK_RESEARCH_AND_DEVELOPMENT': 'OP Stack R&D'
}

def set_categories(categories_path):
    project_categories = json.load(open(categories_path))
    for old_cat,new_cat in CATEGORY_MAPPINGS.items():
        project_categories[new_cat] = project_categories.pop(old_cat)
    return project_categories
