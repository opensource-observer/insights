import json
import pandas as pd


OVERRIDE_MAPPINGS = {
    "bootnodedev": "0x7c96c745536a31712abeccc61dca77089e8eb9ab59876e5d40986700c834aca2",
    "filosofiacodigo": "0x74c9135b2ca59c277d93942e535f02777d2779f1fee5b88c9ff76ff20cdcd8b8",
    "gitcoin": "0x95bba9455fa1028d59c069660656b3fe0b46d7b2e1883b091c5b04b810bc7525", # Gitcoin and Passport
    "itu-blockchain": "0x956b110e3b9aa11c53bbf41b97d34fadb4d516faede3304fa2807db3fd6d7407", # OPClave & ITU
    "lxdao-official": "0x7d3cb52c6e006ca04df32b6bef1982962c0669a7b9d826114cf9f40c0ce9be97", # Various
    "metagov": "0x335ee234463e3a9bf9ea3325fd6942f30877714716b159ca7843f9b4d9ff4285", # MetaGov and DAOstar
    "playmint": "0x33135d1d7ea18427c5096af97f5d5bcac392b8bbe871a9a0a9dd62ce651212df", # Client Side Proofs and Downstream
    "polynomial-protocol": "0x90ef634fad04d6ac2882db44d4a84f31c7f0621f3abd00efb067416e4ff1641c", # Optimitic Indexer & Polynomial Bytes
    "rainbow": "0x723da383185924834ea462c791d4e21dac5dedc94ba164bd37adc571ba5008ed", # Rainbow Kit and Rainbow Me
    "reth-paradigmxyz": "0x62aa2cbedbc3772d3110b0927f0eea6313a71c9b3d7980ee631ca9aa2e9db3c6", # OP Reth
    "synapse": "0x224aae62a450603d6358ab1d699a3daeef169761279597712b08b8dc4d25b198", # Synapse Labs and Synapse DAO
    "ultrasoundmoney": "0xd06423aa05a359735b911e9988486822acb3c3f62e3397ed35d6430240454b0f", # Ultra Sound Money and Relay
    "vyperlang": "0x1b205ded96fa08412a2c8b7100de978779b13fd81fd8a85aaf71f7994065c690", # Vyper, Venom & Fang, Titanoboa
    "waffle-truefieng": "0xf162490ee7fc0844a9f2033eb1107cf910df56889ce42a28ea4bf049ae75bf63" # Waffle and Vaults.fyi
}


class OsoData:

    SLUG_KEY = 'Slug: Primary'
    ID_KEY = 'Project ID'
    LINK_KEY = 'Link'
    IGNORES = ['op']

    def __init__(self, data_path):
        self.data_path = data_path
        self.df = self.load_data()

    def load_data(self, override_mappings=True):
        with open(self.data_path) as j:
            app_data = json.load(j)

        oss_apps = [p for p in app_data if p[self.SLUG_KEY] and p[self.SLUG_KEY] not in self.IGNORES]
        df = pd.DataFrame(oss_apps)
        df.drop_duplicates(subset=[self.LINK_KEY], keep='last', inplace=True)
        if override_mappings:
            for slug,project_id in OVERRIDE_MAPPINGS.items():
                df = df[~((df[self.SLUG_KEY] == slug) & (df[self.ID_KEY] != project_id))]
    
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
