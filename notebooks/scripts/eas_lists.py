import json
import pandas as pd


class OsoData:

    SLUG_KEY = 'Slug: Primary'
    ID_KEY = 'Project ID'
    LINK_KEY = 'Link'
    IGNORES = ['op']

    def __init__(self, data_path):
        self.data_path = data_path
        self.df = self.load_data()

    def load_data(self):
        with open(self.data_path) as j:
            app_data = json.load(j)

        oss_apps = [p for p in app_data if p[self.SLUG_KEY] and p[self.SLUG_KEY] not in self.IGNORES]
        df = pd.DataFrame(oss_apps)
        df.drop_duplicates(subset=[self.LINK_KEY], keep='last', inplace=True)
        print(f"Loaded {len(df)} OSS projects from {self.data_path}.")
        return df

    def get_project_slugs(self):
        slugs = self.df[self.SLUG_KEY].unique()
        print(f"Identified {len(slugs)} unique slugs.")
        return slugs
    
    def map_slugs_to_ids(self):
        return self.df.set_index(self.SLUG_KEY)[self.ID_KEY].to_dict()

    def check_duplicate_slugs(self):
        to_review = self.df[self.SLUG_KEY].value_counts()
        to_review = to_review[to_review > 1]
        dff = (
            self.df[self.df[self.SLUG_KEY].isin(to_review.index)]
            .sort_values(by=self.SLUG_KEY)
            [[self.ID_KEY, 'Project Name', self.SLUG_KEY, 'Payout Address']]
        )
        return dff


def listify(lst, amount):
    total = sum(lst.values())
    factor = amount / total
    new_list = {k:round(v*factor,2) for k,v in lst.items() if v>0}
    new_list = dict(sorted(new_list.items(), key = lambda x: x[1], reverse=True))
    return new_list


# https://optimism.easscan.org/schema/view/0x3e3e2172aebb902cf7aa6e1820809c5b469af139e7a4265442b1c22b97c6b2a5
def create_eas_json(allocation_dict, list_name, list_link, list_descr, list_categories):
    return {
        'listDescription': list_name,
        'impactEvaluationLink': list_link,
        'impactEvaluationDescription': list_descr,
        'impactCategory': list_categories,
        'listContent': [
            {'RPGF3_Application_UID': k, 'OPAmount': v} for k,v in allocation_dict.items()
        ]
    }


def print_project_list_by_tag(data_path):

    oso = OsoData(data_path)
    tags = set([y for x in oso.df['Tags'] for y in x])
    for tag in tags:
        print(tag)
        for _,row in oso.df.sort_values(by='Slug: Primary').iterrows():
            if tag in row['Tags']:
                print("-",row['Slug: Primary'])